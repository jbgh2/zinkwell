"""Unit tests for Canon Ivy 2 protocol."""

import pytest

from zinkwell.devices.canon_ivy2.protocol import (
    parse_bit_range,
    parse_message,
    build_base_message,
    ParsedMessage,
    StartSessionTask,
    GetStatusTask,
    GetSettingTask,
    SetSettingTask,
    GetPrintReadyTask,
    RebootTask,
    START_CODE,
    PACKET_SIZE,
    COMMAND_START_SESSION,
    COMMAND_GET_STATUS,
    ACK_GET_STATUS,
)


class TestParseBitRange:
    """Tests for parse_bit_range function."""

    @pytest.mark.parametrize("value,size,expected", [
        (0, 6, 0),              # Zero
        (0b111111, 6, 63),      # Max 6 bits
        (0b101010, 6, 42),      # Partial pattern
        (85, 6, 21),            # Battery level (6 LSBs of 85)
        (255, 0, 0),            # Size 0 returns 0
        (0b11111111, 8, 255),   # 8 bits
    ])
    def test_extracts_correct_bits(self, value, size, expected):
        """parse_bit_range should extract the correct LSBs."""
        assert parse_bit_range(value, size) == expected


class TestParseMessage:
    """Tests for parse_message function."""

    def test_parse_basic_message(self):
        # Build a 34-byte message with known values
        data = bytearray(34)
        data[5] = 0x01  # ACK high byte
        data[6] = 0x01  # ACK low byte = 257
        data[7] = 0x00  # Error = 0
        data[8:] = b"payload_data_here___"  # Payload

        result = parse_message(bytes(data))

        assert isinstance(result, ParsedMessage)
        assert result.ack == 257
        assert result.error == 0
        assert result.payload == b"payload_data_here___"

    def test_parse_message_with_error(self):
        data = bytearray(34)
        data[7] = 0x05  # Error code 5

        result = parse_message(bytes(data))

        assert result.error == 5


class TestBuildBaseMessage:
    """Tests for build_base_message function."""

    def test_message_size(self):
        msg = build_base_message(COMMAND_GET_STATUS)
        assert len(msg) == PACKET_SIZE

    def test_start_code(self):
        msg = build_base_message(COMMAND_GET_STATUS)
        # START_CODE is 17167 = 0x430F
        assert msg[0] == 0x43
        assert msg[1] == 0x0F

    def test_command_in_header(self):
        msg = build_base_message(COMMAND_GET_STATUS)  # 257 = 0x0101
        # Command is at bytes 5-6 (big endian) per struct format ">HhbHB"
        assert msg[5] == 0x01
        assert msg[6] == 0x01

    def test_session_init_flags(self):
        msg = build_base_message(COMMAND_START_SESSION, flag_1=True)
        # flag_1=True sets b1=-1, b2=-1
        # Signed -1 as bytes
        assert msg[2:4] == b'\xff\xff'


class TestStartSessionTask:
    """Tests for StartSessionTask."""

    def test_ack_value(self):
        task = StartSessionTask()
        assert task.ack == 0

    def test_message_format(self):
        task = StartSessionTask()
        msg = task.get_message()

        assert len(msg) == 34
        assert msg[0:2] == bytes([0x43, 0x0F])  # START_CODE

    def test_process_response(self):
        task = StartSessionTask()

        # Build mock response with battery=50, MTU=512
        data = bytearray(34)
        data[9] = 0x00
        data[10] = 50  # Battery in lower bits
        data[11] = 0x02  # MTU high byte
        data[12] = 0x00  # MTU low byte = 512

        response = ParsedMessage(raw_data=bytes(data), payload=b"", ack=0, error=0)
        battery, mtu = task.process_response(response)

        assert mtu == 512


