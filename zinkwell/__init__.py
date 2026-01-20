"""Zinkwell - Cross-platform Bluetooth photo printer library.

A Python library for controlling Zink-based photo printers like
Canon Ivy 2, Kodak Mini, and similar devices.

Example:
    from zinkwell import get_printer

    printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
    printer.connect()
    printer.print("photo.jpg")
    printer.disconnect()
"""

from .factory import get_printer, list_supported_printers
from .exceptions import (
    ZinkwellError,
    ConnectionError,
    PrintError,
    TransportError,
    ProtocolError,
)

__version__ = "0.1.0"
__all__ = [
    "get_printer",
    "list_supported_printers",
    "ZinkwellError",
    "ConnectionError",
    "PrintError",
    "TransportError",
    "ProtocolError",
]
