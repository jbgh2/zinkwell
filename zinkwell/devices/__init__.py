"""Device implementations."""

from .base import Printer

# Import device implementations to register them
# from .canon_ivy2 import CanonIvy2Printer  # TODO: Phase 2

# Device registry - maps model names to printer classes
DEVICE_REGISTRY = {
    # "canon_ivy2": CanonIvy2Printer,  # TODO: Phase 2
}

__all__ = [
    "Printer",
    "DEVICE_REGISTRY",
]
