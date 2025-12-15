"""Canon Ivy 2 printer implementation."""

import queue
import time
from typing import Any, Dict, Optional

from loguru import logger

from ..base import Printer
from ...models import PrinterStatus, PrinterInfo, PrinterCapabilities
from ...bluetooth import get_transport, BluetoothTransport
from ...utils import ThreadedClient
from ...exceptions import (
    ConnectionError,
    PrintError,
    ProtocolError,
    LowBatteryError,
    CoverOpenError,
    NoPaperError,
    TimeoutError,
)

from .protocol import (
    parse_message,
    StartSessionTask,
    GetStatusTask,
    GetSettingTask,
    SetSettingTask,
    GetPrintReadyTask,
    RebootTask,
    BaseTask,
)
from .image import prepare_image


# Constants
PRINT_BATTERY_MIN = 30
PRINT_DATA_CHUNK = 990


class CanonIvy2Printer(Printer):
    """Canon Ivy 2 Mini Photo Printer.

    A compact Zink-based photo printer that connects via Bluetooth RFCOMM.

    Example:
        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF")
        printer.connect()

        status = printer.get_status()
        if status.is_ready:
            printer.print("photo.jpg")

        printer.disconnect()
    """

    # Class-level printer info (for registry)
    _info = PrinterInfo(
        name="Canon Ivy 2",
        model="canon_ivy2",
        print_width=640,
        print_height=1616,
        supported_formats=["JPEG", "PNG", "BMP", "GIF"],
    )

    _capabilities = PrinterCapabilities(
        can_get_status=True,
        can_get_battery=True,
        can_configure_settings=True,
        can_reboot=True,
        supports_multiple_copies=False,
        min_battery_for_print=PRINT_BATTERY_MIN,
    )

    def __init__(
        self,
        address: str,
        port: int = 1,
        transport: Optional[str] = None,
    ):
        """Initialize Canon Ivy 2 printer.

        Args:
            address: Bluetooth MAC address.
            port: RFCOMM channel (default 1).
            transport: Transport type ("native", "pybluez") or None for auto.
        """
        self._address = address
        self._port = port
        self._transport_type = transport
        self._client: Optional[ThreadedClient] = None
        self._firmware_version: Optional[str] = None

    @property
    def capabilities(self) -> PrinterCapabilities:
        return self._capabilities

    @property
    def info(self) -> PrinterInfo:
        info = PrinterInfo(
            name=self._info.name,
            model=self._info.model,
            print_width=self._info.print_width,
            print_height=self._info.print_height,
            supported_formats=self._info.supported_formats,
            firmware_version=self._firmware_version,
        )
        return info

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.alive.is_set()

    def connect(self) -> None:
        """Connect to the printer and initialize session."""
        if self.is_connected:
            return

        transport = get_transport(self._transport_type)
        self._client = ThreadedClient(
            transport,
            receive_size=4096,
            auto_disconnect_timeout=30,
        )
        self._client.connect(self._address, self._port)

        # Initialize session
        battery_level, mtu = self._perform_task(StartSessionTask())
        logger.debug(f"Connected to Canon Ivy 2; Battery: {battery_level}%; MTU: {mtu}")

    def disconnect(self) -> None:
        """Disconnect from the printer."""
        if self._client is not None:
            self._client.disconnect()
            self._client = None

    def print(
        self,
        image_path: str,
        auto_crop: bool = True,
        quality: int = 100,
        transfer_timeout: int = 60,
        **options,
    ) -> None:
        """Print an image.

        Args:
            image_path: Path to image file.
            auto_crop: If True, crop to fill. If False, fit with letterboxing.
            quality: JPEG quality (1-100).
            transfer_timeout: Seconds to wait for transfer completion.
            **options: Additional options (ignored).

        Raises:
            PrintError: If print fails.
            LowBatteryError: If battery too low.
            CoverOpenError: If cover is open.
            NoPaperError: If no paper.
        """
        # Prepare image data
        image_data = prepare_image(image_path, auto_crop=auto_crop, quality=quality)
        image_length = len(image_data)

        # Check printer is ready
        self._check_print_worthiness()

        # Get settings (required by protocol)
        self.get_settings()

        # Prepare printer for image transfer
        self._perform_task(GetPrintReadyTask(image_length))

        # Send image data in chunks
        start_index = 0
        while start_index < image_length:
            end_index = min(start_index + PRINT_DATA_CHUNK, image_length)
            chunk = image_data[start_index:end_index]
            self._client.outbound_q.put(chunk)
            start_index = end_index

        logger.debug("Image data queued, waiting for transfer...")

        # Wait for transfer completion
        self._receive_message(transfer_timeout)
        logger.debug("Transfer complete! Printing should begin shortly.")

    def get_status(self) -> PrinterStatus:
        """Get current printer status."""
        error_code, battery, usb, cover_open, no_paper, wrong_sheet = self._perform_task(
            GetStatusTask()
        )

        # Determine error message
        error = None
        if cover_open:
            error = "Cover is open"
        elif no_paper:
            error = "No paper"
        elif wrong_sheet:
            error = "Wrong smart sheet"
        elif error_code != 0:
            error = f"Error code: {error_code}"

        is_ready = error is None and battery >= PRINT_BATTERY_MIN

        return PrinterStatus(
            battery_level=battery,
            is_ready=is_ready,
            error=error,
            is_cover_open=cover_open,
        )

    def get_settings(self) -> Dict[str, Any]:
        """Get printer settings."""
        auto_off, firmware, tmd, photos, color = self._perform_task(GetSettingTask())

        self._firmware_version = firmware

        return {
            "auto_power_off": auto_off,
            "firmware_version": firmware,
            "tmd_version": tmd,
            "photos_printed": photos,
            "color_id": color,
        }

    def set_setting(self, key: str, value: Any) -> None:
        """Set a printer setting.

        Args:
            key: Setting name. Currently only "auto_power_off" is supported.
            value: Setting value. For auto_power_off: 3, 5, or 10 (minutes).

        Raises:
            ValueError: If setting name or value is invalid.
        """
        if key == "auto_power_off":
            if value not in (3, 5, 10):
                raise ValueError("auto_power_off must be 3, 5, or 10")
            self._perform_task(SetSettingTask(value))
        else:
            raise ValueError(f"Unknown setting: {key}")

    def reboot(self) -> None:
        """Reboot the printer."""
        self._perform_task(RebootTask())

    def _check_print_worthiness(self) -> None:
        """Check if printer is ready to print, raise appropriate error if not."""
        status = self.get_status()

        if status.is_cover_open:
            raise CoverOpenError()

        if status.error == "No paper":
            raise NoPaperError()

        if status.error == "Wrong smart sheet":
            raise PrintError("Wrong smart sheet inserted", device_error="wrong_smart_sheet")

        if status.battery_level < PRINT_BATTERY_MIN:
            raise LowBatteryError(
                f"Battery at {status.battery_level}%, need {PRINT_BATTERY_MIN}%",
                level=status.battery_level,
            )

        if status.error:
            raise PrintError(status.error)

    def _perform_task(self, task: BaseTask):
        """Execute a protocol task and return the result."""
        self._send_message(task.get_message())
        response = self._receive_message()

        if response.ack != task.ack:
            raise ProtocolError(
                f"Unexpected ACK: expected {task.ack}, got {response.ack}",
                expected=task.ack,
                got=response.ack,
            )

        return task.process_response(response)

    def _send_message(self, message: bytes) -> None:
        """Send a message via the client queue."""
        if not self.is_connected:
            raise ConnectionError("Not connected")

        self._client.outbound_q.put(message)

    def _receive_message(self, timeout: int = 5):
        """Wait for and parse a response message."""
        start = time.time()

        while time.time() < start + timeout:
            if not self.is_connected:
                raise ConnectionError("Connection lost")

            try:
                data = self._client.inbound_q.get(timeout=0.1)
                response = parse_message(data)

                logger.debug(f"Received: ack={response.ack}, error={response.error}")
                return response

            except queue.Empty:
                continue

        raise TimeoutError(f"No response within {timeout} seconds")
