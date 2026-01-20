"""Hardware tests requiring a real printer.

These tests are skipped in CI and require:
1. A real printer to be paired and available
2. TEST_PRINTER_ADDRESS environment variable set
3. TEST_PRINTER_TYPE environment variable set (e.g., "canon_ivy2")

Run with: pytest tests/hardware -v
"""

import os

import pytest

# Skip all tests in this module if no printer configured
PRINTER_ADDRESS = os.environ.get("TEST_PRINTER_ADDRESS")
PRINTER_TYPE = os.environ.get("TEST_PRINTER_TYPE", "canon_ivy2")

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not PRINTER_ADDRESS,
        reason="No TEST_PRINTER_ADDRESS environment variable set",
    ),
]


@pytest.fixture
def printer():
    """Get a connected printer instance."""
    from zinkwell import get_printer

    p = get_printer(PRINTER_TYPE, PRINTER_ADDRESS)
    p.connect()
    yield p
    p.disconnect()


class TestRealPrinter:
    """Tests that run against real hardware."""

    def test_connect_and_disconnect(self):
        """Can connect and disconnect from printer."""
        from zinkwell import get_printer

        printer = get_printer(PRINTER_TYPE, PRINTER_ADDRESS)
        printer.connect()
        assert printer.is_connected
        printer.disconnect()
        assert not printer.is_connected

    def test_get_status(self, printer):
        """Can get printer status."""
        status = printer.get_status()

        assert 0 <= status.battery_level <= 100
        assert isinstance(status.is_ready, bool)

    def test_get_info(self, printer):
        """Can get printer info."""
        info = printer.info

        assert info.name
        assert info.model
        assert info.print_width > 0
        assert info.print_height > 0

    # Uncomment to test actual printing (uses paper!)
    # def test_print_image(self, printer, test_image_path):
    #     """Can print an image."""
    #     printer.print(str(test_image_path))
