"""Mock implementations for testing."""

from typing import Dict, List, Optional, Tuple

from zinkwell.bluetooth.base import BluetoothTransport


class MockTransport(BluetoothTransport):
    """Mock Bluetooth transport for testing.

    Simulates printer responses without actual Bluetooth hardware.
    Records all sent commands for verification.

    Example:
        mock = MockTransport(responses={
            b"\\x43\\x0f...": b"response_bytes...",
        })
        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        # Verify commands sent
        assert len(mock.sent_commands) == 1
    """

    def __init__(self, responses: Optional[Dict[bytes, bytes]] = None):
        """Initialize mock transport.

        Args:
            responses: Mapping of command prefixes to response bytes.
                       When send() is called, looks up response by first 8 bytes.
        """
        self.responses = responses or {}
        self.sent_commands: List[bytes] = []
        self._connected = False
        self._blocking = True
        self._pending_response: Optional[bytes] = None
        self._address: Optional[str] = None
        self._port: Optional[int] = None

    def connect(self, address: str, port: int) -> None:
        """Simulate connection."""
        self._address = address
        self._port = port
        self._connected = True

    def disconnect(self) -> None:
        """Simulate disconnection."""
        self._connected = False
        self._address = None
        self._port = None

    def send(self, data: bytes) -> int:
        """Record sent data and queue response.

        Looks up response by command prefix (first 8 bytes).
        """
        self.sent_commands.append(data)

        # Look up response by command prefix
        cmd_prefix = data[:8] if len(data) >= 8 else data
        self._pending_response = self.responses.get(cmd_prefix)

        return len(data)

    def recv(self, size: int) -> bytes:
        """Return queued response."""
        if not self._blocking and self._pending_response is None:
            raise BlockingIOError("No data available")

        response = self._pending_response or b""
        self._pending_response = None
        return response[:size]

    def set_blocking(self, blocking: bool) -> None:
        """Set blocking mode."""
        self._blocking = blocking

    def is_connected(self) -> bool:
        """Check connection state."""
        return self._connected

    def get_peer_name(self) -> Tuple[str, int]:
        """Return simulated peer address."""
        if not self._connected:
            raise OSError("Not connected")
        return (self._address or "AA:BB:CC:DD:EE:FF", self._port or 1)

    def clear(self) -> None:
        """Clear recorded commands and pending responses."""
        self.sent_commands.clear()
        self._pending_response = None
