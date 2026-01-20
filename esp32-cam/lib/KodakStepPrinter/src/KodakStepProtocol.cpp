#include "KodakStepProtocol.h"

KodakStepProtocol::KodakStepProtocol() {
}

void KodakStepProtocol::initPacketHeader(uint8_t* buffer, uint8_t flags1, uint8_t flags2) const {
    memset(buffer, 0, BTP_PACKET_SIZE);
    buffer[0] = BTP_START_1;  // 0x1B (ESC)
    buffer[1] = BTP_START_2;  // 0x2A (*)
    buffer[2] = BTP_IDENT_1;  // 0x43 (C)
    buffer[3] = BTP_IDENT_2;  // 0x41 (A)
    buffer[4] = flags1;
    buffer[5] = flags2;
}

void KodakStepProtocol::buildGetAccessoryInfoPacket(uint8_t* buffer, bool isSlim) const {
    // 1B 2A 43 41 00 [00|02] 01 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer, 0x00, isSlim ? BTP_FLAG_SLIM_DEVICE : BTP_FLAG_STANDARD_DEVICE);
    buffer[6] = BTP_CMD_GET_ACCESSORY_INFO;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildGetBatteryLevelPacket(uint8_t* buffer) const {
    // 1B 2A 43 41 00 00 0E 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = BTP_CMD_GET_BATTERY_LEVEL;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildGetPageTypePacket(uint8_t* buffer) const {
    // 1B 2A 43 41 00 00 0D 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = BTP_CMD_GET_PAGE_TYPE;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildGetPrintCountPacket(uint8_t* buffer) const {
    // 1B 2A 43 41 00 00 00 01 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = BTP_CMD_PRINT_READY;  // 0x00
    buffer[7] = 0x01;  // Flag distinguishes from PRINT_READY
}

void KodakStepProtocol::buildGetAutoPowerOffPacket(uint8_t* buffer) const {
    // 1B 2A 43 41 00 00 10 00 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = BTP_CMD_GET_AUTO_POWER_OFF;
    buffer[7] = 0x00;
}

void KodakStepProtocol::buildPrintReadyPacket(uint8_t* buffer, uint32_t imageSize, uint8_t numCopies) const {
    // 1B 2A 43 41 00 00 00 00 [SZ] [SZ] [SZ] [CP] 00 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = BTP_CMD_PRINT_READY;  // 0x00
    buffer[7] = 0x00;

    // Image size - 3 bytes, big-endian
    buffer[8] = (imageSize >> 16) & 0xFF;  // MSB
    buffer[9] = (imageSize >> 8) & 0xFF;
    buffer[10] = imageSize & 0xFF;         // LSB

    // Number of copies
    buffer[11] = numCopies;

    // Bytes 12-15 are zeros (already set by initPacketHeader)
}

void KodakStepProtocol::buildStartOfSendAck(uint8_t* buffer) const {
    // 1B 2A 43 41 00 00 01 00 02 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = 0x01;
    buffer[7] = 0x00;
    buffer[8] = 0x02;
}

void KodakStepProtocol::buildEndOfReceivedAck(uint8_t* buffer) const {
    // 1B 2A 43 41 00 00 01 01 02 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = 0x01;
    buffer[7] = 0x01;
    buffer[8] = 0x02;
}

void KodakStepProtocol::buildErrorMessageAck(uint8_t* buffer, uint8_t errorCode) const {
    // 1B 2A 43 41 00 00 01 00 [EC] 00 00 00... (rest zeros)
    initPacketHeader(buffer);
    buffer[6] = 0x01;
    buffer[7] = 0x00;
    buffer[8] = errorCode;
}

bool KodakStepProtocol::parseResponse(const uint8_t* response, uint8_t* errorCode, uint8_t* dataOut) const {
    if (errorCode == nullptr) {
        return false;
    }

    // Verify header
    if (response[0] != BTP_START_1 ||
        response[1] != BTP_START_2 ||
        response[2] != BTP_IDENT_1 ||
        response[3] != BTP_IDENT_2) {
        *errorCode = BTP_ERR_NOT_CONNECTED;
        return false;
    }

    // Extract error code from byte 8
    *errorCode = response[8];

    // Copy payload if requested (bytes 9-33)
    if (dataOut != nullptr) {
        memcpy(dataOut, &response[9], 25);
    }

    return (*errorCode == BTP_ERR_SUCCESS);
}

uint16_t KodakStepProtocol::parsePrintCount(const uint8_t* response) const {
    // Print count is a 16-bit value in bytes 8-9 (big-endian)
    return (response[8] << 8) | response[9];
}

uint8_t KodakStepProtocol::parseAutoPowerOff(const uint8_t* response) const {
    // Auto power off timeout in minutes is in byte 8
    return response[8];
}

uint8_t KodakStepProtocol::parseErrorCode(const uint8_t* response) const {
    // Error code is always in byte 8
    return response[8];
}

const char* KodakStepProtocol::getErrorString(uint8_t errorCode) {
    switch (errorCode) {
        case BTP_ERR_SUCCESS: return "Success";
        case BTP_ERR_PAPER_JAM: return "Paper jam";
        case BTP_ERR_NO_PAPER: return "Out of paper";
        case BTP_ERR_COVER_OPEN: return "Printer cover open";
        case BTP_ERR_PAPER_MISMATCH: return "Wrong paper type";
        case BTP_ERR_LOW_BATTERY: return "Battery too low";
        case BTP_ERR_OVERHEATING: return "Printer overheating";
        case BTP_ERR_COOLING: return "Printer cooling";
        case BTP_ERR_MISFEED: return "Paper misfeed";
        case BTP_ERR_BUSY: return "Printer busy";
        case BTP_ERR_NOT_CONNECTED: return "Not connected";
        default: return "Unknown error";
    }
}

void KodakStepProtocol::printPacketHex(const uint8_t* packet, size_t length, bool enabled) {
    if (!enabled) return;

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
