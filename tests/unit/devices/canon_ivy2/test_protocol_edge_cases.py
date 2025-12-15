"""Edge case tests for Canon Ivy 2 protocol."""

import pytest

from zinkwell.devices.canon_ivy2.protocol import (
    parse_bit_range,
    GetPrintReadyTask,
    ACK_PRINT_READY,
    ParsedMessage,
)


class TestParseBitRangeEdgeCases:
    """Edge case tests for parse_bit_range."""

    def test_empty_string_returns_zero(self):
        """parse_bit_range should handle edge case where bits is empty."""
        # When size is 0, the bits string is empty
        result = parse_bit_range(255, 0)
        assert result == 0

    def test_large_value(self):
        """parse_bit_range should work with larger values."""
        # 8 bits = max 255
        result = parse_bit_range(0b11111111, 8)
        assert result == 255


class TestGetPrintReadyTaskResponse:
    """Tests for GetPrintReadyTask response parsing."""

    def test_process_response_extracts_fields(self):
        """process_response should extract unknown and error_code."""
        task = GetPrintReadyTask(length=1000)

        payload = bytearray(10)
        payload[2] = 42  # Unknown field
        payload[3] = 5   # Error code

        response = ParsedMessage(
            raw_data=b"x" * 34,
            payload=bytes(payload),
            ack=ACK_PRINT_READY,
            error=0,
        )

        unknown, error_code = task.process_response(response)

        assert unknown == 42
        assert error_code == 5

    def test_flag_parameter_affects_message(self):
        """GetPrintReadyTask flag should affect message format."""
        task_no_flag = GetPrintReadyTask(length=100, flag=False)
        task_with_flag = GetPrintReadyTask(length=100, flag=True)

        msg_no_flag = task_no_flag.get_message()
        msg_with_flag = task_with_flag.get_message()

        # The messages should differ at byte 13 (b5 position)
        assert msg_no_flag[13] == 1  # flag=False -> b5=1
        assert msg_with_flag[13] == 2  # flag=True -> b5=2
