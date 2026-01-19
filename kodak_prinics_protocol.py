"""
Kodak/Prinics Zink Printer Protocol Implementation
Based on reverse engineering by oldmud0
Source: https://gist.github.com/oldmud0/4d8b50cc6fdba0dc301ac78f4f05082d
"""

import struct
import serial
import time
from loguru import logger


class PrinterMessage:
    """Kodak/Prinics Zink printer message format."""

    def __init__(self, message_id, unk1=0, unk2=0, additional_data=b''):
        self.message_id = message_id
        self.unk1 = unk1
        self.unk2 = unk2
        self.additional_data = additional_data

    def to_bytes(self):
        """Convert message to bytes."""
        # Message format:
        # u8    - Message ID
        # u8    - Unknown 1
        # u8    - Unknown 2
        # u8    - Padding (0x00)
        # u32be - Additional data length
        # u8[]  - Additional data

        data_length = len(self.additional_data)

        # Pack the header (8 bytes)
        header = struct.pack('>BBBBI',
                             self.message_id,
                             self.unk1,
                             self.unk2,
                             0x00,  # Padding
                             data_length)

        return header + self.additional_data

    def __repr__(self):
        return f"Message(id={self.message_id}, unk1={self.unk1}, unk2={self.unk2}, data_len={len(self.additional_data)})"


class KodakPrinicsPrinter:
    """Kodak/Prinics Zink Printer controller."""

    # Known message IDs
    MSG_INIT_CONNECTION = 100
    MSG_BEGIN_PRINT = 82
    MSG_UNKNOWN_84 = 84
    MSG_UNKNOWN_101 = 101
    MSG_ERROR_RESPONSE = 3
    MSG_VARIABLE_18 = 18
    MSG_VARIABLE_9 = 9

    def __init__(self, port='COM6', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        """Connect to the printer."""
        logger.info(f"Connecting to Kodak/Prinics printer on {self.port}...")

        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2,
                write_timeout=2
            )

            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            logger.success(f"Connected to {self.port}")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from the printer."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Disconnected")

    def send_message(self, message):
        """Send a message to the printer."""
        if not self.ser or not self.ser.is_open:
            logger.error("Not connected")
            return False

        try:
            data = message.to_bytes()
            logger.debug(f"Sending: {message}")
            logger.debug(f"  Hex: {data.hex()}")

            self.ser.write(data)
            self.ser.flush()

            return True

        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False

    def receive_message(self, timeout=2):
        """Receive a message from the printer."""
        if not self.ser or not self.ser.is_open:
            logger.error("Not connected")
            return None

        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self.ser.in_waiting >= 8:  # Minimum message size
                    # Read header (8 bytes)
                    header = self.ser.read(8)

                    if len(header) < 8:
                        continue

                    # Parse header
                    msg_id, unk1, unk2, padding, data_len = struct.unpack('>BBBBI', header)

                    logger.debug(f"Received header: id={msg_id}, unk1={unk1}, unk2={unk2}, data_len={data_len}")

                    # Read additional data if present
                    additional_data = b''
                    if data_len > 0:
                        additional_data = self.ser.read(data_len)

                    # Create message object
                    message = PrinterMessage(msg_id, unk1, unk2, additional_data)
                    logger.info(f"Received: {message}")

                    if additional_data:
                        logger.debug(f"  Data hex: {additional_data.hex()}")
                        # Try to decode as ASCII
                        try:
                            ascii_text = additional_data.decode('ascii', errors='ignore')
                            if ascii_text.strip():
                                logger.debug(f"  ASCII: {ascii_text}")
                        except:
                            pass

                    return message

                time.sleep(0.1)

            logger.warning("Receive timeout")
            return None

        except Exception as e:
            logger.error(f"Receive failed: {e}")
            return None

    def initialize(self):
        """Initialize connection with the printer."""
        logger.info("Initializing printer connection...")

        # Send initial connection message (100, 1, 0)
        msg = PrinterMessage(self.MSG_INIT_CONNECTION, 1, 0)
        if not self.send_message(msg):
            return False

        time.sleep(0.5)

        # Wait for response
        response = self.receive_message()

        if response:
            if response.message_id == self.MSG_ERROR_RESPONSE:
                logger.error("Printer returned error response")
                return False

            logger.success("Printer initialized successfully")
            return True
        else:
            logger.warning("No response from printer (but might still work)")
            return True  # Try to continue anyway

    def begin_print(self):
        """Begin print operation."""
        logger.info("Beginning print operation...")

        # Send begin print message (82, 0, 0)
        msg = PrinterMessage(self.MSG_BEGIN_PRINT, 0, 0)
        if not self.send_message(msg):
            return False

        time.sleep(0.3)

        # Wait for response
        response = self.receive_message()

        if response:
            logger.info(f"Print begin response: {response}")
            return True
        else:
            logger.warning("No response to begin print")
            return False


def test_connection():
    """Test connection to Kodak/Prinics printer."""
    logger.info("=" * 60)
    logger.info("Kodak/Prinics Zink Printer Protocol Test")
    logger.info("=" * 60)

    printer = KodakPrinicsPrinter(port='COM6')

    try:
        # Connect
        if not printer.connect():
            return False

        # Initialize
        if not printer.initialize():
            logger.warning("Initialization may have failed, but continuing...")

        # Try begin print
        printer.begin_print()

        # Listen for any additional messages
        logger.info("")
        logger.info("Listening for additional messages (5 seconds)...")
        for i in range(5):
            response = printer.receive_message(timeout=1)
            if response:
                logger.info(f"Additional message: {response}")

        logger.success("Test complete!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        printer.disconnect()


if __name__ == '__main__':
    test_connection()
