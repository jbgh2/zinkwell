#ifndef KODAK_STEP_PROTOCOL_H
#define KODAK_STEP_PROTOCOL_H

#include <Arduino.h>

// Protocol Constants (BTP = Bluetooth Printer)
#define BTP_PACKET_SIZE 34
#define BTP_CHUNK_SIZE 4096
#define BTP_INTER_CHUNK_DELAY_MS 20
#define BTP_COMMAND_TIMEOUT_MS 5000
#define BTP_MIN_BATTERY_LEVEL 30
#define BTP_MAX_IMAGE_SIZE (2 * 1024 * 1024)  // 2MB max (practical limit for ESP32 with PSRAM)

// Packet Header Bytes
#define BTP_START_1 0x1B  // ESC
#define BTP_START_2 0x2A  // *
#define BTP_IDENT_1 0x43  // C
#define BTP_IDENT_2 0x41  // A

// Command Codes (Byte 6)
#define BTP_CMD_GET_ACCESSORY_INFO 0x01
#define BTP_CMD_GET_PAGE_TYPE 0x0D
#define BTP_CMD_GET_BATTERY_LEVEL 0x0E
#define BTP_CMD_GET_PRINT_COUNT 0x0F
#define BTP_CMD_GET_AUTO_POWER_OFF 0x10
#define BTP_CMD_PRINT_READY 0x00

// Error Codes (Response Byte 8)
#define BTP_ERR_SUCCESS 0x00
#define BTP_ERR_PAPER_JAM 0x01
#define BTP_ERR_NO_PAPER 0x02
#define BTP_ERR_COVER_OPEN 0x03
#define BTP_ERR_PAPER_MISMATCH 0x04
#define BTP_ERR_LOW_BATTERY 0x05
#define BTP_ERR_OVERHEATING 0x06
#define BTP_ERR_COOLING 0x07
#define BTP_ERR_MISFEED 0x08
#define BTP_ERR_BUSY 0x09
#define BTP_ERR_NOT_CONNECTED 0xFE

// Device Type Flags (Byte 5)
#define BTP_FLAG_STANDARD_DEVICE 0x00
#define BTP_FLAG_SLIM_DEVICE 0x02

/**
 * Kodak Step Printer Protocol Implementation
 * Based on reverse-engineered specification from Kodak Step Touch APK
 */
class KodakStepProtocol {
public:
    // Printer status structure
    struct PrinterStatus {
        uint8_t battery_level;
        uint8_t error_code;
        bool is_slim_device;
        bool is_connected;
    };

    KodakStepProtocol();

    // Packet construction methods (all const - don't modify object state)
    void buildGetAccessoryInfoPacket(uint8_t* buffer, bool isSlim = false) const;
    void buildGetBatteryLevelPacket(uint8_t* buffer) const;
    void buildGetPageTypePacket(uint8_t* buffer) const;
    void buildGetPrintCountPacket(uint8_t* buffer) const;
    void buildGetAutoPowerOffPacket(uint8_t* buffer) const;
    void buildPrintReadyPacket(uint8_t* buffer, uint32_t imageSize, uint8_t numCopies = 1) const;
    void buildStartOfSendAck(uint8_t* buffer) const;
    void buildEndOfReceivedAck(uint8_t* buffer) const;
    void buildErrorMessageAck(uint8_t* buffer, uint8_t errorCode) const;

    // Response parsing methods (all const)
    bool parseResponse(const uint8_t* response, uint8_t* errorCode, uint8_t* dataOut = nullptr) const;
    uint16_t parsePrintCount(const uint8_t* response) const;
    uint8_t parseAutoPowerOff(const uint8_t* response) const;
    uint8_t parseErrorCode(const uint8_t* response) const;

    // Utility methods
    static const char* getErrorString(uint8_t errorCode);
    static void printPacketHex(const uint8_t* packet, size_t length, bool enabled = true);

private:
    void initPacketHeader(uint8_t* buffer, uint8_t flags1 = 0x00, uint8_t flags2 = 0x00) const;
};

#endif // KODAK_STEP_PROTOCOL_H
