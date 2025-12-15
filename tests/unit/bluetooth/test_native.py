"""Unit tests for native Bluetooth transport.

These tests focus on behavior we can verify without actual Bluetooth hardware.
Connected-state behavior is tested in integration tests.
"""

import socket
from unittest.mock import MagicMock, patch

import pytest

from zinkwell.bluetooth.native import NativeTransport
from zinkwell.exceptions import ConnectionError


class TestNativeTransportDisconnectedState:
    """Tests for transport behavior when disconnected."""

    def test_starts_disconnected(self):
        """Transport starts in disconnected state."""
        transport = NativeTransport()
        assert not transport.is_connected()

    def test_disconnect_when_not_connected_is_safe(self):
        """Disconnecting when not connected should not raise."""
        transport = NativeTransport()
        transport.disconnect()  # Should not raise

    def test_send_when_not_connected_raises(self):
        """Send when not connected should raise ConnectionError."""
        transport = NativeTransport()
        with pytest.raises(ConnectionError, match="Not connected"):
            transport.send(b"data")

    def test_recv_when_not_connected_raises(self):
        """Recv when not connected should raise ConnectionError."""
        transport = NativeTransport()
        with pytest.raises(ConnectionError, match="Not connected"):
            transport.recv(1024)

    def test_get_peer_name_when_not_connected_raises(self):
        """get_peer_name when not connected should raise ConnectionError."""
        transport = NativeTransport()
        with pytest.raises(ConnectionError, match="Not connected"):
            transport.get_peer_name()


class TestNativeTransportConnection:
    """Tests for connection behavior."""

    @patch("socket.socket")
    def test_connection_failure_raises_connection_error(self, mock_socket_class):
        """Connection failure should raise ConnectionError with details."""
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = OSError("Connection refused")
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()

        with pytest.raises(ConnectionError, match="Failed to connect"):
            transport.connect("AA:BB:CC:DD:EE:FF", 1)

    @patch("socket.socket")
    def test_uses_bluetooth_rfcomm_socket(self, mock_socket_class):
        """Connect should use Bluetooth RFCOMM socket type."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        mock_socket_class.assert_called_once_with(
            socket.AF_BLUETOOTH,
            socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM,
        )

    @patch("socket.socket")
    def test_disconnect_closes_socket(self, mock_socket_class):
        """Disconnect should close the socket."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)
        transport.disconnect()

        mock_socket.close.assert_called_once()
        assert not transport.is_connected()
