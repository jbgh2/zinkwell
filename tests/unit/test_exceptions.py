"""Unit tests for exception classes."""

import pytest

from zinkwell.exceptions import (
    ZinkwellError,
    ConnectionError,
    PrintError,
    LowBatteryError,
    CoverOpenError,
    NoPaperError,
    PaperJamError,
    TransportError,
    ProtocolError,
    TimeoutError,
)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_all_inherit_from_zinkwell_error(self):
        """All custom exceptions should inherit from ZinkwellError."""
        exceptions = [
            ConnectionError, PrintError, TransportError,
            ProtocolError, TimeoutError, LowBatteryError,
            CoverOpenError, NoPaperError, PaperJamError,
        ]
        for exc in exceptions:
            assert issubclass(exc, ZinkwellError), f"{exc.__name__} should inherit from ZinkwellError"

    def test_print_errors_inherit_from_print_error(self):
        """Print-related errors should inherit from PrintError."""
        print_exceptions = [LowBatteryError, CoverOpenError, NoPaperError, PaperJamError]
        for exc in print_exceptions:
            assert issubclass(exc, PrintError), f"{exc.__name__} should inherit from PrintError"


class TestPrintError:
    """Tests for PrintError and subclasses."""

    def test_device_error_attribute(self):
        """PrintError should store device_error."""
        error = PrintError("Print failed", device_error="cover_open")
        assert error.device_error == "cover_open"

    def test_device_error_default_none(self):
        """PrintError device_error should default to None."""
        error = PrintError("Print failed")
        assert error.device_error is None

    @pytest.mark.parametrize("error_class,expected_device_error,expected_message_fragment", [
        (LowBatteryError, "low_battery", "battery"),
        (CoverOpenError, "cover_open", "cover"),
        (NoPaperError, "no_paper", "paper"),
        (PaperJamError, "paper_jam", "jam"),
    ])
    def test_print_error_subclass_defaults(self, error_class, expected_device_error, expected_message_fragment):
        """Print error subclasses should have correct defaults."""
        error = error_class()
        assert error.device_error == expected_device_error
        assert expected_message_fragment in str(error).lower()


class TestLowBatteryError:
    """Tests for LowBatteryError specific behavior."""

    def test_stores_battery_level(self):
        """LowBatteryError should store battery level."""
        error = LowBatteryError("Battery too low", level=15)
        assert error.level == 15


class TestProtocolError:
    """Tests for ProtocolError."""

    def test_stores_expected_and_got(self):
        """ProtocolError should store expected and got values for debugging."""
        error = ProtocolError("Wrong ACK", expected=257, got=999)
        assert error.expected == 257
        assert error.got == 999
