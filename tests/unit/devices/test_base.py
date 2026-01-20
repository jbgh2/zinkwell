"""Unit tests for base Printer class."""

import pytest
import struct

from tests.mocks import MockTransport
from zinkwell.devices.base import Printer
from zinkwell.devices.canon_ivy2 import CanonIvy2Printer
from zinkwell.devices.canon_ivy2.protocol import START_CODE


def build_session_response(battery: int = 80, mtu: int = 512) -> bytes:
    """Build a session start response."""
    data = bytearray(34)
    data[5] = 0
    data[6] = 0
    data[9] = 0
    data[10] = battery
    data[11] = (mtu >> 8) & 0xFF
    data[12] = mtu & 0xFF
    return bytes(data)


class TestPrinterContextManager:
    """Tests for context manager support."""

    def setup_method(self):
        """Set up session prefix."""
        self.session_prefix = bytearray(8)
        struct.pack_into(">H", self.session_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.session_prefix, 2, -1, -1)
        struct.pack_into(">H", self.session_prefix, 5, 0)

    def test_enter_connects(self):
        """__enter__ should connect to printer."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)

        with printer:
            assert printer.is_connected

    def test_exit_disconnects(self):
        """__exit__ should disconnect from printer."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)

        with printer:
            pass

        assert not printer.is_connected

    def test_exit_disconnects_on_exception(self):
        """__exit__ should disconnect even on exception."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)

        try:
            with printer:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert not printer.is_connected

    def test_returns_printer_from_enter(self):
        """__enter__ should return the printer instance."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)

        with printer as p:
            assert p is printer
