"""Bluetooth transport layer."""

from .base import BluetoothTransport
from .native import NativeTransport

__all__ = [
    "BluetoothTransport",
    "NativeTransport",
    "get_transport",
]


def get_transport(transport_type: str = None) -> BluetoothTransport:
    """Get a Bluetooth transport instance.

    Args:
        transport_type: Transport type to use. Options:
            - "native": Python socket-based (default, works on Windows/Linux)
            - "pybluez": PyBluez-based (Linux fallback)
            - None: Auto-detect best available

    Returns:
        A BluetoothTransport instance.

    Raises:
        ValueError: If requested transport type is not available.
    """
    if transport_type is None or transport_type == "native":
        return NativeTransport()

    if transport_type == "pybluez":
        try:
            from .pybluez import PyBluezTransport

            return PyBluezTransport()
        except ImportError:
            raise ValueError("PyBluez transport requested but pybluez is not installed")

    raise ValueError(f"Unknown transport type: {transport_type}")
