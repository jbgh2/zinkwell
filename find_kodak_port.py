"""
Auto-scan all Bluetooth COM ports to find the Kodak Step printer.
"""

import time
from loguru import logger
from client_serial import ClientThread
from task import StartSessionTask
import struct

# Reduce timeouts for faster scanning
WRITE_TIMEOUT = 1
READ_TIMEOUT = 2


def test_port_quick(com_port):
    """Quickly test if a COM port responds to the protocol."""
    logger.info(f"Testing {com_port}...")

    client = ClientThread()

    try:
        # Try to connect
        import serial
        ser = serial.Serial(
            port=com_port,
            baudrate=115200,
            timeout=READ_TIMEOUT,
            write_timeout=WRITE_TIMEOUT
        )

        ser.reset_input_buffer()
        ser.reset_output_buffer()

        logger.debug(f"  Opened {com_port}")

        # Create START_SESSION message
        START_CODE = 17167
        byte_array = bytearray(34)
        struct.pack_into(">HhbHB", byte_array, 0, START_CODE, -1, -1, 0, 0)
        message = bytes(byte_array)

        logger.debug(f"  Sending START_SESSION ({len(message)} bytes)")
        logger.debug(f"  Message hex: {message.hex()}")

        # Try to send
        try:
            ser.write(message)
            ser.flush()
            logger.debug(f"  Message sent successfully")
        except Exception as e:
            logger.warning(f"  Write failed: {e}")
            ser.close()
            return False

        # Try to read response
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            logger.success(f"  {com_port}: GOT RESPONSE! ({len(response)} bytes)")
            logger.info(f"  Response hex: {response.hex()}")

            # Parse basic response info
            if len(response) >= 7:
                start_code = (response[0] << 8) | response[1]
                ack_code = (response[5] << 8) | response[6]
                error_code = response[7] if len(response) > 7 else None

                logger.info(f"  Start code: 0x{start_code:04X}")
                logger.info(f"  ACK code: 0x{ack_code:04X}")
                if error_code is not None:
                    logger.info(f"  Error code: {error_code}")

            ser.close()
            return com_port
        else:
            logger.debug(f"  No response")
            ser.close()
            return False

    except serial.SerialException as e:
        logger.warning(f"  SerialException: {e}")
        return False
    except Exception as e:
        logger.error(f"  Error: {e}")
        return False


def main():
    logger.info("=" * 60)
    logger.info("Kodak Step Printer Auto-Detect")
    logger.info("=" * 60)
    logger.info("Scanning all Bluetooth COM ports...")
    logger.info("")

    ports_to_test = ['COM3', 'COM4', 'COM5', 'COM6', 'COM10']

    working_port = None

    for port in ports_to_test:
        result = test_port_quick(port)
        if result:
            working_port = result
            break
        print()

    print()
    logger.info("=" * 60)

    if working_port:
        logger.success(f"FOUND WORKING PORT: {working_port}")
        logger.success("=" * 60)
        logger.info(f"Use this command to test:")
        logger.info(f"  python test_kodak_serial.py {working_port}")
    else:
        logger.error("NO WORKING PORT FOUND")
        logger.error("=" * 60)
        logger.warning("Troubleshooting:")
        logger.warning("1. Ensure the Kodak Step printer is powered on")
        logger.warning("2. Check if it's already paired in Windows Bluetooth settings")
        logger.warning("3. Try power cycling the printer")
        logger.warning("4. Check if the printer is connected to another device")


if __name__ == '__main__':
    main()
