"""Unit tests for factory functions."""

import pytest

from zinkwell import get_printer, list_supported_printers
from zinkwell.devices.canon_ivy2 import CanonIvy2Printer


class TestGetPrinter:
    """Tests for get_printer factory function."""

    def test_creates_correct_printer_type(self):
        """get_printer should create the correct printer class."""
        printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
        assert isinstance(printer, CanonIvy2Printer)

    def test_unknown_device_raises_with_helpful_message(self):
        """get_printer should raise ValueError with available options."""
        with pytest.raises(ValueError) as exc_info:
            get_printer("unknown_printer", "AA:BB:CC:DD:EE:FF")

        error_msg = str(exc_info.value)
        assert "unknown_printer" in error_msg
        assert "canon_ivy2" in error_msg  # Shows available options


class TestListSupportedPrinters:
    """Tests for list_supported_printers function."""

    def test_returns_printer_info_for_registered_devices(self):
        """list_supported_printers should return PrinterInfo for each device."""
        result = list_supported_printers()

        assert "canon_ivy2" in result
        info = result["canon_ivy2"]
        assert info.name == "Canon Ivy 2"
        assert info.print_width == 640
        assert info.print_height == 1616
