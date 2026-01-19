#include "KodakStepPrinter.h"

KodakStepPrinter::KodakStepPrinter() {
    btSerial = nullptr;
    memset(&status, 0, sizeof(status));
    memset(lastError, 0, sizeof(lastError));
}

KodakStepPrinter::~KodakStepPrinter() {
    disconnect();
    if (btSerial != nullptr) {
        delete btSerial;
        btSerial = nullptr;
    }
}

bool KodakStepPrinter::begin(const char* deviceName) {
    if (btSerial != nullptr) {
        delete btSerial;
    }

    btSerial = new BluetoothSerial();

    // Initialize in master mode (second param = true) to connect to printer
    if (!btSerial->begin(deviceName, true)) {
        setError("Failed to initialize Bluetooth");
        return false;
    }

    Serial.print("Bluetooth initialized as: ");
    Serial.println(deviceName);
    return true;
}

bool KodakStepPrinter::connect(const char* printerAddress) {
    if (btSerial == nullptr) {
        setError("Bluetooth not initialized. Call begin() first.");
        return false;
    }

    Serial.print("Connecting to printer at address: ");
    Serial.println(printerAddress);

    if (!btSerial->connect(printerAddress)) {
        setError("Failed to connect to printer");
        return false;
    }

    delay_ms(500);  // Initial connection delay
    status.is_connected = true;
    Serial.println("Connected to printer");
    return true;
}

bool KodakStepPrinter::connectByName(const char* printerName) {
    if (btSerial == nullptr) {
        setError("Bluetooth not initialized. Call begin() first.");
        return false;
    }

    Serial.println("\n=== Bluetooth Discovery ===");
    Serial.print("Searching for device containing: ");
    Serial.println(printerName);

    // Scan for devices first
    Serial.println("Starting Bluetooth scan...");
    BTScanResults* scanResults = btSerial->discover(10000);  // 10 second scan

    if (scanResults == nullptr) {
        Serial.println("ERROR: Scan returned null");
        setError("Bluetooth scan failed");
        return false;
    }

    int count = scanResults->getCount();
    Serial.print("Found ");
    Serial.print(count);
    Serial.println(" Bluetooth devices:");

    BTAddress targetAddress;
    bool found = false;
    for (int i = 0; i < count; i++) {
        BTAdvertisedDevice* device = scanResults->getDevice(i);
        if (device) {
            String name = device->getName().c_str();
            String addr = device->getAddress().toString().c_str();
            Serial.print("  [");
            Serial.print(i);
            Serial.print("] ");
            Serial.print(addr);
            Serial.print(" - \"");
            Serial.print(name);
            Serial.println("\"");

            // Check if this is our target printer (case-insensitive)
            String nameLower = name;
            String searchLower = printerName;
            nameLower.toLowerCase();
            searchLower.toLowerCase();
            if (nameLower.indexOf(searchLower) >= 0) {
                Serial.println("      ^ MATCH FOUND!");
                targetAddress = device->getAddress();
                found = true;
            }
        }
    }
    Serial.println("=== End Discovery ===\n");

    if (!found) {
        setError("Printer not found in scan");
        return false;
    }

    Serial.print("Connecting to address: ");
    Serial.println(targetAddress.toString().c_str());

    // Connect using the BTAddress directly
    if (!btSerial->connect(targetAddress)) {
        Serial.println("connect() returned false");
        setError("Failed to connect to printer");
        return false;
    }

    Serial.println("connect() returned true, waiting...");
    delay_ms(1000);  // Initial connection delay

    // Verify connection
    if (!btSerial->connected()) {
        Serial.println("connected() check failed after connect()");
        setError("Connection lost after connect");
        return false;
    }

    status.is_connected = true;
    Serial.println("Connected to printer successfully!");
    return true;
}

void KodakStepPrinter::disconnect() {
    if (btSerial != nullptr && status.is_connected) {
        btSerial->disconnect();
        status.is_connected = false;
        Serial.println("Disconnected from printer");
    }
}

