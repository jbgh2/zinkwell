"""
Protocol exploration script for Kodak Step printer.
Tries different protocol variations and listens for responses.
"""

import serial
import struct
import time
from loguru import logger

COM_PORT = "COM6"  # We know this is the working port


def try_canon_protocol():
    """Try the Canon Ivy 2 protocol."""
    logger.info("=" * 60)
    logger.info("Test 1: Canon Ivy 2 Protocol")
    logger.info("=" * 60)

    ser = serial.Serial(COM_PORT, 115200, timeout=2)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Canon Ivy 2 START_SESSION
    START_CODE = 17167  # 0x430F
    byte_array = bytearray(34)
    struct.pack_into(">HhbHB", byte_array, 0, START_CODE, -1, -1, 0, 0)

    logger.info(f"Sending: {byte_array.hex()}")
    ser.write(bytes(byte_array))
    ser.flush()

    time.sleep(1)

    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        logger.success(f"Got response: {response.hex()}")
        return response
    else:
        logger.warning("No response")

    ser.close()
    return None


def try_different_start_codes():
    """Try different start codes to see if Kodak uses something else."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 2: Alternative Start Codes")
    logger.info("=" * 60)

    # Common start codes to try
    start_codes = [
        (0x430F, "Canon Ivy 2"),
        (0x4B4F, "KO (Kodak)"),
        (0x5A4B, "ZK (Zink Kodak)"),
        (0xAAAA, "Common marker 1"),
        (0x5555, "Common marker 2"),
        (0xFF00, "Common marker 3"),
        (0x1234, "Test pattern"),
    ]

    for start_code, name in start_codes:
        logger.info(f"Trying 0x{start_code:04X} ({name})...")

        ser = serial.Serial(COM_PORT, 115200, timeout=1)
        ser.reset_input_buffer()

        byte_array = bytearray(34)
        struct.pack_into(">HhbHB", byte_array, 0, start_code, -1, -1, 0, 0)

        try:
            ser.write(bytes(byte_array))
            ser.flush()
            time.sleep(0.5)

            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                logger.success(f"  Response: {response.hex()}")
                ser.close()
                return response
            else:
                logger.debug("  No response")
        except Exception as e:
            logger.error(f"  Error: {e}")

        ser.close()

    return None


def try_simple_commands():
    """Try very simple commands to elicit any response."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 3: Simple Commands")
    logger.info("=" * 60)

    commands = [
        (b'\x00', "NULL byte"),
        (b'\x01', "SOH (Start of Header)"),
        (b'\x02', "STX (Start of Text)"),
        (b'\x05', "ENQ (Enquiry)"),
        (b'\x06', "ACK"),
        (b'\x10', "DLE (Data Link Escape)"),
        (b'AT\r\n', "AT command"),
        (b'HELLO', "HELLO string"),
        (b'\xFF\xFF\xFF\xFF', "All 1s"),
    ]

    for cmd, name in commands:
        logger.info(f"Sending: {name} ({cmd.hex()})...")

        ser = serial.Serial(COM_PORT, 115200, timeout=1)
        ser.reset_input_buffer()

        try:
            ser.write(cmd)
            ser.flush()
            time.sleep(0.3)

            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                logger.success(f"  Response: {response.hex()} (ASCII: {response})")
                ser.close()
                return response
        except Exception as e:
            logger.error(f"  Error: {e}")

        ser.close()

    return None


def just_listen():
    """Open the port and just listen for any unsolicited data."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 4: Passive Listening")
    logger.info("=" * 60)
    logger.info("Opening port and listening for 5 seconds...")
    logger.info("(Try pressing buttons on the printer)")

    ser = serial.Serial(COM_PORT, 115200, timeout=0.1)
    ser.reset_input_buffer()

    start_time = time.time()
    data_received = False

    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            logger.success(f"Received unsolicited data: {data.hex()}")
            data_received = True
        time.sleep(0.1)

    if not data_received:
        logger.warning("No unsolicited data received")

    ser.close()


def try_different_bauds():
    """Try different baud rates."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test 5: Different Baud Rates")
    logger.info("=" * 60)

    bauds = [9600, 19200, 38400, 57600, 115200, 230400]

    # Canon protocol message
    START_CODE = 17167
    byte_array = bytearray(34)
    struct.pack_into(">HhbHB", byte_array, 0, START_CODE, -1, -1, 0, 0)
    message = bytes(byte_array)

    for baud in bauds:
        logger.info(f"Trying {baud} baud...")

        try:
            ser = serial.Serial(COM_PORT, baud, timeout=1)
            ser.reset_input_buffer()

            ser.write(message)
            ser.flush()
            time.sleep(0.5)

            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                logger.success(f"  Response at {baud}: {response.hex()}")
                ser.close()
                return baud, response
            else:
                logger.debug(f"  No response at {baud}")

            ser.close()
        except Exception as e:
            logger.error(f"  Error at {baud}: {e}")

    return None, None


def main():
    logger.info("Kodak Step Protocol Explorer")
    logger.info("Using COM6 (identified as working port)")
    logger.info("")

    # Run all tests
    try_canon_protocol()
    try_different_start_codes()
    try_simple_commands()
    just_listen()
    try_different_bauds()

    logger.info("")
    logger.info("=" * 60)
    logger.info("Exploration Complete")
    logger.info("=" * 60)
    logger.warning("")
    logger.warning("If no responses were received, the Kodak Step likely uses")
    logger.warning("a completely different protocol than Canon Ivy 2.")
    logger.warning("")
    logger.warning("Next steps:")
    logger.warning("1. Capture Bluetooth traffic with Wireshark while using official app")
    logger.warning("2. Search for existing Kodak Step protocol documentation")
    logger.warning("3. Try connecting from a Linux system with btmon for debugging")


if __name__ == '__main__':
    main()
