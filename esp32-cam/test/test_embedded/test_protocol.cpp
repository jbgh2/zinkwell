/**
 * Embedded unit tests for KodakStepProtocol
 *
 * Run with: pio test -e esp32cam
 *
 * These tests verify protocol packet building and parsing on the actual ESP32.
 */

#include <Arduino.h>
#include <unity.h>
#include <KodakStep.h>

KodakStepProtocol protocol;

void setUp(void) {
    // Set up before each test
}

void tearDown(void) {
    // Clean up after each test
}

// =============================================================================
// Packet Building Tests
// =============================================================================

void test_buildGetAccessoryInfoPacket_standard(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildGetAccessoryInfoPacket(buffer, false);

    // Verify header
    TEST_ASSERT_EQUAL_HEX8(0x1B, buffer[0]);  // ESC
    TEST_ASSERT_EQUAL_HEX8(0x2A, buffer[1]);  // *
    TEST_ASSERT_EQUAL_HEX8(0x43, buffer[2]);  // C
    TEST_ASSERT_EQUAL_HEX8(0x41, buffer[3]);  // A

    // Verify flags
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[4]);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[5]);  // Standard device

    // Verify command
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[6]);  // GET_ACCESSORY_INFO
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[7]);

    // Rest should be zeros
    for (int i = 8; i < KODAK_PACKET_SIZE; i++) {
        TEST_ASSERT_EQUAL_HEX8(0x00, buffer[i]);
    }
}

void test_buildGetAccessoryInfoPacket_slim(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildGetAccessoryInfoPacket(buffer, true);

    // Verify slim flag
    TEST_ASSERT_EQUAL_HEX8(0x02, buffer[5]);  // Slim device flag
}

void test_buildGetBatteryLevelPacket(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildGetBatteryLevelPacket(buffer);

    TEST_ASSERT_EQUAL_HEX8(0x1B, buffer[0]);
    TEST_ASSERT_EQUAL_HEX8(0x2A, buffer[1]);
    TEST_ASSERT_EQUAL_HEX8(0x43, buffer[2]);
    TEST_ASSERT_EQUAL_HEX8(0x41, buffer[3]);
    TEST_ASSERT_EQUAL_HEX8(0x0E, buffer[6]);  // GET_BATTERY_LEVEL
}

void test_buildGetPageTypePacket(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildGetPageTypePacket(buffer);

    TEST_ASSERT_EQUAL_HEX8(0x0D, buffer[6]);  // GET_PAGE_TYPE
}

void test_buildGetPrintCountPacket(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildGetPrintCountPacket(buffer);

    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[6]);
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[7]);  // Flag to distinguish from PRINT_READY
}

void test_buildGetAutoPowerOffPacket(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildGetAutoPowerOffPacket(buffer);

    TEST_ASSERT_EQUAL_HEX8(0x10, buffer[6]);  // GET_AUTO_POWER_OFF
}

void test_buildPrintReadyPacket_small_image(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildPrintReadyPacket(buffer, 1000, 1);

    // Verify command
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[6]);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[7]);

    // Verify image size (1000 = 0x0003E8) big-endian in 3 bytes
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[8]);   // MSB
    TEST_ASSERT_EQUAL_HEX8(0x03, buffer[9]);
    TEST_ASSERT_EQUAL_HEX8(0xE8, buffer[10]);  // LSB

    // Verify copies
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[11]);
}

void test_buildPrintReadyPacket_large_image(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    // Test with 100,000 bytes (0x0186A0)
    protocol.buildPrintReadyPacket(buffer, 100000, 3);

    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[8]);   // MSB
    TEST_ASSERT_EQUAL_HEX8(0x86, buffer[9]);
    TEST_ASSERT_EQUAL_HEX8(0xA0, buffer[10]);  // LSB
    TEST_ASSERT_EQUAL_HEX8(0x03, buffer[11]);  // 3 copies
}

void test_buildStartOfSendAck(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildStartOfSendAck(buffer);

    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[6]);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[7]);
    TEST_ASSERT_EQUAL_HEX8(0x02, buffer[8]);
}

void test_buildEndOfReceivedAck(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildEndOfReceivedAck(buffer);

    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[6]);
    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[7]);
    TEST_ASSERT_EQUAL_HEX8(0x02, buffer[8]);
}

void test_buildErrorMessageAck(void) {
    uint8_t buffer[KODAK_PACKET_SIZE];

    protocol.buildErrorMessageAck(buffer, ERR_NO_PAPER);

    TEST_ASSERT_EQUAL_HEX8(0x01, buffer[6]);
    TEST_ASSERT_EQUAL_HEX8(0x00, buffer[7]);
    TEST_ASSERT_EQUAL_HEX8(ERR_NO_PAPER, buffer[8]);
}

// =============================================================================
// Response Parsing Tests
// =============================================================================

