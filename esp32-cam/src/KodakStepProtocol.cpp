#include "KodakStepProtocol.h"

KodakStepProtocol::KodakStepProtocol() {
}

void KodakStepProtocol::initPacketHeader(uint8_t* buffer, uint8_t flags1, uint8_t flags2) {
    memset(buffer, 0, KODAK_PACKET_SIZE);
    buffer[0] = KODAK_START_1;  // 0x1B (ESC)
    buffer[1] = KODAK_START_2;  // 0x2A (*)
    buffer[2] = KODAK_IDENT_1;  // 0x43 (C)
    buffer[3] = KODAK_IDENT_2;  // 0x41 (A)
    buffer[4] = flags1;
    buffer[5] = flags2;
}

void KodakStepProtocol::buildGetAccessoryInfoPacket(uint8_t* buffer, bool isSlim) {
    // 1B 2A 43 41 00 [00|02] 01 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer, 0x00, isSlim ? FLAG_SLIM_DEVICE : FLAG_STANDARD_DEVICE);
    buffer[6] = CMD_GET_ACCESSORY_INFO;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildGetBatteryLevelPacket(uint8_t* buffer) {
    // 1B 2A 43 41 00 00 0E 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = CMD_GET_BATTERY_LEVEL;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildGetPageTypePacket(uint8_t* buffer) {
    // 1B 2A 43 41 00 00 0D 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = CMD_GET_PAGE_TYPE;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildGetPrintCountPacket(uint8_t* buffer) {
    // 1B 2A 43 41 00 00 00 01 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = CMD_PRINT_READY;  // 0x00
    buffer[7] = 0x01;  // Flag distinguishes from PRINT_READY
}

void KodakStepProtocol::buildGetAutoPowerOffPacket(uint8_t* buffer) {
    // 1B 2A 43 41 00 00 10 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = CMD_GET_AUTO_POWER_OFF;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildPrintReadyPacket(uint8_t* buffer, uint32_t imageSize, uint8_t numCopies) {
    // 1B 2A 43 41 00 00 00 00 [SZ] [SZ] [SZ] [CP] 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = CMD_PRINT_READY;  // 0x00
    buffer[7] = 0x00;

    // Image size - 3 bytes, big-endian
    buffer[8] = (imageSize >> 16) & 0xFF;  // MSB
    buffer[9] = (imageSize >> 8) & 0xFF;
    buffer[10] = imageSize & 0xFF;         // LSB

    // Number of copies
    buffer[11] = numCopies;

    // Bytes 12-15 are zeros (already set by initPacketHeader)
}

void KodakStepProtocol::buildStartOfSendAck(uint8_t* buffer) {
    // 1B 2A 43 41 00 00 01 00 02 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = 0x01;
    buffer[7] = 0x00;
    buffer[8] = 0x02;
}

void KodakStepProtocol::buildEndOfReceivedAck(uint8_t* buffer) {
    // 1B 2A 43 41 00 00 01 01 02 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = 0x01;
    buffer[7] = 0x01;
    buffer[8] = 0x02;
}

void KodakStepProtocol::buildErrorMessageAck(uint8_t* buffer, uint8_t errorCode) {
    // 1B 2A 43 41 00 00 01 00 [EC] 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = 0x01;
    buffer[7] = 0x00;
    buffer[8] = errorCode;
}

bool KodakStepProtocol::parseResponse(const uint8_t* response, uint8_t* errorCode, uint8_t* dataOut) {
    // Verify header
    if (response[0] != KODAK_START_1 ||
        response[1] != KODAK_START_2 ||
        response[2] != KODAK_IDENT_1 ||
        response[3] != KODAK_IDENT_2) {
        Serial.println("Invalid response header");
        *errorCode = ERR_NOT_CONNECTED;
        return false;
    }

    // Extract error code from byte 8
    *errorCode = response[8];

    // Copy payload if requested (bytes 9-33)
    if (dataOut != nullptr) {
        memcpy(dataOut, &response[9], 25);
    }

    return (*errorCode == ERR_SUCCESS);
}

uint8_t KodakStepProtocol::parseBatteryLevel(const uint8_t* response) {
    // Check response type - byte 6 indicates what kind of response this is
    if (response[6] == 0x01) {
        // GET_ACCESSORY_INFO response - battery level is in byte 12
        return response[12];
    } else if (response[6] == 0x04) {
        // GET_BATTERY_LEVEL response type 0x04
        // Byte 8 appears to be charging status (1=charging), not battery level
        // Battery level should come from GET_ACCESSORY_INFO instead
        // Return 0 to indicate this response doesn't contain battery percentage
        return 0;
    }
    // Fallback to byte 8 for unknown response types
    return response[8];
}

uint16_t KodakStepProtocol::parsePrintCount(const uint8_t* response) {
    // Print count is a 16-bit value in bytes 8-9 (big-endian)
    return (response[8] << 8) | response[9];
}

uint8_t KodakStepProtocol::parseAutoPowerOff(const uint8_t* response) {
    // Auto power off timeout in minutes is in byte 8
    return response[8];
}

uint8_t KodakStepProtocol::parseErrorCode(const uint8_t* response) {
    // Error code is always in byte 8
    return response[8];
}

const char* KodakStepProtocol::getErrorString(uint8_t errorCode) {
    switch (errorCode) {
        case ERR_SUCCESS: return "Success";
        case ERR_PAPER_JAM: return "Paper jam";
        case ERR_NO_PAPER: return "Out of paper";
        case ERR_COVER_OPEN: return "Printer cover open";
        case ERR_PAPER_MISMATCH: return "Wrong paper type";
        case ERR_LOW_BATTERY: return "Battery too low";
        case ERR_OVERHEATING: return "Printer overheating";
        case ERR_COOLING: return "Printer cooling";
        case ERR_MISFEED: return "Paper misfeed";
        case ERR_BUSY: return "Printer busy";
        case ERR_NOT_CONNECTED: return "Not connected";
        default: return "Unknown error";
    }
}

void KodakStepProtocol::printPacketHex(const uint8_t* packet, size_t length) {
    Serial.print("Packet [");
    Serial.print(length);
    Serial.print(" bytes]: ");
    for (size_t i = 0; i < length; i++) {
        if (packet[i] < 0x10) Serial.print("0");
        Serial.print(packet[i], HEX);
        Serial.print(" ");
        if ((i + 1) % 16 == 0 && i < length - 1) {
            Serial.println();
            Serial.print("         ");
        }
    }
    Serial.println();
}
