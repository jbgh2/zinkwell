"""Abstract base class for printer implementations."""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

from ..models import PrinterStatus, PrinterInfo, PrinterCapabilities


class Printer(ABC):
    """Abstract base class for all printer implementations.

    Each printer type (Canon Ivy 2, Kodak, etc.) implements this interface,
    providing a consistent API regardless of the underlying protocol.

    Subclasses handle:
    - Device-specific protocol logic
    - Image preparation for that printer
    - Status parsing and normalization
    """

    @property
    @abstractmethod
    def capabilities(self) -> PrinterCapabilities:
        """Return printer capabilities."""
        pass

    @property
    @abstractmethod
    def info(self) -> PrinterInfo:
        """Return static printer information."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if printer is connected."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to printer.

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to printer.

        Safe to call even if not connected.
        """
        pass

    @abstractmethod
    def print(self, image_path: str, **options) -> None:
        """Print an image.

        Args:
            image_path: Path to image file.
            **options: Printer-specific options (copies, quality, etc.)

        Raises:
            PrintError: If print fails (low battery, no paper, etc.)
            ConnectionError: If not connected.
            FileNotFoundError: If image doesn't exist.
        """
        pass

    @abstractmethod
    def get_status(self) -> PrinterStatus:
        """Get current printer status.

        Returns:
            Normalized PrinterStatus.

        Raises:
            ConnectionError: If not connected.
        """
        pass

    # Optional methods with default implementations

    def get_settings(self) -> Dict[str, Any]:
        """Get printer settings.

        Override if the printer supports settings.

        Returns:
            Dict of setting names to values.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(f"{self.info.name} does not support settings")

    def set_setting(self, key: str, value: Any) -> None:
        """Set a printer setting.

        Override if the printer supports settings.

        Args:
            key: Setting name.
            value: Setting value.

        Raises:
            NotImplementedError: If not supported.
            ValueError: If setting name or value is invalid.
        """
        raise NotImplementedError(f"{self.info.name} does not support settings")

    def reboot(self) -> None:
        """Reboot the printer.

        Override if the printer supports reboot.

        Raises:
            NotImplementedError: If not supported.
        """
        raise NotImplementedError(f"{self.info.name} does not support reboot")

    # Context manager support

    def __enter__(self) -> "Printer":
        """Enter context manager - connect to printer."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - disconnect from printer."""
        self.disconnect()
