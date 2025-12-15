"""Unit tests for ThreadedClient."""

import time
from unittest.mock import MagicMock

import pytest

from zinkwell.utils.threading import ThreadedClient
from zinkwell.exceptions import TransportError


class TestThreadedClientTransportErrors:
    """Tests for transport error handling in the I/O thread."""

    def test_transport_error_clears_alive_flag(self):
        """Transport error during send should clear alive flag."""
        mock_transport = MagicMock()
        mock_transport.is_connected.return_value = True
        mock_transport.send.side_effect = TransportError("Connection lost")

        client = ThreadedClient(mock_transport)
        client.alive.set()
        client.start()

        # Queue a message to trigger send
        client.outbound_q.put(b"test")

        # Wait for thread to process and exit
        client.join(timeout=1)

        # alive should be cleared after transport error
        assert not client.alive.is_set()

    def test_os_error_clears_alive_flag(self):
        """OSError during send should clear alive flag."""
        mock_transport = MagicMock()
        mock_transport.is_connected.return_value = True
        mock_transport.send.side_effect = OSError("Bluetooth disconnected")

        client = ThreadedClient(mock_transport)
        client.alive.set()
        client.start()

        # Queue a message to trigger send
        client.outbound_q.put(b"test")

        # Wait for thread to process and exit
        client.join(timeout=1)

        assert not client.alive.is_set()

    def test_normal_disconnect_clears_alive_flag(self):
        """Normal disconnect should clear alive flag."""
        mock_transport = MagicMock()
        mock_transport.is_connected.return_value = False

        client = ThreadedClient(mock_transport)
        client.alive.set()
        client.start()

        # Thread should exit because is_connected returns False
        client.join(timeout=1)

        assert not client.alive.is_set()
