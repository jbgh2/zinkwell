"""Zinkwell exception types.

All exceptions inherit from ZinkwellError for easy catching.
Device-specific details are attached to exceptions where relevant.
"""

from typing import Optional


class ZinkwellError(Exception):
    """Base exception for all Zinkwell errors."""

    pass


class ConnectionError(ZinkwellError):
    """Failed to connect or lost connection to printer."""

    pass


class TransportError(ZinkwellError):
    """Low-level Bluetooth transport error."""

    pass


class ProtocolError(ZinkwellError):
    """Printer protocol error (unexpected response, invalid ACK, etc.)."""

    def __init__(self, message: str, expected: Optional[int] = None, got: Optional[int] = None):
        super().__init__(message)
        self.expected = expected
        self.got = got


class PrintError(ZinkwellError):
    """Print operation failed.

    Attributes:
        device_error: Device-specific error code/name (e.g., "cover_open", "no_paper")
    """

    def __init__(self, message: str, device_error: Optional[str] = None):
        super().__init__(message)
        self.device_error = device_error


class LowBatteryError(PrintError):
    """Battery too low to print."""

    def __init__(self, message: str = "Battery too low to print", level: Optional[int] = None):
        super().__init__(message, device_error="low_battery")
        self.level = level


class CoverOpenError(PrintError):
    """Printer cover is open."""

    def __init__(self, message: str = "Printer cover is open"):
        super().__init__(message, device_error="cover_open")


class NoPaperError(PrintError):
    """No paper in printer."""

    def __init__(self, message: str = "No paper in printer"):
        super().__init__(message, device_error="no_paper")


class PaperJamError(PrintError):
    """Paper is jammed."""

    def __init__(self, message: str = "Paper jam detected"):
        super().__init__(message, device_error="paper_jam")


class TimeoutError(ZinkwellError):
    """Operation timed out waiting for response."""

    pass
