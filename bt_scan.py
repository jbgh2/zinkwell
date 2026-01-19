"""
Bluetooth diagnostic script to scan for devices and discover RFCOMM services.
"""

import socket
from loguru import logger

try:
    AF_BLUETOOTH = socket.AF_BLUETOOTH
    BTPROTO_RFCOMM = socket.BTPROTO_RFCOMM
except AttributeError:
    AF_BLUETOOTH = 32
    BTPROTO_RFCOMM = 3


def test_connection(mac, port):
    """Test connection to a specific MAC and port."""
    logger.info(f"Testing connection to {mac}:{port}")

    try:
        sock = socket.socket(AF_BLUETOOTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)
        sock.settimeout(5)

        logger.debug(f"Attempting to connect...")
        sock.connect((mac, port))

        logger.success(f"Successfully connected to {mac}:{port}")
        sock.close()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to {mac}:{port} - {e}")
        return False


def scan_ports(mac, max_port=30):
    """Scan RFCOMM ports for a given MAC address."""
    logger.info(f"Scanning ports 1-{max_port} for {mac}")
    logger.info("This may take a while...")

    found_ports = []

    for port in range(1, max_port + 1):
        try:
            sock = socket.socket(AF_BLUETOOTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)
            sock.settimeout(2)
            sock.connect((mac, port))

            logger.success(f"Port {port}: OPEN")
            found_ports.append(port)
            sock.close()
        except socket.timeout:
            logger.debug(f"Port {port}: TIMEOUT")
        except OSError as e:
            if "connection refused" in str(e).lower():
                logger.debug(f"Port {port}: CLOSED")
            else:
                logger.debug(f"Port {port}: {e}")
        except Exception as e:
            logger.debug(f"Port {port}: {e}")

    if found_ports:
        logger.success(f"Found open ports: {found_ports}")
    else:
        logger.warning("No open ports found")

    return found_ports


def get_device_info():
    """Get Kodak Step printer info from Windows."""
    logger.info("Checking Bluetooth device status...")

    import subprocess
    result = subprocess.run(
        ['powershell', '-Command',
         "Get-PnpDevice -Class Bluetooth | Where-Object {$_.FriendlyName -like '*KODAK*'} | Select-Object FriendlyName, Status, InstanceId"],
        capture_output=True,
        text=True
    )

    if result.stdout:
        logger.info("Device info:")
        print(result.stdout)
    else:
        logger.warning("Could not retrieve device info")


if __name__ == '__main__':
    KODAK_MAC = "A4:62:DF:A9:72:D4"

    logger.info("=" * 60)
    logger.info("Kodak Step Bluetooth Diagnostic Tool")
    logger.info("=" * 60)

    # Check device status
    get_device_info()

    print("\n")
    logger.info("=" * 60)
    logger.info("RFCOMM Port Scan")
    logger.info("=" * 60)

    # Scan for open ports
    open_ports = scan_ports(KODAK_MAC, max_port=10)

    if not open_ports:
        logger.warning("")
        logger.warning("No open ports found. Possible issues:")
        logger.warning("1. Printer is not powered on")
        logger.warning("2. Printer is not paired/trusted")
        logger.warning("3. Printer is already connected to another device")
        logger.warning("4. Printer is in sleep mode")
