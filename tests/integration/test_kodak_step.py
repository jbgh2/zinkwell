"""Integration tests for Kodak Step printer.

Tests the full flow of printer operations using MockTransport
to simulate printer responses.
"""

import pytest

from tests.mocks import MockTransport
from zinkwell.devices.kodak_step import KodakStepPrinter
from zinkwell.devices.kodak_step.protocol import (
    PACKET_SIZE,
    HEADER,
    CMD_GET_ACCESSORY_INFO,
    CMD_GET_BATTERY_LEVEL,
    CMD_GET_PAGE_TYPE,
    CMD_GET_AUTO_POWER_OFF,
    CMD_GET_PRINT_COUNT,
    CMD_PRINT_READY,
    FLAG_STANDARD_DEVICE,
    FLAG_SLIM_DEVICE,
    ERR_SUCCESS,
    ERR_NO_PAPER,
    ERR_COVER_OPEN,
)
from zinkwell.exceptions import (
    LowBatteryError,
    CoverOpenError,
    NoPaperError,
)


def build_response(error_code: int = ERR_SUCCESS, battery: int = 80) -> bytes:
    """Build a 34-byte response message."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[8] = error_code
    data[12] = battery  # Battery level for GET_ACCESSORY_INFO
    return bytes(data)


def build_accessory_info_response(battery: int = 80) -> bytes:
    """Build an accessory info response with battery level."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[6] = CMD_GET_ACCESSORY_INFO
    data[8] = ERR_SUCCESS
    data[12] = battery
    return bytes(data)


def build_battery_level_response(is_charging: bool = False) -> bytes:
    """Build a battery level (charging status) response."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[6] = CMD_GET_BATTERY_LEVEL
    data[8] = 1 if is_charging else 0
    return bytes(data)


def build_page_type_response(error_code: int = ERR_SUCCESS) -> bytes:
    """Build a page type response."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[6] = CMD_GET_PAGE_TYPE
    data[8] = error_code
    return bytes(data)


def build_print_ready_response(error_code: int = ERR_SUCCESS) -> bytes:
    """Build a print ready response."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[6] = CMD_PRINT_READY
    data[8] = error_code
    return bytes(data)


def build_auto_power_off_response(minutes: int = 5) -> bytes:
    """Build an auto power off response."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[6] = CMD_GET_AUTO_POWER_OFF
    data[8] = minutes
    return bytes(data)


def build_print_count_response(count: int = 100) -> bytes:
    """Build a print count response."""
    data = bytearray(PACKET_SIZE)
    data[0:4] = HEADER
    data[6] = CMD_PRINT_READY
    data[7] = 0x01  # Flag for print count
    data[8] = (count >> 8) & 0xFF
    data[9] = count & 0xFF
    return bytes(data)


def get_accessory_info_prefix(is_slim: bool = False) -> bytes:
    """Get the 8-byte prefix for GET_ACCESSORY_INFO command."""
    prefix = bytearray(8)
    prefix[0:4] = HEADER
    prefix[4] = 0x00
    prefix[5] = FLAG_SLIM_DEVICE if is_slim else FLAG_STANDARD_DEVICE
    prefix[6] = CMD_GET_ACCESSORY_INFO
    prefix[7] = 0x00
    return bytes(prefix)


def get_battery_level_prefix() -> bytes:
    """Get the 8-byte prefix for GET_BATTERY_LEVEL command."""
    prefix = bytearray(8)
    prefix[0:4] = HEADER
    prefix[4] = 0x00
    prefix[5] = 0x00
    prefix[6] = CMD_GET_BATTERY_LEVEL
    prefix[7] = 0x00
    return bytes(prefix)


def get_page_type_prefix() -> bytes:
    """Get the 8-byte prefix for GET_PAGE_TYPE command."""
    prefix = bytearray(8)
    prefix[0:4] = HEADER
    prefix[4] = 0x00
    prefix[5] = 0x00
    prefix[6] = CMD_GET_PAGE_TYPE
    prefix[7] = 0x00
    return bytes(prefix)


def get_auto_power_off_prefix() -> bytes:
    """Get the 8-byte prefix for GET_AUTO_POWER_OFF command."""
    prefix = bytearray(8)
    prefix[0:4] = HEADER
    prefix[4] = 0x00
    prefix[5] = 0x00
    prefix[6] = CMD_GET_AUTO_POWER_OFF
    prefix[7] = 0x00
    return bytes(prefix)


def get_print_count_prefix() -> bytes:
    """Get the 8-byte prefix for GET_PRINT_COUNT command."""
    prefix = bytearray(8)
    prefix[0:4] = HEADER
    prefix[4] = 0x00
    prefix[5] = 0x00
    prefix[6] = CMD_PRINT_READY
    prefix[7] = 0x01  # Flag that distinguishes from PRINT_READY
    return bytes(prefix)


