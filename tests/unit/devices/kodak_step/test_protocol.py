"""Unit tests for Kodak Step protocol."""

import pytest

from zinkwell.devices.kodak_step.protocol import (
    PACKET_SIZE,
    CHUNK_SIZE,
    HEADER,
    CMD_GET_ACCESSORY_INFO,
    CMD_GET_BATTERY_LEVEL,
    CMD_GET_PAGE_TYPE,
    CMD_GET_PRINT_COUNT,
    CMD_GET_AUTO_POWER_OFF,
    CMD_PRINT_READY,
    FLAG_STANDARD_DEVICE,
    FLAG_SLIM_DEVICE,
    ERR_SUCCESS,
    ERR_NO_PAPER,
    ERR_COVER_OPEN,
    get_error_message,
    build_packet,
    parse_response,
    validate_response,
    ParsedResponse,
    GetAccessoryInfoTask,
    GetBatteryLevelTask,
    GetPageTypeTask,
    GetPrintCountTask,
    GetAutoPowerOffTask,
    PrintReadyTask,
)


class TestConstants:
    """Tests for protocol constants."""

    def test_packet_size(self):
        assert PACKET_SIZE == 34

    def test_chunk_size(self):
        assert CHUNK_SIZE == 4096

    def test_header_bytes(self):
        assert HEADER == bytes([0x1B, 0x2A, 0x43, 0x41])


class TestBuildPacket:
    """Tests for build_packet function."""

    def test_packet_size(self):
        packet = build_packet(CMD_GET_ACCESSORY_INFO)
        assert len(packet) == PACKET_SIZE

    def test_header(self):
        packet = build_packet(CMD_GET_ACCESSORY_INFO)
        assert packet[0:4] == HEADER

    def test_command_position(self):
        packet = build_packet(CMD_GET_ACCESSORY_INFO)
        assert packet[6] == CMD_GET_ACCESSORY_INFO

    def test_flags(self):
        packet = build_packet(CMD_GET_ACCESSORY_INFO, flags1=0x01, flags2=0x02, flags3=0x03)
        assert packet[4] == 0x01
        assert packet[5] == 0x02
        assert packet[7] == 0x03

    def test_remaining_bytes_zero(self):
        packet = build_packet(CMD_GET_ACCESSORY_INFO)
        assert all(b == 0 for b in packet[8:])


class TestParseResponse:
    """Tests for parse_response function."""

    def test_parse_valid_response(self):
        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[6] = CMD_GET_ACCESSORY_INFO
        data[7] = 0x00
        data[8] = ERR_SUCCESS
        data[9:] = b"payload_data_here________"  # 25 bytes

        response = parse_response(bytes(data))

        assert isinstance(response, ParsedResponse)
        assert response.command == CMD_GET_ACCESSORY_INFO
        assert response.sub_type == 0x00
        assert response.error_code == ERR_SUCCESS
        assert len(response.payload) == 25

    def test_parse_error_response(self):
        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_NO_PAPER

        response = parse_response(bytes(data))

        assert response.error_code == ERR_NO_PAPER

    def test_parse_invalid_header(self):
        data = bytearray(PACKET_SIZE)
        data[0:4] = b"\x00\x00\x00\x00"

        with pytest.raises(ValueError, match="Invalid header"):
            parse_response(bytes(data))

    def test_parse_short_response(self):
        data = b"\x1B\x2A\x43\x41"  # Only header, too short

        with pytest.raises(ValueError, match="too short"):
            parse_response(data)


class TestValidateResponse:
    """Tests for validate_response function."""

    def test_valid_response(self):
        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_SUCCESS

        is_valid, error_code = validate_response(bytes(data))

        assert is_valid
        assert error_code == ERR_SUCCESS

    def test_invalid_header(self):
        data = bytearray(PACKET_SIZE)
        data[0:4] = b"\x00\x00\x00\x00"

        is_valid, error_code = validate_response(bytes(data))

        assert not is_valid

    def test_short_response(self):
        data = b"\x1B\x2A"

        is_valid, error_code = validate_response(data)

        assert not is_valid


class TestGetErrorMessage:
    """Tests for get_error_message function."""

    def test_success(self):
        assert get_error_message(ERR_SUCCESS) is None

    def test_known_errors(self):
        assert get_error_message(ERR_NO_PAPER) == "No paper"
        assert get_error_message(ERR_COVER_OPEN) == "Cover open"

    def test_unknown_error(self):
        msg = get_error_message(0x99)
        assert "Unknown error" in msg


class TestGetAccessoryInfoTask:
    """Tests for GetAccessoryInfoTask."""

    def test_command(self):
        task = GetAccessoryInfoTask()
        assert task.command == CMD_GET_ACCESSORY_INFO

    def test_message_standard_device(self):
        task = GetAccessoryInfoTask(is_slim=False)
        msg = task.get_message()

        assert len(msg) == PACKET_SIZE
        assert msg[0:4] == HEADER
        assert msg[5] == FLAG_STANDARD_DEVICE
        assert msg[6] == CMD_GET_ACCESSORY_INFO

    def test_message_slim_device(self):
        task = GetAccessoryInfoTask(is_slim=True)
        msg = task.get_message()

        assert msg[5] == FLAG_SLIM_DEVICE

    def test_process_response(self):
        task = GetAccessoryInfoTask()

        # Build mock response with battery=75 at byte 12
        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_SUCCESS
        data[12] = 75  # Battery level

        response = parse_response(bytes(data))
        battery, is_charging = task.process_response(response)

        assert battery == 75


