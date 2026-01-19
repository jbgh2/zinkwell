"""
Test script for Kodak Step printer prototype.

This script attempts to connect to the Kodak Step printer and perform basic operations
using the Canon Ivy 2 protocol as a starting point. The protocol may need adjustments.
"""

from kodak_step import KodakStepPrinter
from loguru import logger
import sys

# Kodak Step printer MAC address (discovered via Bluetooth enumeration)
PRINTER_MAC = "A4:62:DF:A9:72:D4"


def test_connection():
    """Test basic connection to the printer."""
    logger.info("=" * 60)
    logger.info("Test 1: Connection Test")
    logger.info("=" * 60)

    printer = KodakStepPrinter()

    try:
        logger.info(f"Connecting to Kodak Step printer at {PRINTER_MAC}...")
        printer.connect(PRINTER_MAC)
        logger.success("Connection successful!")
        return printer
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_status(printer):
    """Test getting printer status."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 2: Status Query")
    logger.info("=" * 60)

    try:
        status = printer.get_status()
        error_code, battery_level, usb_status, is_cover_open, is_no_paper, is_wrong_smart_sheet = status

        logger.info(f"Status retrieved successfully:")
        logger.info(f"  Error Code: {error_code}")
        logger.info(f"  Battery Level: {battery_level}%")
        logger.info(f"  USB Connected: {bool(usb_status)}")
        logger.info(f"  Cover Open: {is_cover_open}")
        logger.info(f"  No Paper: {is_no_paper}")
        logger.info(f"  Wrong Smart Sheet: {is_wrong_smart_sheet}")
        return True
    except Exception as e:
        logger.error(f"Status query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings(printer):
    """Test getting printer settings."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 3: Settings Query")
    logger.info("=" * 60)

    try:
        settings = printer.get_setting()
        auto_power_off, firmware_version, tmd_version, number_of_photos_printed, color_id = settings

        logger.info(f"Settings retrieved successfully:")
        logger.info(f"  Auto Power Off: {auto_power_off} minutes")
        logger.info(f"  Firmware Version: {firmware_version}")
        logger.info(f"  TMD Version: {tmd_version}")
        logger.info(f"  Photos Printed: {number_of_photos_printed}")
        logger.info(f"  Color ID: {color_id}")
        return True
    except Exception as e:
        logger.error(f"Settings query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_print(printer, image_path="./assets/test_image.jpg"):
    """Test printing an image."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 4: Print Test")
    logger.info("=" * 60)

    try:
        logger.info(f"Attempting to print: {image_path}")
        printer.print(image_path)
        logger.success("Print command completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Print failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    logger.info("Kodak Step Printer Prototype Test Suite")
    logger.info("Based on Canon Ivy 2 protocol specification")
    logger.info("")

    # Test 1: Connection
    printer = test_connection()
    if not printer:
        logger.error("Connection failed. Cannot proceed with further tests.")
        sys.exit(1)

    try:
        # Test 2: Status
        test_status(printer)

        # Test 3: Settings
        test_settings(printer)

        # Test 4: Print (only if user confirms)
        logger.info("")
        logger.info("=" * 60)
        user_input = input("Attempt to print test image? (y/n): ")
        if user_input.lower() == 'y':
            test_print(printer)
        else:
            logger.info("Skipping print test.")

    finally:
        # Always disconnect
        logger.info("")
        logger.info("=" * 60)
        logger.info("Disconnecting from printer...")
        printer.disconnect()
        logger.info("Test suite complete.")


if __name__ == '__main__':
    main()