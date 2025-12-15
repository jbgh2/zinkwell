"""Device implementations."""

from .base import Printer
from .canon_ivy2 import CanonIvy2Printer

# Device registry - maps model names to printer classes
DEVICE_REGISTRY = {
    "canon_ivy2": CanonIvy2Printer,
}

__all__ = [
    "Printer",
    "CanonIvy2Printer",
    "DEVICE_REGISTRY",
]
