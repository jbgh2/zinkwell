#ifndef KODAK_STEP_PROTOCOL_H
#define KODAK_STEP_PROTOCOL_H

#include <Arduino.h>

// Protocol Constants
#define KODAK_PACKET_SIZE 34
#define KODAK_CHUNK_SIZE 4096
#define KODAK_INTER_CHUNK_DELAY_MS 20
#define KODAK_COMMAND_TIMEOUT_MS 5000
#define KODAK_MIN_BATTERY_LEVEL 30

// Packet Header Bytes
#define KODAK_START_1 0x1B  // ESC
#define KODAK_START_2 0x2A  // *
#define KODAK_IDENT_1 0x43  // C
#define KODAK_IDENT_2 0x41  // A

// Command Codes (Byte 6)
#define CMD_GET_ACCESSORY_INFO 0x01
#define CMD_GET_PAGE_TYPE 0x0D
#define CMD_GET_BATTERY_LEVEL 0x0E
#define CMD_GET_PRINT_COUNT 0x0F
#define CMD_GET_AUTO_POWER_OFF 0x10
#define CMD_PRINT_READY 0x00

// Error Codes (Response Byte 8)
#define ERR_SUCCESS 0x00
#define ERR_PAPER_JAM 0x01
#define ERR_NO_PAPER 0x02
#define ERR_COVER_OPEN 0x03
#define ERR_PAPER_MISMATCH 0x04
#define ERR_LOW_BATTERY 0x05
#define ERR_OVERHEATING 0x06
#define ERR_COOLING 0x07
#define ERR_MISFEED 0x08
#define ERR_BUSY 0x09
#define ERR_NOT_CONNECTED 0xFE

// Device Type Flags (Byte 5)
#define FLAG_STANDARD_DEVICE 0x00
#define FLAG_SLIM_DEVICE 0x02

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

    // Packet construction methods
    void buildGetAccessoryInfoPacket(uint8_t* buffer, bool isSlim = false);
    void buildGetBatteryLevelPacket(uint8_t* buffer);
    void buildGetPageTypePacket(uint8_t* buffer);
    void buildGetPrintCountPacket(uint8_t* buffer);
    void buildGetAutoPowerOffPacket(uint8_t* buffer);
    void buildPrintReadyPacket(uint8_t* buffer, uint32_t imageSize, uint8_t numCopies = 1);
    void buildStartOfSendAck(uint8_t* buffer);
    void buildEndOfReceivedAck(uint8_t* buffer);
    void buildErrorMessageAck(uint8_t* buffer, uint8_t errorCode);

    // Response parsing methods
    bool parseResponse(const uint8_t* response, uint8_t* errorCode, uint8_t* dataOut = nullptr);
    uint8_t parseBatteryLevel(const uint8_t* response);
    uint8_t parseErrorCode(const uint8_t* response);

    // Utility methods
    static const char* getErrorString(uint8_t errorCode);
    static void printPacketHex(const uint8_t* packet, size_t length);

private:
    void initPacketHeader(uint8_t* buffer, uint8_t flags1 = 0x00, uint8_t flags2 = 0x00);
};

#endif // KODAK_STEP_PROTOCOL_H
