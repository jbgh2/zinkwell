"""Native Python socket-based Bluetooth transport.

Uses Python's built-in socket module with AF_BLUETOOTH for RFCOMM
communication. Works on Windows and Linux without external dependencies.
"""

import socket
from typing import Tuple, Optional

from .base import BluetoothTransport
from ..exceptions import ConnectionError, TransportError


class NativeTransport(BluetoothTransport):
    """Bluetooth transport using Python's native socket module.

    This uses socket.AF_BLUETOOTH with socket.BTPROTO_RFCOMM for
    serial port communication over Bluetooth.

    Supported platforms:
    - Windows (tested)
    - Linux (should work)
    - macOS (not supported - no AF_BLUETOOTH)
    """

    def __init__(self):
        self._socket: Optional[socket.socket] = None

    def connect(self, address: str, port: int) -> None:
        """Connect to a Bluetooth device.

        Args:
            address: Bluetooth MAC address (e.g., "AA:BB:CC:DD:EE:FF")
            port: RFCOMM channel (typically 1)

        Raises:
            ConnectionError: If connection fails.
        """
        try:
            self._socket = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_STREAM,
                socket.BTPROTO_RFCOMM,
            )
            self._socket.connect((address, port))
        except OSError as e:
            self._socket = None
            raise ConnectionError(f"Failed to connect to {address}:{port}: {e}") from e

    def disconnect(self) -> None:
        """Close the Bluetooth connection."""
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass  # Ignore errors on close
            finally:
                self._socket = None

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
        if self._socket is None:
            raise ConnectionError("Not connected")

        try:
            self._socket.sendall(data)
            return len(data)
        except OSError as e:
            raise TransportError(f"Send failed: {e}") from e

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
        if self._socket is None:
            raise ConnectionError("Not connected")

        try:
            return self._socket.recv(size)
        except BlockingIOError:
            raise  # Let caller handle non-blocking case
        except OSError as e:
            raise TransportError(f"Receive failed: {e}") from e

    def set_blocking(self, blocking: bool) -> None:
        """Set socket blocking mode.

        Args:
            blocking: True for blocking, False for non-blocking.
        """
        if self._socket is not None:
            self._socket.setblocking(blocking)

    def is_connected(self) -> bool:
        """Check if the connection is active.

        Returns:
            True if connected, False otherwise.
        """
        if self._socket is None:
            return False

        try:
            self._socket.getpeername()
            return True
        except OSError:
            return False

    def get_peer_name(self) -> Tuple[str, int]:
        """Get the remote device address.

        Returns:
            Tuple of (address, port).

        Raises:
            ConnectionError: If not connected.
        """
        if self._socket is None:
            raise ConnectionError("Not connected")

        try:
            return self._socket.getpeername()
        except OSError as e:
            raise ConnectionError(f"Failed to get peer name: {e}") from e
