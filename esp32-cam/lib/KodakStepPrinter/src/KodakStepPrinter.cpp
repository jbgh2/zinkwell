#include "KodakStepPrinter.h"

KodakStepPrinter::KodakStepPrinter() {
    btSerial = nullptr;
    memset(&status, 0, sizeof(status));
    memset(lastError, 0, sizeof(lastError));
    debugEnabled = true;  // Default to enabled for backward compatibility
}

KodakStepPrinter::~KodakStepPrinter() {
    disconnect();
    if (btSerial != nullptr) {
        delete btSerial;
        btSerial = nullptr;
    }
}

void KodakStepPrinter::setDebugOutput(bool enabled) {
    debugEnabled = enabled;
}

bool KodakStepPrinter::getDebugOutput() const {
    return debugEnabled;
}

void KodakStepPrinter::debugPrint(const char* msg) {
    if (debugEnabled) {
        Serial.print(msg);
    }
}

void KodakStepPrinter::debugPrintln(const char* msg) {
    if (debugEnabled) {
        Serial.println(msg);
    }
}

bool KodakStepPrinter::begin(const char* deviceName) {
    if (btSerial != nullptr) {
        delete btSerial;
        btSerial = nullptr;
    }

    btSerial = new (std::nothrow) BluetoothSerial();
    if (btSerial == nullptr) {
        setError("Failed to allocate BluetoothSerial (out of memory)");
        return false;
    }

    // Initialize in master mode (second param = true) to connect to printer
    if (!btSerial->begin(deviceName, true)) {
        setError("Failed to initialize Bluetooth");
        delete btSerial;
        btSerial = nullptr;
        return false;
    }

    if (debugEnabled) {
        Serial.print("Bluetooth initialized as: ");
        Serial.println(deviceName);
    }
    return true;
}

bool KodakStepPrinter::connect(const char* printerAddress) {
    if (btSerial == nullptr) {
        setError("Bluetooth not initialized. Call begin() first.");
        return false;
    }

    if (debugEnabled) {
        Serial.print("Connecting to printer at address: ");
        Serial.println(printerAddress);
    }

    if (!btSerial->connect(printerAddress)) {
        setError("Failed to connect to printer");
        return false;
    }

    delay(500);  // Initial connection delay
    yield();
    status.is_connected = true;
    debugPrintln("Connected to printer");
    return true;
}

bool KodakStepPrinter::connectByName(const char* printerName) {
    if (btSerial == nullptr) {
        setError("Bluetooth not initialized. Call begin() first.");
        return false;
    }

    if (printerName == nullptr) {
        setError("Printer name cannot be null");
        return false;
    }

    debugPrintln("\n=== Bluetooth Discovery ===");
    if (debugEnabled) {
        Serial.print("Searching for device containing: ");
        Serial.println(printerName);
    }

    // Scan for devices first
    debugPrintln("Starting Bluetooth scan...");
    BTScanResults* scanResults = btSerial->discover(10000);  // 10 second scan

    if (scanResults == nullptr) {
        debugPrintln("ERROR: Scan returned null");
        setError("Bluetooth scan failed");
        return false;
    }

    int count = scanResults->getCount();
    if (debugEnabled) {
        Serial.print("Found ");
        Serial.print(count);
        Serial.println(" Bluetooth devices:");
    }

    BTAddress targetAddress;
    bool found = false;

    // Pre-convert search string to lowercase once (avoid repeated allocations)
    size_t searchLen = strlen(printerName);
    char* searchLower = (char*)alloca(searchLen + 1);  // Stack allocation
    for (size_t i = 0; i <= searchLen; i++) {
        searchLower[i] = tolower(printerName[i]);
    }

    for (int i = 0; i < count; i++) {
        BTAdvertisedDevice* device = scanResults->getDevice(i);
        if (device) {
            // Use C strings directly to avoid String heap allocations
            const char* name = device->getName().c_str();
            const char* addr = device->getAddress().toString().c_str();

            if (debugEnabled) {
                Serial.print("  [");
                Serial.print(i);
                Serial.print("] ");
                Serial.print(addr);
                Serial.print(" - \"");
                Serial.print(name);
                Serial.println("\"");
            }

            // Case-insensitive substring search without String allocations
            size_t nameLen = strlen(name);
            bool match = false;
            for (size_t j = 0; j + searchLen <= nameLen && !match; j++) {
                bool subMatch = true;
                for (size_t k = 0; k < searchLen && subMatch; k++) {
                    if (tolower(name[j + k]) != searchLower[k]) {
                        subMatch = false;
                    }
                }
                if (subMatch) {
                    match = true;
                }
            }

            if (match) {
                debugPrintln("      ^ MATCH FOUND!");
                targetAddress = device->getAddress();
                found = true;
                break;
            }
        }
        yield();  // Allow other tasks during scan processing
    }
    debugPrintln("=== End Discovery ===\n");

    if (!found) {
        setError("Printer not found in scan");
        return false;
    }

    if (debugEnabled) {
        Serial.print("Connecting to address: ");
        Serial.println(targetAddress.toString().c_str());
    }

    // Connect using the BTAddress directly
    if (!btSerial->connect(targetAddress)) {
        debugPrintln("connect() returned false");
        setError("Failed to connect to printer");
        return false;
    }

    debugPrintln("connect() returned true, waiting...");
    delay(1000);  // Initial connection delay
    yield();

    // Verify connection
    if (!btSerial->connected()) {
        debugPrintln("connected() check failed after connect()");
        setError("Connection lost after connect");
        return false;
    }

    status.is_connected = true;
    debugPrintln("Connected to printer successfully!");
    return true;
}

