"""Kodak Step protocol implementation.

This module handles the binary protocol for communicating with
Kodak Step series printers over Bluetooth RFCOMM.

Protocol details:
- Packet size: 34 bytes
- Header: 0x1B 0x2A 0x43 0x41 (ESC * C A)
- Commands and responses use same header structure
"""

from dataclasses import dataclass
from typing import Tuple, Optional

# Protocol constants
PACKET_SIZE = 34
CHUNK_SIZE = 4096
INTER_CHUNK_DELAY_MS = 20
MIN_BATTERY_LEVEL = 30

# Header bytes
HEADER = bytes([0x1B, 0x2A, 0x43, 0x41])  # ESC * C A

# Command codes (byte 6)
CMD_PRINT_READY = 0x00
CMD_GET_ACCESSORY_INFO = 0x01
CMD_GET_PAGE_TYPE = 0x0D
CMD_GET_BATTERY_LEVEL = 0x0E
CMD_GET_PRINT_COUNT = 0x0F
CMD_GET_AUTO_POWER_OFF = 0x10

# Device type flags (byte 5)
FLAG_STANDARD_DEVICE = 0x00
FLAG_SLIM_DEVICE = 0x02

# Error codes (response byte 8)
ERR_SUCCESS = 0x00
ERR_PAPER_JAM = 0x01
ERR_NO_PAPER = 0x02
ERR_COVER_OPEN = 0x03
ERR_PAPER_MISMATCH = 0x04
ERR_LOW_BATTERY = 0x05
ERR_OVERHEATING = 0x06
ERR_COOLING = 0x07
ERR_MISFEED = 0x08
ERR_BUSY = 0x09
ERR_NOT_CONNECTED = 0xFE

ERROR_MESSAGES = {
    ERR_SUCCESS: None,
    ERR_PAPER_JAM: "Paper jam",
    ERR_NO_PAPER: "No paper",
    ERR_COVER_OPEN: "Cover open",
    ERR_PAPER_MISMATCH: "Paper mismatch",
    ERR_LOW_BATTERY: "Low battery",
    ERR_OVERHEATING: "Overheating",
    ERR_COOLING: "Cooling down",
    ERR_MISFEED: "Paper misfeed",
    ERR_BUSY: "Printer busy",
    ERR_NOT_CONNECTED: "Not connected",
}


def get_error_message(error_code: int) -> Optional[str]:
    """Get human-readable error message for an error code."""
    return ERROR_MESSAGES.get(error_code, f"Unknown error ({error_code})")


@dataclass
class ParsedResponse:
    """Parsed response from printer."""

    raw_data: bytes
    command: int
    sub_type: int
    error_code: int
    payload: bytes


def build_packet(
    command: int,
    flags1: int = 0x00,
    flags2: int = 0x00,
    flags3: int = 0x00,
) -> bytearray:
    """Build a 34-byte packet with header.

    Args:
        command: Command code (byte 6).
        flags1: Flags byte 1 (byte 4).
        flags2: Flags byte 2 (byte 5).
        flags3: Flags byte 3 (byte 7).

    Returns:
        34-byte packet buffer.
    """
    packet = bytearray(PACKET_SIZE)
    packet[0:4] = HEADER
    packet[4] = flags1
    packet[5] = flags2
    packet[6] = command
    packet[7] = flags3
    return packet


def parse_response(data: bytes) -> ParsedResponse:
    """Parse an incoming response from the printer.

    Args:
        data: Raw bytes received from printer (34 bytes).

    Returns:
        ParsedResponse with extracted fields.

    Raises:
        ValueError: If response header is invalid.
    """
    if len(data) < PACKET_SIZE:
        raise ValueError(f"Response too short: {len(data)} bytes, expected {PACKET_SIZE}")

    if data[0:4] != HEADER:
        raise ValueError(f"Invalid header: {data[0:4].hex()}")

    return ParsedResponse(
        raw_data=data,
        command=data[6],
        sub_type=data[7],
        error_code=data[8],
        payload=data[9:],
    )


def validate_response(data: bytes) -> Tuple[bool, int]:
    """Validate response header and extract error code.

    Args:
        data: Raw response bytes.

    Returns:
        Tuple of (is_valid_header, error_code).
    """
    if len(data) < PACKET_SIZE:
        return False, ERR_NOT_CONNECTED

    if data[0:4] != HEADER:
        return False, ERR_NOT_CONNECTED

    return True, data[8]


# Task classes for each command type


