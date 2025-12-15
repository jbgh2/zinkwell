"""Unit tests for factory functions."""

import pytest

from zinkwell import get_printer, list_supported_printers
from zinkwell.devices.canon_ivy2 import CanonIvy2Printer


class TestGetPrinter:
    """Tests for get_printer factory function."""

    def test_creates_canon_ivy2_printer(self):
        """get_printer should create CanonIvy2Printer for 'canon_ivy2'."""
        printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")

        assert isinstance(printer, CanonIvy2Printer)

    def test_passes_address_and_port(self):
        """get_printer should pass address and port to printer."""
        printer = get_printer("canon_ivy2", "11:22:33:44:55:66", port=3)

        assert printer._address == "11:22:33:44:55:66"
        assert printer._port == 3

    def test_unknown_device_raises_value_error(self):
        """get_printer should raise ValueError for unknown device type."""
        with pytest.raises(ValueError) as exc_info:
            get_printer("unknown_printer", "AA:BB:CC:DD:EE:FF")

        assert "Unknown device type" in str(exc_info.value)
        assert "unknown_printer" in str(exc_info.value)
        assert "canon_ivy2" in str(exc_info.value)  # Shows available options

    def test_passes_transport_type(self):
        """get_printer should pass transport type to printer."""
        printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF", transport="native")

        assert printer._transport_type == "native"


class TestListSupportedPrinters:
    """Tests for list_supported_printers function."""

    def test_returns_dict(self):
        """list_supported_printers should return a dictionary."""
        result = list_supported_printers()

        assert isinstance(result, dict)

    def test_includes_canon_ivy2(self):
        """list_supported_printers should include canon_ivy2."""
        result = list_supported_printers()

        assert "canon_ivy2" in result

    def test_returns_printer_info(self):
        """list_supported_printers should return PrinterInfo objects."""
        result = list_supported_printers()

        info = result["canon_ivy2"]
        assert info.name == "Canon Ivy 2"
        assert info.model == "canon_ivy2"
        assert info.print_width == 640
        assert info.print_height == 1616
