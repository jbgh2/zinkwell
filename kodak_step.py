import time
import queue
from loguru import logger

from task import (
    StartSessionTask,
    GetStatusTask,
    GetSettingTask,
    SetSettingTask,
    GetPrintReadyTask,
    RebootTask
)
import image

from exceptions import (
    ClientUnavailableError,
    ReceiveTimeoutError,
    AckError,
    LowBatteryError,
    CoverOpenError,
    NoPaperError,
    WrongSmartSheetError
)
from client_windows import ClientThread
from utils import parse_incoming_message

PRINT_BATTERY_MIN = 30
PRINT_DATA_CHUNK = 990


class KodakStepPrinter:
    """
    Kodak Step Printer implementation based on Canon Ivy 2 protocol.
    This is a prototype - the Kodak Step may have protocol differences.
    """
    client = ClientThread()

    def connect(self, mac_address, port=1):
        """Connect to the Kodak Step printer via Bluetooth."""
        logger.info(f"Attempting to connect to Kodak Step printer at {mac_address}:{port}")
        self.client.connect(mac_address, port)

        try:
            battery_level, mtu = self.__start_session()
            logger.debug("Connected; Battery level: {}; MTU: {}".format(battery_level, mtu))
        except Exception as e:
            logger.error(f"Error during session initialization: {e}")
            logger.warning("Connection established but session initialization may have failed.")
            logger.warning("This could indicate protocol differences between Kodak Step and Canon Ivy 2.")
            raise

    def disconnect(self):
        """Disconnect from the printer."""
        self.client.disconnect()

    def is_connected(self):
        """Check if the printer is connected."""
        return self.client.alive.is_set()

    def print(self, target, auto_crop=True, transfer_timeout=60):
        """
        Print an image.

        Args:
            target: Path to image file (str) or image data (bytes)
            auto_crop: Whether to auto-crop the image
            transfer_timeout: Timeout for image transfer in seconds
        """
        image_data = bytes()

        if type(target) is str:
            image_data = image.prepare_image(target, auto_crop)
        elif type(target) is bytes:
            image_data = target
        else:
            raise ValueError(
                "Unsupported target; expected string or bytes but got {}".format(
                    type(target)
                )
            )

        image_length = len(image_data)
        logger.info(f"Prepared image data: {image_length} bytes")

        self.check_print_worthiness()
        self.get_setting()

        # setup the printer to receive the image data
        self.get_print_ready(image_length)

        # split up the image and add to the client queue
        start_index = 0
        chunk_count = 0
        while True:
            end_index = min(start_index + PRINT_DATA_CHUNK, image_length)
            image_chunk = image_data[start_index:end_index]

            self.client.outbound_q.put(image_chunk)
            chunk_count += 1

            if end_index >= image_length:
                break

            start_index = end_index

        logger.debug(f"Beginning data transfer... ({chunk_count} chunks)")

        # wait longer than usual since the transfer takes some time
        self.__receive_message(transfer_timeout)

        logger.debug("Data transfer complete! Printing should begin in a moment")

    def reboot(self):
        """Reboot the printer."""
        return self.__perform_task(RebootTask())

    def get_status(self):
        """Get printer status including battery, errors, and paper state."""
        return self.__perform_task(GetStatusTask())

    def get_setting(self):
        """Get printer settings."""
        return self.__perform_task(GetSettingTask())

    def set_setting(self, auto_power_off):
        """
        Sets the auto power off setting on the printer.

        Args:
            auto_power_off: Time in minutes before the printer turns off without any
                          activity. Supported values are 3, 5, and 10.
        """
        return self.__perform_task(SetSettingTask(auto_power_off))

    def get_print_ready(self, length):
        """Prepare the printer to receive image data."""
        return self.__perform_task(GetPrintReadyTask(length))

    def check_print_worthiness(self):
        """
        Validate that the printer is in a good state for printing.
        Raises exceptions if there are issues.
        """
        status = self.get_status()
        error_code, battery_level, _, is_cover_open, is_no_paper, is_wrong_smart_sheet = status

        if error_code != 0:
            logger.error(
                "Status contains a non-zero error code: {}",
                error_code
            )

        if battery_level < PRINT_BATTERY_MIN:
            raise LowBatteryError()

        if is_cover_open:
            raise CoverOpenError()

        if is_no_paper:
            raise NoPaperError()

        if is_wrong_smart_sheet:
            raise WrongSmartSheetError()

    def __start_session(self):
        """Initialize the communication session."""
        return self.__perform_task(StartSessionTask())

    def __perform_task(self, task):
        """Execute a task and process its response."""
        # send the task's message
        self.__send_message(task.get_message())
        response = self.__receive_message()

        if response[2] != task.ack:
            raise AckError("Got invalid ack; expected {} but got {}".format(
                task.ack, response[2]
            ))

        # process and return the response
        return task.process_response(response)

    def __send_message(self, message):
        """Send a message to the printer."""
        if not self.client.alive.is_set():
            raise ClientUnavailableError()

        # add the message to the client thread's outbound queue
        self.client.outbound_q.put(message)

    def __receive_message(self, timeout=5):
        """Receive a message from the printer."""
        start = int(time.time())
        while int(time.time()) < (start + timeout):
            if not self.client.alive.is_set():
                raise ClientUnavailableError("")

            try:
                # attempt to read the client thread's inbound queue
                response = parse_incoming_message(
                    self.client.inbound_q.get(False, 0.1)
                )

                logger.debug(
                    "Received message: ack: {}, error: {}",
                    response[2],
                    response[3]
                )
                return response
            except queue.Empty:
                pass

        raise ReceiveTimeoutError()