"""Printer status and info data models."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PrinterStatus:
    """Normalized printer status across all printer types.

    This provides a common interface for checking printer state,
    regardless of the underlying device protocol.
    """

    battery_level: int
    """Battery level as percentage (0-100)."""

    is_ready: bool
    """Whether the printer can accept a print job."""

    error: Optional[str] = None
    """Human-readable error message, or None if no error."""

    # Optional fields - not all printers support these
    paper_remaining: Optional[int] = None
    """Number of prints remaining, if known."""

    is_cover_open: Optional[bool] = None
    """Whether the cover is open, if detectable."""

    is_charging: Optional[bool] = None
    """Whether the printer is charging, if detectable."""


@dataclass
class PrinterInfo:
    """Static printer information and specifications.

    This contains device metadata that doesn't change during operation.
    """

    name: str
    """Human-readable printer name (e.g., "Canon Ivy 2")."""

    model: str
    """Model identifier used in get_printer() (e.g., "canon_ivy2")."""

    print_width: int
    """Print width in pixels."""

    print_height: int
    """Print height in pixels."""

    supported_formats: List[str] = field(default_factory=lambda: ["JPEG", "PNG"])
    """List of supported input image formats."""

    firmware_version: Optional[str] = None
    """Firmware version, if available."""

    serial_number: Optional[str] = None
    """Serial number, if available."""