bool KodakStepPrinter::isConnected() {
    return status.is_connected && (btSerial != nullptr) && btSerial->connected();
}

bool KodakStepPrinter::initialize(bool isSlimDevice) {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[KODAK_PACKET_SIZE];
    uint8_t response[KODAK_PACKET_SIZE];

    // Send GET_ACCESSORY_INFO
    protocol.buildGetAccessoryInfoPacket(command, isSlimDevice);

    Serial.println("Sending GET_ACCESSORY_INFO...");
    protocol.printPacketHex(command, KODAK_PACKET_SIZE);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get accessory info");
        return false;
    }

    uint8_t errorCode;
    if (!protocol.parseResponse(response, &errorCode)) {
        setError(protocol.getErrorString(errorCode));
        status.error_code = errorCode;
        return false;
    }

    status.is_slim_device = isSlimDevice;
    status.error_code = ERR_SUCCESS;

    Serial.println("Printer initialized successfully");
    delay_ms(500);  // Wait after initialization
    return true;
}

bool KodakStepPrinter::getBatteryLevel(uint8_t* level) {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[KODAK_PACKET_SIZE];
    uint8_t response[KODAK_PACKET_SIZE];

    protocol.buildGetBatteryLevelPacket(command);

    Serial.println("Requesting battery level...");

    if (!sendAndReceive(command, response)) {
        setError("Failed to get battery level");
        return false;
    }

    // Debug: print raw bytes for battery parsing
    Serial.print("Battery response bytes 6-10: ");
    for (int i = 6; i <= 10; i++) {
        Serial.print("0x");
        if (response[i] < 0x10) Serial.print("0");
        Serial.print(response[i], HEX);
        Serial.print(" ");
    }
    Serial.println();

    *level = protocol.parseBatteryLevel(response);
    status.battery_level = *level;

    Serial.print("Battery level (byte 8): ");
    Serial.print(*level);
    Serial.println("%");

    delay_ms(100);
    return true;
}

bool KodakStepPrinter::checkPaperStatus() {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[KODAK_PACKET_SIZE];
    uint8_t response[KODAK_PACKET_SIZE];

    protocol.buildGetPageTypePacket(command);

    Serial.println("Checking paper status...");

    if (!sendAndReceive(command, response)) {
        setError("Failed to check paper status");
        return false;
    }

    uint8_t errorCode;
    if (!protocol.parseResponse(response, &errorCode)) {
        setError(protocol.getErrorString(errorCode));
        status.error_code = errorCode;
        return false;
    }

    Serial.println("Paper status OK");
    delay_ms(100);
    return true;
}

bool KodakStepPrinter::getPrintCount(uint16_t* count) {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[KODAK_PACKET_SIZE];
    uint8_t response[KODAK_PACKET_SIZE];

    protocol.buildGetPrintCountPacket(command);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get print count");
        return false;
    }

    *count = protocol.parsePrintCount(response);

    delay_ms(100);
    return true;
}

bool KodakStepPrinter::getAutoPowerOff(uint8_t* minutes) {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[KODAK_PACKET_SIZE];
    uint8_t response[KODAK_PACKET_SIZE];

    protocol.buildGetAutoPowerOffPacket(command);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get auto power off setting");
        return false;
    }

    *minutes = protocol.parseAutoPowerOff(response);

    delay_ms(100);
    return true;
}