void test_parseResponse_success(void) {
    uint8_t response[KODAK_PACKET_SIZE] = {0};
    response[0] = 0x1B;
    response[1] = 0x2A;
    response[2] = 0x43;
    response[3] = 0x41;
    response[8] = 0x00;  // Success

    uint8_t errorCode = 0xFF;
    bool result = protocol.parseResponse(response, &errorCode);

    TEST_ASSERT_TRUE(result);
    TEST_ASSERT_EQUAL_HEX8(ERR_SUCCESS, errorCode);
}

void test_parseResponse_error(void) {
    uint8_t response[KODAK_PACKET_SIZE] = {0};
    response[0] = 0x1B;
    response[1] = 0x2A;
    response[2] = 0x43;
    response[3] = 0x41;
    response[8] = ERR_NO_PAPER;

    uint8_t errorCode = 0xFF;
    bool result = protocol.parseResponse(response, &errorCode);

    TEST_ASSERT_FALSE(result);
    TEST_ASSERT_EQUAL_HEX8(ERR_NO_PAPER, errorCode);
}

void test_parseResponse_invalid_header(void) {
    uint8_t response[KODAK_PACKET_SIZE] = {0};  // All zeros = invalid

    uint8_t errorCode = 0xFF;
    bool result = protocol.parseResponse(response, &errorCode);

    TEST_ASSERT_FALSE(result);
    TEST_ASSERT_EQUAL_HEX8(ERR_NOT_CONNECTED, errorCode);
}

void test_parsePrintCount(void) {
    uint8_t response[KODAK_PACKET_SIZE] = {0};
    response[0] = 0x1B;
    response[1] = 0x2A;
    response[2] = 0x43;
    response[3] = 0x41;
    response[8] = 0x01;  // High byte
    response[9] = 0x2C;  // Low byte = 0x012C = 300

    uint16_t count = protocol.parsePrintCount(response);

    TEST_ASSERT_EQUAL_UINT16(300, count);
}

void test_parseAutoPowerOff(void) {
    uint8_t response[KODAK_PACKET_SIZE] = {0};
    response[8] = 15;  // 15 minutes

    uint8_t minutes = protocol.parseAutoPowerOff(response);

    TEST_ASSERT_EQUAL_UINT8(15, minutes);
}

// =============================================================================
// Error String Tests
// =============================================================================

void test_getErrorString_success(void) {
    const char* str = KodakStepProtocol::getErrorString(ERR_SUCCESS);
    TEST_ASSERT_EQUAL_STRING("Success", str);
}

void test_getErrorString_no_paper(void) {
    const char* str = KodakStepProtocol::getErrorString(ERR_NO_PAPER);
    TEST_ASSERT_EQUAL_STRING("Out of paper", str);
}

void test_getErrorString_unknown(void) {
    const char* str = KodakStepProtocol::getErrorString(0xFF);
    TEST_ASSERT_EQUAL_STRING("Unknown error", str);
}

// =============================================================================
// Constants Tests
// =============================================================================

void test_packet_size_constant(void) {
    TEST_ASSERT_EQUAL(34, KODAK_PACKET_SIZE);
}

void test_chunk_size_constant(void) {
    TEST_ASSERT_EQUAL(4096, KODAK_CHUNK_SIZE);
}

void test_min_battery_constant(void) {
    TEST_ASSERT_EQUAL(30, KODAK_MIN_BATTERY_LEVEL);
}

// =============================================================================
// Main
// =============================================================================

void setup() {
    delay(2000);  // Wait for Serial monitor to connect

    UNITY_BEGIN();

    // Packet building tests
    RUN_TEST(test_buildGetAccessoryInfoPacket_standard);
    RUN_TEST(test_buildGetAccessoryInfoPacket_slim);
    RUN_TEST(test_buildGetBatteryLevelPacket);
    RUN_TEST(test_buildGetPageTypePacket);
    RUN_TEST(test_buildGetPrintCountPacket);
    RUN_TEST(test_buildGetAutoPowerOffPacket);
    RUN_TEST(test_buildPrintReadyPacket_small_image);
    RUN_TEST(test_buildPrintReadyPacket_large_image);
    RUN_TEST(test_buildStartOfSendAck);
    RUN_TEST(test_buildEndOfReceivedAck);
    RUN_TEST(test_buildErrorMessageAck);

    // Response parsing tests
    RUN_TEST(test_parseResponse_success);
    RUN_TEST(test_parseResponse_error);
    RUN_TEST(test_parseResponse_invalid_header);
    RUN_TEST(test_parsePrintCount);
    RUN_TEST(test_parseAutoPowerOff);

    // Error string tests
    RUN_TEST(test_getErrorString_success);
    RUN_TEST(test_getErrorString_no_paper);
    RUN_TEST(test_getErrorString_unknown);

    // Constants tests
    RUN_TEST(test_packet_size_constant);
    RUN_TEST(test_chunk_size_constant);
    RUN_TEST(test_min_battery_constant);

    UNITY_END();
}

void loop() {
    // Nothing to do
}
