"""Kodak Step printer implementation."""

import queue
import time
from typing import Any, Dict, Optional, Union

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
    PACKET_SIZE,
    CHUNK_SIZE,
    INTER_CHUNK_DELAY_MS,
    MIN_BATTERY_LEVEL,
    ERR_SUCCESS,
    ERR_NO_PAPER,
    ERR_COVER_OPEN,
    get_error_message,
    parse_response,
    validate_response,
    GetAccessoryInfoTask,
    GetBatteryLevelTask,
    GetPageTypeTask,
    GetPrintCountTask,
    GetAutoPowerOffTask,
    PrintReadyTask,
    BaseTask,
)
from .image import prepare_image


class KodakStepPrinter(Printer):
    """Kodak Step Series Mini Photo Printer.

    Supports Kodak Step, Step Touch, Step Slim, and Snap 2 printers.
    These are compact Zink-based photo printers that connect via Bluetooth SPP.

    Example:
        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF")
        printer.connect()

        status = printer.get_status()
        if status.is_ready:
            printer.print("photo.jpg")

        printer.disconnect()
    """

    # Class-level printer info (for registry)
    _info = PrinterInfo(
        name="Kodak Step",
        model="kodak_step",
        print_width=640,
        print_height=1616,
        supported_formats=["JPEG", "PNG", "BMP", "GIF"],
    )

    _capabilities = PrinterCapabilities(
        can_get_status=True,
        can_get_battery=True,
        can_configure_settings=True,
        can_reboot=False,
        supports_multiple_copies=True,
        min_battery_for_print=MIN_BATTERY_LEVEL,
    )

    def __init__(
        self,
        address: str,
        port: int = 1,
        transport: Optional[Union[str, BluetoothTransport]] = None,
        is_slim: bool = False,
    ):
        """Initialize Kodak Step printer.

        Args:
            address: Bluetooth MAC address.
            port: RFCOMM channel (default 1).
            transport: Transport type ("native", "pybluez"), transport instance,
                or None for auto-detection.
            is_slim: True for Step Slim or Snap 2 devices.
        """
        self._address = address
        self._port = port
        self._is_slim = is_slim
        # Store transport instance or type string
        if isinstance(transport, BluetoothTransport):
            self._transport_instance = transport
            self._transport_type = None
        else:
            self._transport_instance = None
            self._transport_type = transport
        self._client: Optional[ThreadedClient] = None
        self._battery_level: int = 0
        self._is_charging: bool = False

    @property
    def capabilities(self) -> PrinterCapabilities:
        return self._capabilities

    @property
    def info(self) -> PrinterInfo:
        name = "Kodak Step Slim" if self._is_slim else "Kodak Step"
        return PrinterInfo(
            name=name,
            model=self._info.model,
            print_width=self._info.print_width,
            print_height=self._info.print_height,
            supported_formats=self._info.supported_formats,
        )

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.alive.is_set()

    def connect(self) -> None:
        """Connect to the printer and initialize session."""
        if self.is_connected:
            return

        # Use provided transport instance or create one
        if self._transport_instance is not None:
            transport = self._transport_instance
        else:
            transport = get_transport(self._transport_type)

        self._client = ThreadedClient(
            transport,
            receive_size=4096,
            auto_disconnect_timeout=30,
        )
        self._client.connect(self._address, self._port)

        # Initialize session with GET_ACCESSORY_INFO
        battery_level, is_charging = self._perform_task(
            GetAccessoryInfoTask(is_slim=self._is_slim)
        )
        self._battery_level = battery_level
        self._is_charging = is_charging

        logger.debug(f"Connected to Kodak Step; Battery: {battery_level}%")

        # Required delay after initialization
        time.sleep(0.5)

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
        copies: int = 1,
        transfer_timeout: int = 60,
        **options,
    ) -> None:
        """Print an image.

        Args:
            image_path: Path to image file.
            auto_crop: If True, crop to fill. If False, fit with letterboxing.
            quality: JPEG quality (1-100).
            copies: Number of copies to print (1-255).
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

        # Prepare printer for image transfer
        error_code = self._perform_task(PrintReadyTask(image_length, num_copies=copies))
        if error_code != ERR_SUCCESS:
            raise PrintError(get_error_message(error_code), device_error=str(error_code))

        # Required delay after PRINT_READY
        time.sleep(0.1)

        # Send image data in chunks
        start_index = 0
        while start_index < image_length:
            end_index = min(start_index + CHUNK_SIZE, image_length)
            chunk = image_data[start_index:end_index]
            self._client.outbound_q.put(chunk)
            start_index = end_index

            # Inter-chunk delay
            time.sleep(INTER_CHUNK_DELAY_MS / 1000.0)

        logger.debug("Image data queued, printer should start printing...")

    def get_status(self) -> PrinterStatus:
        """Get current printer status."""
        # Get battery from accessory info
        battery_level, is_charging = self._perform_task(
            GetAccessoryInfoTask(is_slim=self._is_slim)
        )
        self._battery_level = battery_level

        # Check charging status
        is_charging = self._perform_task(GetBatteryLevelTask())
        self._is_charging = is_charging

        time.sleep(0.1)

        # Check paper status
        paper_error = self._perform_task(GetPageTypeTask())

        # Determine error message
        error = None
        is_cover_open = False
        if paper_error == ERR_COVER_OPEN:
            error = "Cover is open"
            is_cover_open = True
        elif paper_error == ERR_NO_PAPER:
            error = "No paper"
        elif paper_error != ERR_SUCCESS:
            error = get_error_message(paper_error)

        is_ready = error is None and battery_level >= MIN_BATTERY_LEVEL

        return PrinterStatus(
            battery_level=battery_level,
            is_ready=is_ready,
            error=error,
            is_cover_open=is_cover_open,
            is_charging=is_charging,
        )

    def get_settings(self) -> Dict[str, Any]:
        """Get printer settings."""
        # Get auto power-off setting
        auto_off = self._perform_task(GetAutoPowerOffTask())
        time.sleep(0.1)

        # Get print count
        print_count = self._perform_task(GetPrintCountTask())

        return {
            "auto_power_off": auto_off,
            "print_count": print_count,
        }

    def _check_print_worthiness(self) -> None:
        """Check if printer is ready to print, raise appropriate error if not."""
        status = self.get_status()

        if status.is_cover_open:
            raise CoverOpenError()

        if status.error == "No paper":
            raise NoPaperError()

        if status.battery_level < MIN_BATTERY_LEVEL:
            raise LowBatteryError(
                f"Battery at {status.battery_level}%, need {MIN_BATTERY_LEVEL}%",
                level=status.battery_level,
            )

        if status.error:
            raise PrintError(status.error)

    def _perform_task(self, task: BaseTask):
        """Execute a protocol task and return the result."""
        self._send_message(task.get_message())
        response = self._receive_message()

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
                response = parse_response(data)

                logger.debug(
                    f"Received: cmd={response.command}, error={response.error_code}"
                )
                return response

            except queue.Empty:
                continue
            except ValueError as e:
                raise ProtocolError(str(e))

        raise TimeoutError(f"No response within {timeout} seconds")
