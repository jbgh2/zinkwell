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
        assert issubclass(ConnectionError, ZinkwellError)
        assert issubclass(PrintError, ZinkwellError)
        assert issubclass(TransportError, ZinkwellError)
        assert issubclass(ProtocolError, ZinkwellError)
        assert issubclass(TimeoutError, ZinkwellError)

    def test_print_errors_inherit_from_print_error(self):
        """Print-related errors should inherit from PrintError."""
        assert issubclass(LowBatteryError, PrintError)
        assert issubclass(CoverOpenError, PrintError)
        assert issubclass(NoPaperError, PrintError)


class TestPrintError:
    """Tests for PrintError class."""

    def test_basic_message(self):
        """PrintError should store message."""
        error = PrintError("Something went wrong")

        assert str(error) == "Something went wrong"

    def test_device_error_attribute(self):
        """PrintError should store device_error."""
        error = PrintError("Print failed", device_error="cover_open")

        assert error.device_error == "cover_open"

    def test_device_error_default_none(self):
        """PrintError device_error should default to None."""
        error = PrintError("Print failed")

        assert error.device_error is None


class TestLowBatteryError:
    """Tests for LowBatteryError class."""

    def test_stores_battery_level(self):
        """LowBatteryError should store battery level."""
        error = LowBatteryError("Battery too low", level=15)

        assert error.level == 15

    def test_default_message(self):
        """LowBatteryError should have default message."""
        error = LowBatteryError()

        assert "Battery too low" in str(error)


class TestCoverOpenError:
    """Tests for CoverOpenError class."""

    def test_default_message(self):
        """CoverOpenError should have default message."""
        error = CoverOpenError()

        assert "cover is open" in str(error).lower()

    def test_device_error_attribute(self):
        """CoverOpenError should set device_error."""
        error = CoverOpenError()

        assert error.device_error == "cover_open"


class TestNoPaperError:
    """Tests for NoPaperError class."""

    def test_default_message(self):
        """NoPaperError should have default message."""
        error = NoPaperError()

        assert "No paper" in str(error)

    def test_device_error_attribute(self):
        """NoPaperError should set device_error."""
        error = NoPaperError()

        assert error.device_error == "no_paper"


class TestPaperJamError:
    """Tests for PaperJamError class."""

    def test_default_message(self):
        """PaperJamError should have default message."""
        error = PaperJamError()

        assert "jam" in str(error).lower()

    def test_device_error_attribute(self):
        """PaperJamError should set device_error."""
        error = PaperJamError()

        assert error.device_error == "paper_jam"


class TestProtocolError:
    """Tests for ProtocolError class."""

    def test_stores_expected_and_got(self):
        """ProtocolError should store expected and got values."""
        error = ProtocolError("Wrong ACK", expected=257, got=999)

        assert error.expected == 257
        assert error.got == 999


class TestTransportError:
    """Tests for TransportError class."""

    def test_basic_message(self):
        """TransportError should store message."""
        error = TransportError("Connection failed")

        assert "Connection failed" in str(error)


class TestTimeoutError:
    """Tests for TimeoutError class."""

    def test_basic_message(self):
        """TimeoutError should store message."""
        error = TimeoutError("No response within 5 seconds")

        assert "No response" in str(error)