void KodakStepPrinter::disconnect() {
    if (btSerial != nullptr && status.is_connected) {
        btSerial->disconnect();
        status.is_connected = false;
        debugPrintln("Disconnected from printer");
    }
}

bool KodakStepPrinter::isConnected() {
    return status.is_connected && (btSerial != nullptr) && btSerial->connected();
}

bool KodakStepPrinter::initialize(bool isSlimDevice, uint8_t* rawResponse) {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    // Send GET_ACCESSORY_INFO
    protocol.buildGetAccessoryInfoPacket(command, isSlimDevice);

    debugPrintln("Sending GET_ACCESSORY_INFO...");
    if (debugEnabled) {
        protocol.printPacketHex(command, BTP_PACKET_SIZE, debugEnabled);
    }

    if (!sendAndReceive(command, response)) {
        setError("Failed to get accessory info");
        return false;
    }

    // Copy raw response if requested
    if (rawResponse != nullptr) {
        memcpy(rawResponse, response, BTP_PACKET_SIZE);
    }

    uint8_t errorCode;
    if (!protocol.parseResponse(response, &errorCode)) {
        setError(protocol.getErrorString(errorCode));
        status.error_code = errorCode;
        return false;
    }

    status.is_slim_device = isSlimDevice;
    status.error_code = BTP_ERR_SUCCESS;

    debugPrintln("Printer initialized successfully");
    delay(500);  // Wait after initialization
    yield();
    return true;
}

bool KodakStepPrinter::getBatteryLevel(uint8_t* level, uint8_t* rawResponse) {
    if (level == nullptr) {
        setError("Output parameter 'level' cannot be null");
        return false;
    }

    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    // Battery level is in byte 12 of GET_ACCESSORY_INFO response
    // Note: GET_BATTERY_LEVEL (0x0E) returns charging status, not battery percentage
    protocol.buildGetAccessoryInfoPacket(command, status.is_slim_device);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get battery level");
        return false;
    }

    if (rawResponse != nullptr) {
        memcpy(rawResponse, response, BTP_PACKET_SIZE);
    }

    *level = response[12];
    status.battery_level = *level;

    delay(100);
    yield();
    return true;
}

bool KodakStepPrinter::getChargingStatus(bool* isCharging, uint8_t* rawResponse) {
    if (isCharging == nullptr) {
        setError("Output parameter 'isCharging' cannot be null");
        return false;
    }

    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    // GET_BATTERY_LEVEL (0x0E) returns charging status in byte 8 (1 = charging)
    protocol.buildGetBatteryLevelPacket(command);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get charging status");
        return false;
    }

    if (rawResponse != nullptr) {
        memcpy(rawResponse, response, BTP_PACKET_SIZE);
    }

    // Byte 8 contains charging status: 1 = charging, 0 = not charging
    *isCharging = (response[8] == 1);

    delay(100);
    yield();
    return true;
}

bool KodakStepPrinter::checkPaperStatus() {
    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    protocol.buildGetPageTypePacket(command);

    debugPrintln("Checking paper status...");

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

    debugPrintln("Paper status OK");
    delay(100);
    yield();
    return true;
}

bool KodakStepPrinter::getPrintCount(uint16_t* count) {
    if (count == nullptr) {
        setError("Output parameter 'count' cannot be null");
        return false;
    }

    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    protocol.buildGetPrintCountPacket(command);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get print count");
        return false;
    }

    *count = protocol.parsePrintCount(response);

    delay(100);
    yield();
    return true;
}

bool KodakStepPrinter::getAutoPowerOff(uint8_t* minutes) {
    if (minutes == nullptr) {
        setError("Output parameter 'minutes' cannot be null");
        return false;
    }

    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    protocol.buildGetAutoPowerOffPacket(command);

    if (!sendAndReceive(command, response)) {
        setError("Failed to get auto power off setting");
        return false;
    }

    *minutes = protocol.parseAutoPowerOff(response);

    delay(100);
    yield();
    return true;
}

