"""Device implementations."""

from .base import Printer
from .canon_ivy2 import CanonIvy2Printer
from .kodak_step import KodakStepPrinter

# Device registry - maps model names to printer classes
DEVICE_REGISTRY = {
    "canon_ivy2": CanonIvy2Printer,
    "kodak_step": KodakStepPrinter,
}

__all__ = [
    "Printer",
    "CanonIvy2Printer",
    "KodakStepPrinter",
    "DEVICE_REGISTRY",
]