class TestGetStatusTask:
    """Tests for GetStatusTask."""

    def test_ack_value(self):
        task = GetStatusTask()
        assert task.ack == ACK_GET_STATUS

    def test_process_response_no_errors(self):
        task = GetStatusTask()

        # Build payload with no errors, 80% battery
        payload = bytearray(10)
        payload[0] = 0x00
        payload[1] = 80  # Battery encoded
        payload[2] = 0  # Error code
        payload[4] = 0x00
        payload[5] = 0x00  # No flags

        response = ParsedMessage(
            raw_data=b"x" * 34,
            payload=bytes(payload),
            ack=ACK_GET_STATUS,
            error=0,
        )

        error_code, battery, usb, cover_open, no_paper, wrong_sheet = task.process_response(
            response
        )

        assert error_code == 0
        assert not cover_open
        assert not no_paper
        assert not wrong_sheet

    def test_process_response_cover_open(self):
        task = GetStatusTask()

        payload = bytearray(10)
        payload[4] = 0x00
        payload[5] = 0x01  # Cover open flag

        response = ParsedMessage(
            raw_data=b"x" * 34,
            payload=bytes(payload),
            ack=ACK_GET_STATUS,
            error=0,
        )

        _, _, _, cover_open, no_paper, _ = task.process_response(response)

        assert cover_open
        assert not no_paper

    def test_process_response_no_paper(self):
        task = GetStatusTask()

        payload = bytearray(10)
        payload[4] = 0x00
        payload[5] = 0x02  # No paper flag

        response = ParsedMessage(
            raw_data=b"x" * 34,
            payload=bytes(payload),
            ack=ACK_GET_STATUS,
            error=0,
        )

        _, _, _, cover_open, no_paper, _ = task.process_response(response)

        assert not cover_open
        assert no_paper


class TestGetSettingTask:
    """Tests for GetSettingTask."""

    def test_process_response(self):
        task = GetSettingTask()

        # Build payload with settings
        payload = bytearray(10)
        payload[0] = 5  # Auto power off = 5 minutes
        payload[1] = 1  # Firmware major
        payload[2] = 2  # Firmware minor
        payload[3] = 3  # Firmware patch
        payload[5] = 1  # TMD version
        payload[6] = 0x00
        payload[7] = 42  # Photos printed
        payload[8] = 1  # Color ID

        response = ParsedMessage(
            raw_data=b"x" * 34,
            payload=bytes(payload),
            ack=259,
            error=0,
        )

        auto_off, firmware, tmd, photos, color = task.process_response(response)

        assert auto_off == 5
        assert firmware == "1.2.3"
        assert tmd == 1
        assert photos == 42
        assert color == 1


class TestSetSettingTask:
    """Tests for SetSettingTask."""

    def test_message_contains_value(self):
        task = SetSettingTask(auto_power_off=10)
        msg = task.get_message()

        # Value should be at offset 8
        assert msg[8] == 10


class TestGetPrintReadyTask:
    """Tests for GetPrintReadyTask."""

    def test_message_contains_length(self):
        task = GetPrintReadyTask(length=12345)
        msg = task.get_message()

        # Length is packed as 4 bytes starting at offset 8
        # 12345 = 0x00003039
        assert msg[8] == 0x00
        assert msg[9] == 0x00
        assert msg[10] == 0x30
        assert msg[11] == 0x39

    def test_flag_affects_message(self):
        """Flag parameter should change byte 13."""
        task_false = GetPrintReadyTask(length=100, flag=False)
        task_true = GetPrintReadyTask(length=100, flag=True)

        assert task_false.get_message()[13] == 1
        assert task_true.get_message()[13] == 2

    def test_process_response(self):
        """process_response should extract error code."""
        task = GetPrintReadyTask(length=1000)

        payload = bytearray(10)
        payload[3] = 5  # Error code

        response = ParsedMessage(
            raw_data=b"x" * 34,
            payload=bytes(payload),
            ack=769,
            error=0,
        )

        _, error_code = task.process_response(response)
        assert error_code == 5


class TestRebootTask:
    """Tests for RebootTask."""

    def test_ack_value(self):
        task = RebootTask()
        assert task.ack == 65535

    def test_message_format(self):
        task = RebootTask()
        msg = task.get_message()

        assert len(msg) == 34
        assert msg[8] == 1  # Reboot flag
