import socket
import queue
import threading
import time
from loguru import logger

# the amount of time without sending any messages before disconnecting (in seconds)
AUTO_DISCONNECT_TIMEOUT = 30

# Bluetooth socket constants (cross-platform)
# Use AF_BLUETOOTH (available on Windows/Linux) instead of AF_BTH
try:
    AF_BLUETOOTH = socket.AF_BLUETOOTH
    BTPROTO_RFCOMM = socket.BTPROTO_RFCOMM
except AttributeError:
    # Fallback for older systems
    AF_BLUETOOTH = 32  # AF_BTH on Windows
    BTPROTO_RFCOMM = 3


class ClientThread(threading.Thread):
    """Windows-compatible Bluetooth RFCOMM client using native sockets."""

    def __init__(self, receive_size=4096):
        super().__init__()

        self.receive_size = receive_size

        self.sock = None
        self.alive = threading.Event()

        self.outbound_q = queue.Queue()
        self.inbound_q = queue.Queue()

        self.disconnect_timer = threading.Timer(
            AUTO_DISCONNECT_TIMEOUT,
            self.disconnect
        )

    def connect(self, mac, port):
        """
        Connect to a Bluetooth device using Windows sockets.

        Args:
            mac: Bluetooth MAC address (e.g., "A4:62:DF:A9:72:D4")
            port: RFCOMM port (typically 1)
        """
        try:
            # Create a Bluetooth socket
            logger.debug(f"Creating Bluetooth RFCOMM socket...")
            sock = socket.socket(AF_BLUETOOTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)

            # Connect to the device
            # Windows expects MAC address in format without colons
            # and as an integer, or we can use (address, port) tuple
            logger.debug(f"Connecting to {mac}:{port}...")
            sock.connect((mac, port))

            logger.info(f"Successfully connected to {mac}:{port}")

            self.sock = sock
            self.alive.set()
            self.start()

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def run(self):
        """Main thread loop for handling send/receive operations."""
        logger.debug("Client thread started")

        while self.alive.is_set():
            # Check that the socket is still active
            try:
                self.sock.getpeername()
            except (OSError, socket.error) as e:
                logger.warning(f"Socket disconnected: {e}")
                self.disconnect()
                break

            # Block for sending messages
            self.sock.setblocking(True)

            # Send any outbound messages
            try:
                # Get the next out queue item
                message = self.outbound_q.get(True, 0.1)

                logger.debug(f"Sending {len(message)} bytes")
                self.sock.send(message)

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

            # Skip blocking for receiving messages
            self.sock.setblocking(False)

            # Receive incoming messages
            try:
                data = self.sock.recv(self.receive_size)
                if data:
                    logger.debug(f"Received {len(data)} bytes")
                    self.inbound_q.put(data)
            except BlockingIOError:
                # No data available, this is normal
                pass
            except Exception as e:
                logger.debug(f"Receive error (may be normal): {e}")
                pass

    def disconnect(self, timeout=None):
        """Disconnect from the Bluetooth device."""
        logger.debug("Disconnecting...")

        if self.sock:
            try:
                self.sock.close()
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