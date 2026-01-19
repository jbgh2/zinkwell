"""
Test script to identify which COM port the Kodak Step printer is using.
"""

import serial
import serial.tools.list_ports
import struct
import time
from loguru import logger

# From the protocol documentation
START_CODE = 17167  # 0x430F
COMMAND_START_SESSION = 0
COMMAND_GET_STATUS = 257


def get_base_message(command, flag_1=False, flag_2=False):
    """Create a base protocol message (34 bytes)."""
    b1 = 1
    b2 = 32

    if flag_1:
        b1 = -1
        b2 = -1

    byte_array = bytearray(34)
    struct.pack_into(
        ">HhbHB",
        byte_array,
        0,
        START_CODE,
        b1,
        b2,
        command,
        1 if flag_2 else 0
    )

    return bytes(byte_array)


def test_com_port(port_name):
    """Test a COM port to see if it responds to Kodak Step protocol."""
    logger.info(f"Testing {port_name}...")

    try:
        # Open serial port
        ser = serial.Serial(
            port=port_name,
            baudrate=115200,  # Common Bluetooth baudrate
            timeout=2
        )

        logger.debug(f"Opened {port_name}")

        # Clear any existing data
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Try sending START_SESSION command
        start_session_msg = get_base_message(COMMAND_START_SESSION, True, False)

        logger.debug(f"Sending START_SESSION command ({len(start_session_msg)} bytes)")
        logger.debug(f"Message hex: {start_session_msg.hex()}")

        ser.write(start_session_msg)
        time.sleep(0.5)

        # Try to read response
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            logger.success(f"{port_name}: Got response! ({len(response)} bytes)")
            logger.info(f"Response hex: {response.hex()}")

            ser.close()
            return port_name, response
        else:
            logger.warning(f"{port_name}: No response")
            ser.close()
            return None, None

    except serial.SerialException as e:
        logger.error(f"{port_name}: SerialException - {e}")
        return None, None
    except Exception as e:
        logger.error(f"{port_name}: Error - {e}")
        return None, None


def main():
    logger.info("=" * 60)
    logger.info("Kodak Step COM Port Scanner")
    logger.info("=" * 60)

    # List all COM ports
    logger.info("Available COM ports:")
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        logger.info(f"  {port.device}: {port.description}")

    print()

    # Test Bluetooth COM ports
    bt_ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM10']

    logger.info("=" * 60)
    logger.info("Testing Bluetooth COM ports...")
    logger.info("=" * 60)
    logger.info("Please ensure the Kodak Step printer is powered on!")
    logger.info("")

    working_port = None
    response_data = None

    for port in bt_ports:
        port_name, response = test_com_port(port)
        if port_name:
            working_port = port_name
            response_data = response
            break
        print()

    if working_port:
        logger.success("=" * 60)
        logger.success(f"Found working port: {working_port}")
        logger.success("=" * 60)
        logger.info(f"Response length: {len(response_data)} bytes")
        logger.info(f"Response hex: {response_data.hex()}")

        # Try to parse response
        if len(response_data) >= 34:
            logger.info("Parsing response...")
            # Parse header
            start_code = (response_data[0] << 8) | response_data[1]
            ack_code = (response_data[5] << 8) | response_data[6]
            error_code = response_data[7]

            logger.info(f"  Start code: 0x{start_code:04X} (expected 0x430F)")
            logger.info(f"  ACK code: 0x{ack_code:04X} (expected 0x0000 for START_SESSION)")
            logger.info(f"  Error code: {error_code}")

            # Extract battery and MTU from payload
            if len(response_data) >= 13:
                payload = response_data[8:]
                battery_raw = (payload[1] << 8) | payload[2]
                mtu = (payload[3] << 8) | payload[4]
                logger.info(f"  Battery raw: {battery_raw}")
                logger.info(f"  MTU: {mtu}")

    else:
        logger.error("=" * 60)
        logger.error("No working port found!")
        logger.error("=" * 60)
        logger.warning("Possible issues:")
        logger.warning("1. Printer is not powered on")
        logger.warning("2. Printer is not in pairing/discovery mode")
        logger.warning("3. Printer is using a different protocol")
        logger.warning("4. Need to pair the printer first via Windows Settings")


if __name__ == '__main__':
    main()
