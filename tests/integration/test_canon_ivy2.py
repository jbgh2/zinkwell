"""Integration tests for Canon Ivy 2 printer.

Tests the full flow of printer operations using MockTransport
to simulate printer responses.
"""

import pytest
import struct

from tests.mocks import MockTransport
from zinkwell.devices.canon_ivy2 import CanonIvy2Printer
from zinkwell.devices.canon_ivy2.protocol import (
    START_CODE,
    PACKET_SIZE,
    ACK_START_SESSION,
    ACK_GET_STATUS,
    ACK_SETTING_ACCESSORY,
    ACK_PRINT_READY,
)
from zinkwell.exceptions import (
    LowBatteryError,
    CoverOpenError,
    NoPaperError,
    ProtocolError,
)


def build_response(ack: int, error: int = 0, payload: bytes = b"") -> bytes:
    """Build a 34-byte response message."""
    data = bytearray(PACKET_SIZE)
    # ACK at bytes 5-6 (big endian)
    data[5] = (ack >> 8) & 0xFF
    data[6] = ack & 0xFF
    # Error at byte 7
    data[7] = error
    # Payload starting at byte 8
    if payload:
        data[8:8 + len(payload)] = payload[:PACKET_SIZE - 8]
    return bytes(data)


def build_session_response(battery: int = 80, mtu: int = 512) -> bytes:
    """Build a session start response with battery and MTU."""
    data = bytearray(PACKET_SIZE)
    data[5] = 0  # ACK high
    data[6] = 0  # ACK low = 0 (ACK_START_SESSION)
    data[9] = 0
    data[10] = battery  # Battery in lower bits
    data[11] = (mtu >> 8) & 0xFF  # MTU high
    data[12] = mtu & 0xFF  # MTU low
    return bytes(data)


def build_status_response(
    battery: int = 80,
    error_code: int = 0,
    cover_open: bool = False,
    no_paper: bool = False,
    wrong_sheet: bool = False,
) -> bytes:
    """Build a status response."""
    payload = bytearray(10)
    # Battery encoded in first 2 bytes
    payload[0] = 0
    payload[1] = battery
    payload[2] = error_code

    # Flags in bytes 4-5
    flags = 0
    if cover_open:
        flags |= 0x01
    if no_paper:
        flags |= 0x02
    if wrong_sheet:
        flags |= 0x10
    payload[4] = 0
    payload[5] = flags

    return build_response(ACK_GET_STATUS, payload=bytes(payload))


def build_settings_response(
    auto_off: int = 5,
    firmware: tuple = (1, 0, 0),
    photos: int = 42,
) -> bytes:
    """Build a settings response."""
    payload = bytearray(10)
    payload[0] = auto_off
    payload[1] = firmware[0]
    payload[2] = firmware[1]
    payload[3] = firmware[2]
    payload[5] = 1  # TMD version
    payload[6] = (photos >> 8) & 0xFF
    payload[7] = photos & 0xFF
    payload[8] = 0  # Color ID

    return build_response(ACK_SETTING_ACCESSORY, payload=bytes(payload))


def build_print_ready_response() -> bytes:
    """Build a print ready response."""
    payload = bytearray(10)
    payload[2] = 0  # Unknown
    payload[3] = 0  # Error code
    return build_response(ACK_PRINT_READY, payload=bytes(payload))


def get_command_prefix(command: int) -> bytes:
    """Get the 8-byte prefix for a command message."""
    msg = bytearray(8)
    struct.pack_into(">H", msg, 0, START_CODE)
    struct.pack_into(">hb", msg, 2, 1, 32)  # Default flags
    struct.pack_into(">H", msg, 5, command)
    return bytes(msg)