class TestKodakStepConnection:
    """Tests for connection flow."""

    def test_connect_establishes_session(self):
        """Connect should establish session and get battery."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=75),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        assert printer.is_connected
        assert len(mock.sent_commands) == 1
        printer.disconnect()

    def test_connect_slim_device(self):
        """Connect should use slim variant for Step Slim."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(is_slim=True): build_accessory_info_response(battery=75),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock, is_slim=True)
        printer.connect()

        assert printer.is_connected
        # Verify slim flag was used
        sent_cmd = mock.sent_commands[0]
        assert sent_cmd[5] == FLAG_SLIM_DEVICE
        printer.disconnect()

    def test_disconnect_cleans_up(self):
        """Disconnect should clean up client."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        assert printer.is_connected

        printer.disconnect()
        assert not printer.is_connected


class TestKodakStepStatus:
    """Tests for get_status flow."""

    def test_get_status_returns_battery(self):
        """get_status should return battery level."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=65),
            get_battery_level_prefix(): build_battery_level_response(is_charging=False),
            get_page_type_prefix(): build_page_type_response(ERR_SUCCESS),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        mock.clear()

        status = printer.get_status()

        assert status.battery_level == 65
        assert status.is_ready
        printer.disconnect()

    def test_get_status_charging(self):
        """get_status should detect charging status."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=50),
            get_battery_level_prefix(): build_battery_level_response(is_charging=True),
            get_page_type_prefix(): build_page_type_response(ERR_SUCCESS),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        mock.clear()

        status = printer.get_status()

        assert status.is_charging is True
        printer.disconnect()

    def test_get_status_cover_open(self):
        """get_status should detect cover open."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=80),
            get_battery_level_prefix(): build_battery_level_response(),
            get_page_type_prefix(): build_page_type_response(ERR_COVER_OPEN),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        mock.clear()

        status = printer.get_status()

        assert status.is_cover_open
        assert not status.is_ready
        assert status.error == "Cover is open"
        printer.disconnect()

    def test_get_status_no_paper(self):
        """get_status should detect no paper."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=80),
            get_battery_level_prefix(): build_battery_level_response(),
            get_page_type_prefix(): build_page_type_response(ERR_NO_PAPER),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        mock.clear()

        status = printer.get_status()

        assert not status.is_ready
        assert status.error == "No paper"
        printer.disconnect()


class TestKodakStepPrintChecks:
    """Tests for pre-print validation."""

    def test_print_rejects_cover_open(self, tmp_path):
        """Print should raise CoverOpenError if cover is open."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=80),
            get_battery_level_prefix(): build_battery_level_response(),
            get_page_type_prefix(): build_page_type_response(ERR_COVER_OPEN),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(CoverOpenError):
            printer.print(str(img_path))

        printer.disconnect()

    def test_print_rejects_no_paper(self, tmp_path):
        """Print should raise NoPaperError if no paper."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=80),
            get_battery_level_prefix(): build_battery_level_response(),
            get_page_type_prefix(): build_page_type_response(ERR_NO_PAPER),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(NoPaperError):
            printer.print(str(img_path))

        printer.disconnect()

    def test_print_rejects_low_battery(self, tmp_path):
        """Print should raise LowBatteryError if battery below 30%."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(battery=20),
            get_battery_level_prefix(): build_battery_level_response(),
            get_page_type_prefix(): build_page_type_response(ERR_SUCCESS),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(LowBatteryError):
            printer.print(str(img_path))

        printer.disconnect()


class TestKodakStepSettings:
    """Tests for settings flow."""

    def test_get_settings_returns_values(self):
        """get_settings should return auto power off and print count."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(),
            get_auto_power_off_prefix(): build_auto_power_off_response(minutes=10),
            get_print_count_prefix(): build_print_count_response(count=250),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        mock.clear()

        settings = printer.get_settings()

        assert settings["auto_power_off"] == 10
        assert settings["print_count"] == 250
        printer.disconnect()


class TestKodakStepInfo:
    """Tests for printer info."""

    def test_info_standard_device(self):
        """Info should show standard device name."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock, is_slim=False)
        printer.connect()

        info = printer.info

        assert info.name == "Kodak Step"
        assert info.model == "kodak_step"
        printer.disconnect()

    def test_info_slim_device(self):
        """Info should show slim device name."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(is_slim=True): build_accessory_info_response(),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock, is_slim=True)
        printer.connect()

        info = printer.info

        assert info.name == "Kodak Step Slim"
        printer.disconnect()


class TestKodakStepCapabilities:
    """Tests for printer capabilities."""

    def test_capabilities_property(self):
        """Printer should expose capabilities."""
        mock = MockTransport(responses={
            get_accessory_info_prefix(): build_accessory_info_response(),
        })

        printer = KodakStepPrinter("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        caps = printer.capabilities

        assert caps.can_get_status is True
        assert caps.can_get_battery is True
        assert caps.can_configure_settings is True
        assert caps.can_reboot is False
        assert caps.supports_multiple_copies is True
        assert caps.min_battery_for_print == 30
        printer.disconnect()
