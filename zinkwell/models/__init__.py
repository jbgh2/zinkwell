"""Data models for Zinkwell."""

from .status import PrinterStatus, PrinterInfo
from .capabilities import PrinterCapabilities

__all__ = [
    "PrinterStatus",
    "PrinterInfo",
    "PrinterCapabilities",
]