class TestCanonIvy2Connection:
    """Tests for connection flow."""

    def test_connect_establishes_session(self):
        """Connect should establish session and get battery/MTU."""
        # Session init uses flag_1=True which sets different header
        session_prefix = bytearray(8)
        struct.pack_into(">H", session_prefix, 0, START_CODE)
        struct.pack_into(">hb", session_prefix, 2, -1, -1)  # flag_1=True
        struct.pack_into(">H", session_prefix, 5, 0)  # COMMAND_START_SESSION

        mock = MockTransport(responses={
            bytes(session_prefix): build_session_response(battery=75, mtu=1024),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        assert printer.is_connected
        assert len(mock.sent_commands) == 1
        printer.disconnect()

    def test_disconnect_cleans_up(self):
        """Disconnect should clean up client."""
        session_prefix = bytearray(8)
        struct.pack_into(">H", session_prefix, 0, START_CODE)
        struct.pack_into(">hb", session_prefix, 2, -1, -1)
        struct.pack_into(">H", session_prefix, 5, 0)

        mock = MockTransport(responses={
            bytes(session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()
        assert printer.is_connected

        printer.disconnect()
        assert not printer.is_connected


class TestCanonIvy2Status:
    """Tests for get_status flow."""

    def setup_method(self):
        """Set up printer with mock transport for status tests."""
        # Session prefix
        self.session_prefix = bytearray(8)
        struct.pack_into(">H", self.session_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.session_prefix, 2, -1, -1)
        struct.pack_into(">H", self.session_prefix, 5, 0)

        # Status prefix - command 257 = 0x0101
        self.status_prefix = bytearray(8)
        struct.pack_into(">H", self.status_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.status_prefix, 2, 1, 32)
        struct.pack_into(">H", self.status_prefix, 5, 257)

    def test_get_status_returns_battery(self):
        """get_status should return battery level."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(battery=50),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        status = printer.get_status()

        assert status.battery_level == 50  # parse_bit_range extracts 6 LSBs of 50 = 50
        assert status.is_ready  # No errors, battery >= 30%
        printer.disconnect()

    def test_get_status_cover_open(self):
        """get_status should detect cover open."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(cover_open=True),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        status = printer.get_status()

        assert status.is_cover_open
        assert not status.is_ready
        assert status.error == "Cover is open"
        printer.disconnect()

    def test_get_status_no_paper(self):
        """get_status should detect no paper."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(no_paper=True),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        status = printer.get_status()

        assert not status.is_ready
        assert status.error == "No paper"
        printer.disconnect()


class TestCanonIvy2PrintChecks:
    """Tests for pre-print validation."""

    def setup_method(self):
        """Set up command prefixes."""
        self.session_prefix = bytearray(8)
        struct.pack_into(">H", self.session_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.session_prefix, 2, -1, -1)
        struct.pack_into(">H", self.session_prefix, 5, 0)

        self.status_prefix = bytearray(8)
        struct.pack_into(">H", self.status_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.status_prefix, 2, 1, 32)
        struct.pack_into(">H", self.status_prefix, 5, 257)

    def test_print_rejects_cover_open(self, tmp_path):
        """Print should raise CoverOpenError if cover is open."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(cover_open=True),
        })

        # Create a test image
        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(CoverOpenError):
            printer.print(str(img_path))

        printer.disconnect()

    def test_print_rejects_no_paper(self, tmp_path):
        """Print should raise NoPaperError if no paper."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(no_paper=True),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(NoPaperError):
            printer.print(str(img_path))

        printer.disconnect()

    def test_print_rejects_low_battery(self, tmp_path):
        """Print should raise LowBatteryError if battery below 30%."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(battery=20),
            # Status response with battery < 30% encoded
            bytes(self.status_prefix): build_status_response(battery=20),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(LowBatteryError):
            printer.print(str(img_path))

        printer.disconnect()


class TestCanonIvy2Settings:
    """Tests for settings flow."""

    def setup_method(self):
        """Set up command prefixes."""
        self.session_prefix = bytearray(8)
        struct.pack_into(">H", self.session_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.session_prefix, 2, -1, -1)
        struct.pack_into(">H", self.session_prefix, 5, 0)

        # Settings prefix - command 259
        self.settings_prefix = bytearray(8)
        struct.pack_into(">H", self.settings_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.settings_prefix, 2, 1, 32)
        struct.pack_into(">H", self.settings_prefix, 5, 259)

    def test_get_settings_returns_firmware(self):
        """get_settings should return firmware version."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.settings_prefix): build_settings_response(
                auto_off=10, firmware=(2, 1, 5), photos=100
            ),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        settings = printer.get_settings()

        assert settings["firmware_version"] == "2.1.5"
        assert settings["auto_power_off"] == 10
        assert settings["photos_printed"] == 100
        printer.disconnect()

    def test_set_setting_auto_power_off(self):
        """set_setting should send auto_power_off value."""
        # Set setting uses flag_2=True which changes the header
        set_settings_prefix = bytearray(8)
        struct.pack_into(">H", set_settings_prefix, 0, START_CODE)
        struct.pack_into(">hb", set_settings_prefix, 2, 1, 32)
        struct.pack_into(">HB", set_settings_prefix, 5, 259, 1)  # flag_2=True adds 1

        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(set_settings_prefix): build_response(ACK_SETTING_ACCESSORY),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        printer.set_setting("auto_power_off", 5)

        # Verify command was sent
        assert len(mock.sent_commands) == 2  # session + set_setting
        printer.disconnect()

    def test_set_setting_invalid_key_raises(self):
        """set_setting with unknown key should raise ValueError."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(ValueError) as exc_info:
            printer.set_setting("unknown_setting", 5)

        assert "Unknown setting" in str(exc_info.value)
        printer.disconnect()

    def test_set_setting_invalid_value_raises(self):
        """set_setting with invalid value should raise ValueError."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(ValueError) as exc_info:
            printer.set_setting("auto_power_off", 7)  # Must be 3, 5, or 10

        assert "must be 3, 5, or 10" in str(exc_info.value)
        printer.disconnect()


class TestCanonIvy2ErrorHandling:
    """Tests for error handling paths."""

    def setup_method(self):
        """Set up command prefixes."""
        self.session_prefix = bytearray(8)
        struct.pack_into(">H", self.session_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.session_prefix, 2, -1, -1)
        struct.pack_into(">H", self.session_prefix, 5, 0)

        self.status_prefix = bytearray(8)
        struct.pack_into(">H", self.status_prefix, 0, START_CODE)
        struct.pack_into(">hb", self.status_prefix, 2, 1, 32)
        struct.pack_into(">H", self.status_prefix, 5, 257)

    def test_wrong_smart_sheet_error(self, tmp_path):
        """Print should raise PrintError for wrong smart sheet."""
        from zinkwell.exceptions import PrintError

        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(wrong_sheet=True),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(PrintError) as exc_info:
            printer.print(str(img_path))

        assert "Wrong smart sheet" in str(exc_info.value)
        printer.disconnect()

    def test_status_with_error_code(self):
        """get_status should report error codes."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(error_code=42),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        status = printer.get_status()

        assert status.error == "Error code: 42"
        assert not status.is_ready
        printer.disconnect()

    def test_protocol_error_wrong_ack(self):
        """Protocol error should be raised for unexpected ACK."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_response(ack=9999),  # Wrong ACK
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(ProtocolError) as exc_info:
            printer.get_status()

        assert "Unexpected ACK" in str(exc_info.value)
        printer.disconnect()

    def test_print_with_generic_error(self, tmp_path):
        """Print should raise PrintError for generic status errors."""
        from zinkwell.exceptions import PrintError

        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(self.status_prefix): build_status_response(error_code=99),
        })

        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), "red")
        img.save(img_path)

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        with pytest.raises(PrintError):
            printer.print(str(img_path))

        printer.disconnect()

    def test_info_includes_firmware_after_get_settings(self):
        """Printer info should include firmware version after get_settings."""
        settings_prefix = bytearray(8)
        struct.pack_into(">H", settings_prefix, 0, START_CODE)
        struct.pack_into(">hb", settings_prefix, 2, 1, 32)
        struct.pack_into(">H", settings_prefix, 5, 259)

        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
            bytes(settings_prefix): build_settings_response(firmware=(3, 2, 1)),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        # Before get_settings, firmware is None
        assert printer.info.firmware_version is None

        printer.get_settings()

        # After get_settings, firmware is populated
        assert printer.info.firmware_version == "3.2.1"
        printer.disconnect()

    def test_capabilities_property(self):
        """Printer should expose capabilities."""
        mock = MockTransport(responses={
            bytes(self.session_prefix): build_session_response(),
        })

        printer = CanonIvy2Printer("AA:BB:CC:DD:EE:FF", transport=mock)
        printer.connect()

        caps = printer.capabilities

        assert caps.can_get_status is True
        assert caps.can_reboot is True
        assert caps.min_battery_for_print == 30
        printer.disconnect()