class BaseTask:
    """Base class for protocol tasks."""

    command: int = 0

    def get_message(self) -> bytes:
        """Build the command message."""
        raise NotImplementedError

    def process_response(self, response: ParsedResponse):
        """Process the response from printer."""
        pass


class GetAccessoryInfoTask(BaseTask):
    """Initialize connection and handshake with printer.

    Must be sent first after connecting.
    """

    command = CMD_GET_ACCESSORY_INFO

    def __init__(self, is_slim: bool = False):
        """Initialize task.

        Args:
            is_slim: True for Step Slim or Snap 2 devices.
        """
        self.is_slim = is_slim

    def get_message(self) -> bytes:
        flags2 = FLAG_SLIM_DEVICE if self.is_slim else FLAG_STANDARD_DEVICE
        packet = build_packet(CMD_GET_ACCESSORY_INFO, flags2=flags2)
        return bytes(packet)

    def process_response(self, response: ParsedResponse) -> Tuple[int, bool]:
        """Parse accessory info response.

        Returns:
            Tuple of (battery_level, is_charging).
            Battery level is in byte 12 (index 3 of payload after byte 9).
        """
        # Battery level is at byte 12 of full response (payload index 3)
        battery_level = response.raw_data[12] if len(response.raw_data) > 12 else 0
        # Charging status might be elsewhere - for now return False
        return battery_level, False


class GetBatteryLevelTask(BaseTask):
    """Query charging status.

    Note: This returns charging status (1=charging), not battery percentage.
    Battery percentage comes from GET_ACCESSORY_INFO response.
    """

    command = CMD_GET_BATTERY_LEVEL

    def get_message(self) -> bytes:
        packet = build_packet(CMD_GET_BATTERY_LEVEL)
        return bytes(packet)

    def process_response(self, response: ParsedResponse) -> bool:
        """Parse battery level response.

        Returns:
            True if charging, False otherwise.
        """
        # Byte 8 contains charging status: 1 = charging, 0 = not charging
        return response.error_code == 1


class GetPageTypeTask(BaseTask):
    """Query paper status."""

    command = CMD_GET_PAGE_TYPE

    def get_message(self) -> bytes:
        packet = build_packet(CMD_GET_PAGE_TYPE)
        return bytes(packet)

    def process_response(self, response: ParsedResponse) -> int:
        """Parse page type response.

        Returns:
            Error code (0 = paper OK).
        """
        return response.error_code


class GetPrintCountTask(BaseTask):
    """Query total print count."""

    command = CMD_PRINT_READY  # Uses same command byte as PRINT_READY

    def get_message(self) -> bytes:
        # Distinguished from PRINT_READY by byte 7 = 0x01
        packet = build_packet(CMD_PRINT_READY, flags3=0x01)
        return bytes(packet)

    def process_response(self, response: ParsedResponse) -> int:
        """Parse print count response.

        Returns:
            Total number of prints.
        """
        # Print count is 16-bit big-endian in bytes 8-9
        return (response.raw_data[8] << 8) | response.raw_data[9]


class GetAutoPowerOffTask(BaseTask):
    """Query auto power-off setting."""

    command = CMD_GET_AUTO_POWER_OFF

    def get_message(self) -> bytes:
        packet = build_packet(CMD_GET_AUTO_POWER_OFF)
        return bytes(packet)

    def process_response(self, response: ParsedResponse) -> int:
        """Parse auto power-off response.

        Returns:
            Auto power-off timeout in minutes.
        """
        return response.raw_data[8]


class PrintReadyTask(BaseTask):
    """Prepare printer to receive image data."""

    command = CMD_PRINT_READY

    def __init__(self, image_size: int, num_copies: int = 1):
        """Initialize task.

        Args:
            image_size: Size of image data in bytes.
            num_copies: Number of copies to print (1-255).
        """
        self.image_size = image_size
        self.num_copies = num_copies

    def get_message(self) -> bytes:
        packet = build_packet(CMD_PRINT_READY)

        # Image size - 3 bytes, big-endian (bytes 8-10)
        packet[8] = (self.image_size >> 16) & 0xFF
        packet[9] = (self.image_size >> 8) & 0xFF
        packet[10] = self.image_size & 0xFF

        # Number of copies (byte 11)
        packet[11] = self.num_copies

        return bytes(packet)

    def process_response(self, response: ParsedResponse) -> int:
        """Parse print ready response.

        Returns:
            Error code (0 = ready to receive image).
        """
        return response.error_code
