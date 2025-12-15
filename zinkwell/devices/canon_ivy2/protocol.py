"""Canon Ivy 2 protocol implementation.

This module handles the binary protocol for communicating with
Canon Ivy 2 printers over Bluetooth RFCOMM.

Protocol details:
- Packet size: 34 bytes
- Start code: 0x430F (17167)
- Commands and ACKs use matching codes
"""

import struct
from dataclasses import dataclass
from typing import Tuple, Optional

# Protocol constants
START_CODE = 17167  # 0x430F
PACKET_SIZE = 34

# Command codes
COMMAND_START_SESSION = 0
COMMAND_GET_STATUS = 257
COMMAND_SETTING_ACCESSORY = 259
COMMAND_PRINT_READY = 769
COMMAND_REBOOT = 65535

# ACK codes (match command codes)
ACK_START_SESSION = 0
ACK_GET_STATUS = 257
ACK_SETTING_ACCESSORY = 259
ACK_PRINT_READY = 769
ACK_REBOOT = 65535


def parse_bit_range(value: int, size: int) -> int:
    """Extract a range of bits from a value.

    Args:
        value: Integer to extract bits from.
        size: Number of bits to extract.

    Returns:
        Extracted integer value.
    """
    bits = ""
    for i in range(size):
        bits += "1" if ((value >> i) & 1) == 1 else "0"

    try:
        return int(bits[::-1], 2)
    except ValueError:
        return 0


@dataclass
class ParsedMessage:
    """Parsed response from printer."""

    raw_data: bytes
    payload: bytes
    ack: int
    error: int


def parse_message(data: bytes) -> ParsedMessage:
    """Parse an incoming message from the printer.

    Args:
        data: Raw bytes received from printer.

    Returns:
        ParsedMessage with extracted fields.
    """
    payload = data[8:]
    ack = (data[6] & 255) | ((data[5] & 255) << 8)
    error = data[7] & 255

    return ParsedMessage(
        raw_data=data,
        payload=payload,
        ack=ack,
        error=error,
    )


def build_base_message(command: int, flag_1: bool = False, flag_2: bool = False) -> bytearray:
    """Build a base 34-byte message with header.

    Args:
        command: Command code.
        flag_1: If True, sets b1/b2 to -1/-1 (session init).
        flag_2: If True, sets write flag in header.

    Returns:
        34-byte message buffer.
    """
    b1 = -1 if flag_1 else 1
    b2 = -1 if flag_1 else 32

    message = bytearray(PACKET_SIZE)
    struct.pack_into(
        ">HhbHB",
        message,
        0,
        START_CODE,
        b1,
        b2,
        command,
        1 if flag_2 else 0,
    )

    return message


# Task classes for each command type


class BaseTask:
    """Base class for protocol tasks."""

    ack: int = 0

    def get_message(self) -> bytes:
        """Build the command message."""
        raise NotImplementedError

    def process_response(self, response: ParsedMessage):
        """Process the response from printer."""
        pass


class StartSessionTask(BaseTask):
    """Initialize session with printer, get battery and MTU."""

    ack = ACK_START_SESSION

    def get_message(self) -> bytes:
        return bytes(build_base_message(COMMAND_START_SESSION, flag_1=True, flag_2=False))

    def process_response(self, response: ParsedMessage) -> Tuple[int, int]:
        """Parse session response.

        Returns:
            Tuple of (battery_level, mtu).
        """
        data = response.raw_data
        battery_level = parse_bit_range((data[9] << 8) | data[10], 6)
        mtu = ((data[11] & 255) << 8) | (data[12] & 255)

        return battery_level, mtu


class GetStatusTask(BaseTask):
    """Get printer status (battery, errors, paper)."""

    ack = ACK_GET_STATUS

    def get_message(self) -> bytes:
        return bytes(build_base_message(COMMAND_GET_STATUS))

    def process_response(self, response: ParsedMessage) -> Tuple[int, int, int, bool, bool, bool]:
        """Parse status response.

        Returns:
            Tuple of (error_code, battery_level, usb_status,
                      is_cover_open, is_no_paper, is_wrong_smart_sheet).
        """
        payload = response.payload

        i = (payload[0] << 8) | payload[1]
        error_code = payload[2]
        battery_level = parse_bit_range(i, 6)
        usb_status = (i >> 7) & 1

        queue_flags = ((payload[4] & 255) << 8) | (payload[5] & 255)
        is_cover_open = (queue_flags & 1) == 1
        is_no_paper = (queue_flags & 2) == 2
        is_wrong_smart_sheet = (queue_flags & 16) == 16

        return error_code, battery_level, usb_status, is_cover_open, is_no_paper, is_wrong_smart_sheet


class GetSettingTask(BaseTask):
    """Get printer settings (auto-off, firmware, etc.)."""

    ack = ACK_SETTING_ACCESSORY

    def get_message(self) -> bytes:
        return bytes(build_base_message(COMMAND_SETTING_ACCESSORY))

    def process_response(self, response: ParsedMessage) -> Tuple[int, str, int, int, int]:
        """Parse settings response.

        Returns:
            Tuple of (auto_power_off, firmware_version, tmd_version,
                      number_of_photos_printed, color_id).
        """
        payload = response.payload

        auto_power_off = payload[0]
        firmware_version = f"{payload[1]}.{payload[2]}.{payload[3]}"
        tmd_version = payload[5]
        number_of_photos_printed = (payload[6] << 8) | payload[7]
        color_id = payload[8]

        return auto_power_off, firmware_version, tmd_version, number_of_photos_printed, color_id


class SetSettingTask(BaseTask):
    """Set printer settings (auto-off timer)."""

    ack = ACK_SETTING_ACCESSORY

    def __init__(self, auto_power_off: int):
        """Initialize with auto-off value.

        Args:
            auto_power_off: Minutes until auto power off (3, 5, or 10).
        """
        self.auto_power_off = auto_power_off

    def get_message(self) -> bytes:
        message = build_base_message(COMMAND_SETTING_ACCESSORY, flag_1=False, flag_2=True)
        struct.pack_into(">B", message, 8, self.auto_power_off)
        return bytes(message)


class GetPrintReadyTask(BaseTask):
    """Prepare printer to receive image data."""

    ack = ACK_PRINT_READY

    def __init__(self, length: int, flag: bool = False):
        """Initialize with image data length.

        Args:
            length: Length of image data in bytes.
            flag: Unknown flag (default False).
        """
        self.length = length
        self.flag = flag

    def get_message(self) -> bytes:
        message = build_base_message(COMMAND_PRINT_READY)

        # Pack image length as big-endian 32-bit
        b0 = (((-16777216) & self.length) >> 24) & 0xFF
        b1 = ((16711680 & self.length) >> 16) & 0xFF
        b2 = ((65280 & self.length) >> 8) & 0xFF
        b3 = self.length & 255
        b4 = 1
        b5 = 2 if self.flag else 1

        struct.pack_into(">BBBBBB", message, 8, b0, b1, b2, b3, b4, b5)
        return bytes(message)

    def process_response(self, response: ParsedMessage) -> Tuple[int, int]:
        """Parse print ready response.

        Returns:
            Tuple of (unknown, error_code).
        """
        payload = response.payload
        unknown = payload[2] & 255
        error_code = payload[3] & 255

        return unknown, error_code


class RebootTask(BaseTask):
    """Reboot the printer."""

    ack = ACK_REBOOT

    def get_message(self) -> bytes:
        message = build_base_message(COMMAND_REBOOT, flag_1=False, flag_2=True)
        struct.pack_into(">B", message, 8, 1)
        return bytes(message)
