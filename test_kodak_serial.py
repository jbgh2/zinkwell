"""
Test script for Kodak Step printer using serial/COM port connection.
You must specify the COM port to use.
"""

import sys
import time
import queue
from loguru import logger

from client_serial import ClientThread
from task import (
    StartSessionTask,
    GetStatusTask,
    GetSettingTask,
    GetPrintReadyTask,
)
from utils import parse_incoming_message
from exceptions import (
    ClientUnavailableError,
    ReceiveTimeoutError,
    AckError,
)
import image


def test_with_com_port(com_port):
    """Test the Kodak Step printer on a specific COM port."""

    logger.info("=" * 60)
    logger.info(f"Testing Kodak Step on {com_port}")
    logger.info("=" * 60)

    client = ClientThread()

    try:
        logger.info(f"Connecting to {com_port}...")
        client.connect(com_port)  # Serial connection

        # Wait a moment for connection to establish
        time.sleep(0.5)

        if not client.alive.is_set():
            logger.error("Failed to establish connection")
            return False

        logger.success("Connected!")

        # Helper function to send/receive messages
        def perform_task(task):
            # Send message
            client.outbound_q.put(task.get_message())

            # Wait for response
            start = int(time.time())
            timeout = 5
            while int(time.time()) < (start + timeout):
                if not client.alive.is_set():
                    raise ClientUnavailableError("Client disconnected")

                try:
                    response = parse_incoming_message(
                        client.inbound_q.get(False, 0.1)
                    )

                    logger.debug(f"Received message: ack: {response[2]}, error: {response[3]}")

                    if response[2] != task.ack:
                        raise AckError(f"Got invalid ack; expected {task.ack} but got {response[2]}")

                    return task.process_response(response)
                except queue.Empty:
                    pass

            raise ReceiveTimeoutError("No response received")

        # Try to start session
        logger.info("")
        logger.info("Attempting to start session...")
        try:
            battery_level, mtu = perform_task(StartSessionTask())
            logger.success(f"Session started! Battery: {battery_level}%, MTU: {mtu}")
        except Exception as e:
            logger.error(f"Session start failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Try to get status
        logger.info("")
        logger.info("Attempting to get status...")
        try:
            status = perform_task(GetStatusTask())
            error_code, battery_level, usb_status, is_cover_open, is_no_paper, is_wrong_smart_sheet = status

            logger.success("Status retrieved:")
            logger.info(f"  Error Code: {error_code}")
            logger.info(f"  Battery Level: {battery_level}%")
            logger.info(f"  USB Connected: {bool(usb_status)}")
            logger.info(f"  Cover Open: {is_cover_open}")
            logger.info(f"  No Paper: {is_no_paper}")
            logger.info(f"  Wrong Smart Sheet: {is_wrong_smart_sheet}")
        except Exception as e:
            logger.error(f"Status query failed: {e}")
            import traceback
            traceback.print_exc()

        # Try to get settings
        logger.info("")
        logger.info("Attempting to get settings...")
        try:
            settings = perform_task(GetSettingTask())
            auto_power_off, firmware_version, tmd_version, number_of_photos_printed, color_id = settings

            logger.success("Settings retrieved:")
            logger.info(f"  Auto Power Off: {auto_power_off} minutes")
            logger.info(f"  Firmware Version: {firmware_version}")
            logger.info(f"  TMD Version: {tmd_version}")
            logger.info(f"  Photos Printed: {number_of_photos_printed}")
            logger.info(f"  Color ID: {color_id}")
        except Exception as e:
            logger.error(f"Settings query failed: {e}")
            import traceback
            traceback.print_exc()

        # Ask about printing
        logger.info("")
        logger.info("=" * 60)
        user_input = input("Attempt to print test image? (y/n): ")
        if user_input.lower() == 'y':
            try:
                logger.info("Preparing image...")
                image_data = image.prepare_image("./assets/test_image.jpg", auto_crop=True)
                image_length = len(image_data)
                logger.info(f"Image prepared: {image_length} bytes")

                logger.info("Sending PRINT_READY command...")
                perform_task(GetPrintReadyTask(image_length))

                logger.info("Transferring image data...")
                PRINT_DATA_CHUNK = 990
                start_index = 0
                chunk_count = 0

                while True:
                    end_index = min(start_index + PRINT_DATA_CHUNK, image_length)
                    image_chunk = image_data[start_index:end_index]
                    client.outbound_q.put(image_chunk)
                    chunk_count += 1

                    if end_index >= image_length:
                        break
                    start_index = end_index

                logger.info(f"Sent {chunk_count} chunks, waiting for completion...")

                # Wait for transfer complete response
                start = int(time.time())
                timeout = 60
                while int(time.time()) < (start + timeout):
                    try:
                        response = parse_incoming_message(
                            client.inbound_q.get(False, 0.1)
                        )
                        logger.success("Transfer complete!")
                        logger.info(f"Response: {response}")
                        break
                    except queue.Empty:
                        pass

                logger.success("Print command completed!")
            except Exception as e:
                logger.error(f"Print failed: {e}")
                import traceback
                traceback.print_exc()

        return True

    except Exception as e:
        logger.error(f"Connection error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        logger.info("")
        logger.info("Disconnecting...")
        client.disconnect()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_kodak_serial.py <COM_PORT>")
        print("Example: python test_kodak_serial.py COM3")
        print("")
        print("Available Bluetooth COM ports:")
        print("  COM3, COM4, COM5, COM6, COM10")
        sys.exit(1)

    com_port = sys.argv[1]
    test_with_com_port(com_port)
