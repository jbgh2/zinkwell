"""Abstract base class for Bluetooth transports."""

from abc import ABC, abstractmethod
from typing import Tuple


class BluetoothTransport(ABC):
    """Abstract base class for Bluetooth backends.

    This provides a minimal socket-like interface for Bluetooth RFCOMM
    communication. Implementations handle platform-specific details.

    The transport layer is intentionally simple - just raw socket operations.
    Threading, queuing, and higher-level logic belong in the device layer.
    """

    @abstractmethod
    def connect(self, address: str, port: int) -> None:
        """Connect to a Bluetooth device.

        Args:
            address: Bluetooth MAC address (e.g., "AA:BB:CC:DD:EE:FF")
            port: RFCOMM channel (typically 1)

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the Bluetooth connection.

        Safe to call even if not connected.
        """
        pass

    @abstractmethod
    def send(self, data: bytes) -> int:
        """Send data over the connection.

        Args:
            data: Bytes to send.

        Returns:
            Number of bytes sent.

        Raises:
            ConnectionError: If not connected.
            TransportError: If send fails.
        """
        pass

    @abstractmethod
    def recv(self, size: int) -> bytes:
        """Receive data from the connection.

        Args:
            size: Maximum number of bytes to receive.

        Returns:
            Received bytes (may be less than size).

        Raises:
            ConnectionError: If not connected.
            TransportError: If receive fails.
            BlockingIOError: If non-blocking and no data available.
        """
        pass

    @abstractmethod
    def set_blocking(self, blocking: bool) -> None:
        """Set socket blocking mode.

        Args:
            blocking: True for blocking, False for non-blocking.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the connection is active.

        Returns:
            True if connected, False otherwise.
        """
        pass

    @abstractmethod
    def get_peer_name(self) -> Tuple[str, int]:
        """Get the remote device address.

        Returns:
            Tuple of (address, port).

        Raises:
            ConnectionError: If not connected.
        """
        pass