bool KodakStepPrinter::printImage(const uint8_t* jpegData, size_t dataSize, uint8_t numCopies,
                                   KodakProgressCallback progressCallback) {
    if (jpegData == nullptr) {
        setError("Image data cannot be null");
        return false;
    }

    if (dataSize == 0) {
        setError("Image data size cannot be zero");
        return false;
    }

    if (dataSize > BTP_MAX_IMAGE_SIZE) {
        setError("Image data exceeds maximum size (2MB)");
        return false;
    }

    if (!isConnected()) {
        setError("Not connected to printer");
        return false;
    }

    // Check battery level
    uint8_t battery;
    if (!getBatteryLevel(&battery)) {
        return false;
    }

    if (battery < BTP_MIN_BATTERY_LEVEL) {
        setError("Battery too low to print");
        return false;
    }

    // Check paper status
    if (!checkPaperStatus()) {
        return false;
    }

    // Send PRINT_READY command
    uint8_t command[BTP_PACKET_SIZE];
    uint8_t response[BTP_PACKET_SIZE];

    protocol.buildPrintReadyPacket(command, dataSize, numCopies);

    debugPrintln("Sending PRINT_READY...");
    if (debugEnabled) {
        Serial.print("Image size: ");
        Serial.print(dataSize);
        Serial.print(" bytes, copies: ");
        Serial.println(numCopies);
    }

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

    delay(100);
    yield();

    // Transfer image data
    debugPrintln("Transferring image data...");
    if (!transferImageData(jpegData, dataSize, progressCallback)) {
        setError("Failed to transfer image data");
        return false;
    }

    debugPrintln("Image transfer complete!");
    debugPrintln("Printer should start printing now...");

    return true;
}

bool KodakStepPrinter::transferImageData(const uint8_t* data, size_t size,
                                          KodakProgressCallback progressCallback) {
    size_t offset = 0;
    size_t chunkNum = 0;
    size_t totalChunks = (size + BTP_CHUNK_SIZE - 1) / BTP_CHUNK_SIZE;

    // Check connection once at start, then use skipConnectionCheck for performance
    if (!isConnected()) {
        return false;
    }

    while (offset < size) {
        size_t remaining = size - offset;
        size_t chunkSize = (remaining < BTP_CHUNK_SIZE) ? remaining : BTP_CHUNK_SIZE;

        chunkNum++;
        if (debugEnabled) {
            Serial.print("Sending chunk ");
            Serial.print(chunkNum);
            Serial.print("/");
            Serial.print(totalChunks);
            Serial.print(" (");
            Serial.print(chunkSize);
            Serial.println(" bytes)");
        }

        // Use skipConnectionCheck=true since we checked at start of transfer
        if (!sendCommand(&data[offset], chunkSize, true)) {
            debugPrintln("Failed to send chunk");
            return false;
        }

        offset += chunkSize;

        // Call progress callback if provided
        if (progressCallback != nullptr) {
            progressCallback(offset, size);
        }

        delay(BTP_INTER_CHUNK_DELAY_MS);
        yield();  // Allow other tasks between chunks
    }

    return true;
}

bool KodakStepPrinter::sendCommand(const uint8_t* command, size_t length, bool skipConnectionCheck) {
    if (btSerial == nullptr) {
        return false;
    }

    // Only check connection if not skipped (for performance in hot path)
    if (!skipConnectionCheck && !btSerial->connected()) {
        status.is_connected = false;
        return false;
    }

    size_t written = btSerial->write(command, length);
    if (written != length) {
        if (debugEnabled) {
            Serial.print("Warning: Only wrote ");
            Serial.print(written);
            Serial.print(" of ");
            Serial.print(length);
            Serial.println(" bytes");
        }
        return false;
    }

    return true;
}

bool KodakStepPrinter::receiveResponse(uint8_t* response, uint32_t timeoutMs) {
    if (btSerial == nullptr || !btSerial->connected()) {
        status.is_connected = false;
        return false;
    }

    uint32_t startTime = millis();
    size_t bytesRead = 0;

    while (bytesRead < BTP_PACKET_SIZE) {
        // Unsigned subtraction handles millis() overflow correctly
        if (millis() - startTime > timeoutMs) {
            debugPrintln("Response timeout");
            return false;
        }

        if (btSerial->available()) {
            response[bytesRead++] = btSerial->read();
        } else {
            delay(10);  // Small delay to avoid busy waiting
            yield();    // Allow other tasks
        }
    }

    if (debugEnabled) {
        Serial.println("Received response:");
        protocol.printPacketHex(response, BTP_PACKET_SIZE, debugEnabled);
    }

    return true;
}

bool KodakStepPrinter::sendAndReceive(const uint8_t* command, uint8_t* response) {
    if (!sendCommand(command, BTP_PACKET_SIZE)) {
        return false;
    }

    return receiveResponse(response);
}

KodakStepProtocol::PrinterStatus KodakStepPrinter::getStatus() const {
    return status;
}

const char* KodakStepPrinter::getLastError() const {
    return lastError;
}

void KodakStepPrinter::setError(const char* error) {
    strncpy(lastError, error, sizeof(lastError) - 1);
    lastError[sizeof(lastError) - 1] = '\0';
    if (debugEnabled) {
        Serial.print("Error: ");
        Serial.println(error);
    }
}
