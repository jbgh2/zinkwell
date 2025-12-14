"""Unit tests for native Bluetooth transport."""

import socket
from unittest.mock import Mock, patch, MagicMock

import pytest

from zinkwell.bluetooth.native import NativeTransport
from zinkwell.exceptions import ConnectionError, TransportError


class TestNativeTransport:
    """Tests for NativeTransport."""

    def test_init_not_connected(self):
        """Transport starts disconnected."""
        transport = NativeTransport()
        assert not transport.is_connected()

    @patch("socket.socket")
    def test_connect_creates_bluetooth_socket(self, mock_socket_class):
        """Connect creates socket with correct parameters."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        mock_socket_class.assert_called_once_with(
            socket.AF_BLUETOOTH,
            socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM,
        )
        mock_socket.connect.assert_called_once_with(("AA:BB:CC:DD:EE:FF", 1))

    @patch("socket.socket")
    def test_connect_failure_raises_connection_error(self, mock_socket_class):
        """Connection failure raises ConnectionError."""
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = OSError("Connection refused")
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()

        with pytest.raises(ConnectionError, match="Failed to connect"):
            transport.connect("AA:BB:CC:DD:EE:FF", 1)

    @patch("socket.socket")
    def test_disconnect_closes_socket(self, mock_socket_class):
        """Disconnect closes the socket."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)
        transport.disconnect()

        mock_socket.close.assert_called_once()

    def test_disconnect_when_not_connected_is_safe(self):
        """Disconnecting when not connected doesn't raise."""
        transport = NativeTransport()
        transport.disconnect()  # Should not raise

    @patch("socket.socket")
    def test_send_returns_bytes_sent(self, mock_socket_class):
        """Send returns number of bytes sent."""
        mock_socket = MagicMock()
        mock_socket.send.return_value = 10
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        result = transport.send(b"0123456789")

        assert result == 10
        mock_socket.send.assert_called_once_with(b"0123456789")

    def test_send_when_not_connected_raises(self):
        """Send when not connected raises ConnectionError."""
        transport = NativeTransport()

        with pytest.raises(ConnectionError, match="Not connected"):
            transport.send(b"data")

    @patch("socket.socket")
    def test_recv_returns_data(self, mock_socket_class):
        """Recv returns received data."""
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"response"
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        result = transport.recv(1024)

        assert result == b"response"

    def test_recv_when_not_connected_raises(self):
        """Recv when not connected raises ConnectionError."""
        transport = NativeTransport()

        with pytest.raises(ConnectionError, match="Not connected"):
            transport.recv(1024)

    @patch("socket.socket")
    def test_set_blocking(self, mock_socket_class):
        """Set blocking mode on socket."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        transport.set_blocking(False)
        mock_socket.setblocking.assert_called_with(False)

        transport.set_blocking(True)
        mock_socket.setblocking.assert_called_with(True)

    @patch("socket.socket")
    def test_is_connected_true_when_connected(self, mock_socket_class):
        """is_connected returns True when connected."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        assert transport.is_connected()

    @patch("socket.socket")
    def test_is_connected_false_after_disconnect(self, mock_socket_class):
        """is_connected returns False after disconnect."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)
        transport.disconnect()

        assert not transport.is_connected()

    @patch("socket.socket")
    def test_get_peer_name(self, mock_socket_class):
        """get_peer_name returns address tuple."""
        mock_socket = MagicMock()
        mock_socket.getpeername.return_value = ("AA:BB:CC:DD:EE:FF", 1)
        mock_socket_class.return_value = mock_socket

        transport = NativeTransport()
        transport.connect("AA:BB:CC:DD:EE:FF", 1)

        result = transport.get_peer_name()

        assert result == ("AA:BB:CC:DD:EE:FF", 1)

    def test_get_peer_name_when_not_connected_raises(self):
        """get_peer_name when not connected raises ConnectionError."""
        transport = NativeTransport()

        with pytest.raises(ConnectionError, match="Not connected"):
            transport.get_peer_name()
