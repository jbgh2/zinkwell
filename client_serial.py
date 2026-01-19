import serial
import queue
import threading
import time
from loguru import logger

# the amount of time without sending any messages before disconnecting (in seconds)
AUTO_DISCONNECT_TIMEOUT = 30


class ClientThread(threading.Thread):
    """Serial/COM port client for Windows Bluetooth connections."""

    def __init__(self, receive_size=4096):
        super().__init__()

        self.receive_size = receive_size

        self.ser = None
        self.alive = threading.Event()

        self.outbound_q = queue.Queue()
        self.inbound_q = queue.Queue()

        self.disconnect_timer = threading.Timer(
            AUTO_DISCONNECT_TIMEOUT,
            self.disconnect
        )

    def connect(self, port, baudrate=115200):
        """
        Connect to a serial/COM port.

        Args:
            port: COM port name (e.g., "COM3")
            baudrate: Baud rate (default 115200)
        """
        try:
            logger.debug(f"Opening serial port {port} at {baudrate} baud...")

            # Create serial connection
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
                write_timeout=2
            )

            # Clear buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            logger.info(f"Successfully opened {port}")

            self.ser = ser
            self.alive.set()
            self.start()

        except Exception as e:
            logger.error(f"Failed to open port: {e}")
            raise

    def run(self):
        """Main thread loop for handling send/receive operations."""
        logger.debug("Client thread started")

        while self.alive.is_set():
            # Check that the serial port is still active
            if not self.ser or not self.ser.is_open:
                logger.warning("Serial port closed")
                self.disconnect()
                break

            # Send any outbound messages
            try:
                # Get the next out queue item (non-blocking with short timeout)
                message = self.outbound_q.get(True, 0.1)

                logger.debug(f"Sending {len(message)} bytes")
                self.ser.write(message)
                self.ser.flush()  # Ensure data is sent

                time.sleep(0.02)

                # Reset the timer
                self.disconnect_timer.cancel()
                self.disconnect_timer = threading.Timer(
                    AUTO_DISCONNECT_TIMEOUT,
                    self.disconnect
                )
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error sending message: {e}")

            # Receive incoming messages
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        logger.debug(f"Received {len(data)} bytes")
                        self.inbound_q.put(data)
            except Exception as e:
                logger.debug(f"Receive error: {e}")
                pass

    def disconnect(self, timeout=None):
        """Disconnect from the serial port."""
        logger.debug("Disconnecting...")

        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass

        self.disconnect_timer.cancel()

        # Unset the alive event so run() will not continue
        self.alive.clear()

        try:
            # Block the calling thread until this thread completes
            threading.Thread.join(self, timeout)
        except RuntimeError:
            pass

        logger.info("Disconnected")