bool KodakStepPrinter::printImage(const uint8_t* jpegData, size_t dataSize, uint8_t numCopies) {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    // Check battery level
    uint8_t battery;
    if (!getBatteryLevel(&battery)) {
        return false;
    }

    if (battery < KODAK_MIN_BATTERY_LEVEL) {
        Serial.println("WARNING: Battery reported as low, but continuing anyway for testing...");
        // setError("Battery too low to print");
        // return false;
    }

    // Check paper status
    if (!checkPaperStatus()) {
        Serial.println("Warning: Paper check failed, continuing anyway...");
    }

    // Send PRINT_READY command
    uint8_t command[KODAK_PACKET_SIZE];
    uint8_t response[KODAK_PACKET_SIZE];

    protocol.buildPrintReadyPacket(command, dataSize, numCopies);

    Serial.println("Sending PRINT_READY...");
    Serial.print("Image size: ");
    Serial.print(dataSize);
    Serial.print(" bytes, copies: ");
    Serial.println(numCopies);

    if (!sendAndReceive(command, response)) {
        setError("Failed to send PRINT_READY");
        return false;
    }

    uint8_t errorCode;
    if (!protocol.parseResponse(response, &errorCode)) {
        setError(protocol.getErrorString(errorCode));
        status.error_code = errorCode;
        return false;
    }

    delay_ms(100);

    // Transfer image data
    Serial.println("Transferring image data...");
    if (!transferImageData(jpegData, dataSize)) {
        setError("Failed to transfer image data");
        return false;
    }

    Serial.println("Image transfer complete!");
    Serial.println("Printer should start printing now...");

    return true;
}

bool KodakStepPrinter::transferImageData(const uint8_t* data, size_t size) {
    size_t offset = 0;
    size_t chunkNum = 0;
    size_t totalChunks = (size + KODAK_CHUNK_SIZE - 1) / KODAK_CHUNK_SIZE;

    while (offset < size) {
        size_t remaining = size - offset;
        size_t chunkSize = (remaining < KODAK_CHUNK_SIZE) ? remaining : KODAK_CHUNK_SIZE;

        chunkNum++;
        Serial.print("Sending chunk ");
        Serial.print(chunkNum);
        Serial.print("/");
        Serial.print(totalChunks);
        Serial.print(" (");
        Serial.print(chunkSize);
        Serial.println(" bytes)");

        if (!sendCommand(&data[offset], chunkSize)) {
            Serial.println("Failed to send chunk");
            return false;
        }

        offset += chunkSize;
        delay_ms(KODAK_INTER_CHUNK_DELAY_MS);
    }

    return true;
}

bool KodakStepPrinter::sendCommand(const uint8_t* command, size_t length) {
    if (btSerial == nullptr || !isConnected()) {
        return false;
    }

    size_t written = btSerial->write(command, length);
    if (written != length) {
        Serial.print("Warning: Only wrote ");
        Serial.print(written);
        Serial.print(" of ");
        Serial.print(length);
        Serial.println(" bytes");
        return false;
    }

    return true;
}

bool KodakStepPrinter::receiveResponse(uint8_t* response, uint32_t timeoutMs) {
    if (btSerial == nullptr || !isConnected()) {
        return false;
    }

    uint32_t startTime = millis();
    size_t bytesRead = 0;

    while (bytesRead < KODAK_PACKET_SIZE) {
        if (millis() - startTime > timeoutMs) {
            Serial.println("Response timeout");
            return false;
        }

        if (btSerial->available()) {
            response[bytesRead++] = btSerial->read();
        } else {
            delay(10);  // Small delay to avoid busy waiting
        }
    }

    Serial.println("Received response:");
    protocol.printPacketHex(response, KODAK_PACKET_SIZE);

    return true;
}

bool KodakStepPrinter::sendAndReceive(const uint8_t* command, uint8_t* response) {
    if (!sendCommand(command, KODAK_PACKET_SIZE)) {
        return false;
    }

    return receiveResponse(response);
}

KodakStepProtocol::PrinterStatus KodakStepPrinter::getStatus() {
    return status;
}

const char* KodakStepPrinter::getLastError() {
    return lastError;
}

void KodakStepPrinter::setError(const char* error) {
    strncpy(lastError, error, sizeof(lastError) - 1);
    lastError[sizeof(lastError) - 1] = '\0';
    Serial.print("Error: ");
    Serial.println(error);
}

void KodakStepPrinter::delay_ms(uint32_t ms) {
    delay(ms);
}
