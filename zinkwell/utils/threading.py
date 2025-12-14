"""Threaded client wrapper for Bluetooth transports.

Provides a reusable threading layer for devices that need
non-blocking I/O with queue-based message passing.
"""

import queue
import threading
import time
from typing import Optional

from ..bluetooth.base import BluetoothTransport


class ThreadedClient(threading.Thread):
    """Reusable threaded I/O wrapper around any BluetoothTransport.

    Provides:
    - Background thread for non-blocking I/O
    - Inbound/outbound message queues
    - Auto-disconnect timer
    - Connection state management

    Devices that need threaded I/O can use this directly.
    Devices with simpler needs can use BluetoothTransport directly.

    Example:
        transport = NativeTransport()
        client = ThreadedClient(transport, auto_disconnect_timeout=30)
        client.connect("AA:BB:CC:DD:EE:FF", 1)

        # Send message
        client.outbound_q.put(message_bytes)

        # Receive response
        try:
            response = client.inbound_q.get(timeout=5)
        except queue.Empty:
            raise TimeoutError("No response")

        client.disconnect()
    """

    def __init__(
        self,
        transport: BluetoothTransport,
        receive_size: int = 4096,
        auto_disconnect_timeout: int = 30,
    ):
        """Initialize the threaded client.

        Args:
            transport: Bluetooth transport to wrap.
            receive_size: Buffer size for receiving data.
            auto_disconnect_timeout: Seconds of inactivity before auto-disconnect.
        """
        super().__init__(daemon=True)

        self.transport = transport
        self.receive_size = receive_size
        self.auto_disconnect_timeout = auto_disconnect_timeout

        self.alive = threading.Event()
        self.outbound_q: queue.Queue[bytes] = queue.Queue()
        self.inbound_q: queue.Queue[bytes] = queue.Queue()
        self._disconnect_timer: Optional[threading.Timer] = None

    def connect(self, address: str, port: int) -> None:
        """Connect and start the I/O thread.

        Args:
            address: Bluetooth MAC address.
            port: RFCOMM channel.
        """
        self.transport.connect(address, port)
        self.alive.set()
        self._reset_disconnect_timer()
        self.start()

    def disconnect(self, timeout: Optional[float] = None) -> None:
        """Stop thread and close connection.

        Args:
            timeout: Max time to wait for thread to stop.
        """
        self.alive.clear()

        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None

        self.transport.disconnect()

        try:
            self.join(timeout)
        except RuntimeError:
            pass  # Thread not started or already joined

    def run(self) -> None:
        """Background I/O loop."""
        while self.alive.is_set():
            # Check connection health
            if not self.transport.is_connected():
                self.disconnect()
                break

            # Send outbound messages (blocking with short timeout)
            self.transport.set_blocking(True)
            try:
                message = self.outbound_q.get(timeout=0.1)
                self.transport.send(message)
                self._reset_disconnect_timer()
                time.sleep(0.02)  # Small delay between sends
            except queue.Empty:
                pass

            # Receive inbound messages (non-blocking)
            self.transport.set_blocking(False)
            try:
                data = self.transport.recv(self.receive_size)
                if data:
                    self.inbound_q.put(data)
            except (OSError, BlockingIOError):
                pass  # No data available

    def _reset_disconnect_timer(self) -> None:
        """Reset the auto-disconnect timer."""
        if self._disconnect_timer is not None:
            self._disconnect_timer.cancel()

        self._disconnect_timer = threading.Timer(
            self.auto_disconnect_timeout,
            self.disconnect,
        )
        self._disconnect_timer.daemon = True
        self._disconnect_timer.start()