class TestGetBatteryLevelTask:
    """Tests for GetBatteryLevelTask (charging status)."""

    def test_command(self):
        task = GetBatteryLevelTask()
        assert task.command == CMD_GET_BATTERY_LEVEL

    def test_message_format(self):
        task = GetBatteryLevelTask()
        msg = task.get_message()

        assert len(msg) == PACKET_SIZE
        assert msg[6] == CMD_GET_BATTERY_LEVEL

    def test_process_response_charging(self):
        task = GetBatteryLevelTask()

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = 1  # Charging

        response = parse_response(bytes(data))
        is_charging = task.process_response(response)

        assert is_charging is True

    def test_process_response_not_charging(self):
        task = GetBatteryLevelTask()

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = 0  # Not charging

        response = parse_response(bytes(data))
        is_charging = task.process_response(response)

        assert is_charging is False


class TestGetPageTypeTask:
    """Tests for GetPageTypeTask."""

    def test_command(self):
        task = GetPageTypeTask()
        assert task.command == CMD_GET_PAGE_TYPE

    def test_message_format(self):
        task = GetPageTypeTask()
        msg = task.get_message()

        assert len(msg) == PACKET_SIZE
        assert msg[6] == CMD_GET_PAGE_TYPE

    def test_process_response_success(self):
        task = GetPageTypeTask()

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_SUCCESS

        response = parse_response(bytes(data))
        error_code = task.process_response(response)

        assert error_code == ERR_SUCCESS

    def test_process_response_no_paper(self):
        task = GetPageTypeTask()

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_NO_PAPER

        response = parse_response(bytes(data))
        error_code = task.process_response(response)

        assert error_code == ERR_NO_PAPER


class TestGetPrintCountTask:
    """Tests for GetPrintCountTask."""

    def test_command(self):
        task = GetPrintCountTask()
        assert task.command == CMD_PRINT_READY  # Same as PRINT_READY

    def test_message_format(self):
        task = GetPrintCountTask()
        msg = task.get_message()

        assert len(msg) == PACKET_SIZE
        assert msg[6] == CMD_PRINT_READY
        assert msg[7] == 0x01  # Distinguishing flag

    def test_process_response(self):
        task = GetPrintCountTask()

        # Print count = 1234 = 0x04D2
        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = 0x04
        data[9] = 0xD2

        response = parse_response(bytes(data))
        count = task.process_response(response)

        assert count == 1234


class TestGetAutoPowerOffTask:
    """Tests for GetAutoPowerOffTask."""

    def test_command(self):
        task = GetAutoPowerOffTask()
        assert task.command == CMD_GET_AUTO_POWER_OFF

    def test_message_format(self):
        task = GetAutoPowerOffTask()
        msg = task.get_message()

        assert len(msg) == PACKET_SIZE
        assert msg[6] == CMD_GET_AUTO_POWER_OFF

    def test_process_response(self):
        task = GetAutoPowerOffTask()

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = 10  # 10 minutes

        response = parse_response(bytes(data))
        minutes = task.process_response(response)

        assert minutes == 10


class TestPrintReadyTask:
    """Tests for PrintReadyTask."""

    def test_command(self):
        task = PrintReadyTask(image_size=1000)
        assert task.command == CMD_PRINT_READY

    def test_message_contains_size(self):
        # 50000 bytes = 0x00C350
        task = PrintReadyTask(image_size=50000)
        msg = task.get_message()

        assert len(msg) == PACKET_SIZE
        assert msg[6] == CMD_PRINT_READY
        assert msg[7] == 0x00  # No flag (distinguishes from GET_PRINT_COUNT)
        # Image size - 3 bytes big-endian
        assert msg[8] == 0x00
        assert msg[9] == 0xC3
        assert msg[10] == 0x50

    def test_message_contains_copies(self):
        task = PrintReadyTask(image_size=1000, num_copies=3)
        msg = task.get_message()

        assert msg[11] == 3

    def test_default_copies(self):
        task = PrintReadyTask(image_size=1000)
        msg = task.get_message()

        assert msg[11] == 1

    def test_process_response_success(self):
        task = PrintReadyTask(image_size=1000)

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_SUCCESS

        response = parse_response(bytes(data))
        error_code = task.process_response(response)

        assert error_code == ERR_SUCCESS

    def test_process_response_error(self):
        task = PrintReadyTask(image_size=1000)

        data = bytearray(PACKET_SIZE)
        data[0:4] = HEADER
        data[8] = ERR_NO_PAPER

        response = parse_response(bytes(data))
        error_code = task.process_response(response)

        assert error_code == ERR_NO_PAPER
