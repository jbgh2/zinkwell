"""Factory functions for creating printer instances."""

from typing import Optional, Dict

from .devices import DEVICE_REGISTRY
from .devices.base import Printer
from .models import PrinterInfo


def get_printer(
    device_type: str,
    address: str,
    port: int = 1,
    transport: Optional[str] = None,
) -> Printer:
    """Create a printer instance.

    Args:
        device_type: Printer type identifier (e.g., "canon_ivy2", "kodak_snap").
        address: Bluetooth MAC address (e.g., "AA:BB:CC:DD:EE:FF").
        port: RFCOMM port (default 1).
        transport: Force specific transport ("native", "pybluez"), or None for auto.

    Returns:
        Configured Printer instance ready to connect.

    Raises:
        ValueError: If device_type is not recognized.

    Example:
        printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
        printer.connect()
        printer.print("photo.jpg")
        printer.disconnect()

    Example with context manager:
        with get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF") as printer:
            printer.print("photo.jpg")
    """
    if device_type not in DEVICE_REGISTRY:
        available = ", ".join(DEVICE_REGISTRY.keys()) if DEVICE_REGISTRY else "(none yet)"
        raise ValueError(
            f"Unknown device type: '{device_type}'. Available: {available}"
        )

    printer_class = DEVICE_REGISTRY[device_type]
    return printer_class(address=address, port=port, transport=transport)


def list_supported_printers() -> Dict[str, PrinterInfo]:
    """List all supported printer types.

    Returns:
        Dict mapping device type names to PrinterInfo objects.

    Example:
        for name, info in list_supported_printers().items():
            print(f"{name}: {info.name} ({info.print_width}x{info.print_height})")
    """
    result = {}
    for name, printer_class in DEVICE_REGISTRY.items():
        # Get info from class - each printer class should have an info property
        # For now, we create a temporary instance concept or use class attribute
        if hasattr(printer_class, "_info"):
            result[name] = printer_class._info
    return result
