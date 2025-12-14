"""Contract tests for BluetoothTransport implementations.

All transport implementations must pass these tests to ensure
consistent behavior across platforms.
"""

import pytest

from zinkwell.bluetooth.base import BluetoothTransport
from zinkwell.bluetooth.native import NativeTransport
from zinkwell.exceptions import ConnectionError


class TransportContractTests:
    """Base contract tests that all transports must pass.

    Subclass this and provide a transport fixture to test
    a specific implementation.
    """

    @pytest.fixture
    def transport(self) -> BluetoothTransport:
        """Return a transport instance to test."""
        raise NotImplementedError("Subclass must provide transport fixture")

    def test_starts_disconnected(self, transport: BluetoothTransport):
        """Transport starts in disconnected state."""
        assert not transport.is_connected()

    def test_disconnect_when_not_connected_is_safe(self, transport: BluetoothTransport):
        """Calling disconnect when not connected should not raise."""
        transport.disconnect()  # Should not raise

    def test_send_when_disconnected_raises(self, transport: BluetoothTransport):
        """Sending when not connected should raise ConnectionError."""
        with pytest.raises(ConnectionError):
            transport.send(b"data")

    def test_recv_when_disconnected_raises(self, transport: BluetoothTransport):
        """Receiving when not connected should raise ConnectionError."""
        with pytest.raises(ConnectionError):
            transport.recv(1024)

    def test_get_peer_name_when_disconnected_raises(self, transport: BluetoothTransport):
        """Getting peer name when not connected should raise ConnectionError."""
        with pytest.raises(ConnectionError):
            transport.get_peer_name()

    def test_set_blocking_when_disconnected_is_safe(self, transport: BluetoothTransport):
        """Setting blocking mode when not connected should not raise."""
        transport.set_blocking(True)
        transport.set_blocking(False)


class TestNativeTransportContract(TransportContractTests):
    """Contract tests for NativeTransport."""

    @pytest.fixture
    def transport(self) -> BluetoothTransport:
        return NativeTransport()


# Add more transport implementations here as they're created:
#
# class TestPyBluezTransportContract(TransportContractTests):
#     @pytest.fixture
#     def transport(self) -> BluetoothTransport:
#         return PyBluezTransport()
