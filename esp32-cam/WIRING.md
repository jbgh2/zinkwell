# ESP32-CAM Wiring Guide

## ESP32-CAM Pinout Reference

```
                        ┌─────────────┐
                        │             │
                  GND ──┤ 1       40  ├── GND
                   5V ──┤ 2       39  ├── 5V
                 IO12 ──┤ 3       38  ├── IO13
                 IO13 ──┤ 4       37  ├── IO15
                 IO15 ──┤ 5       36  ├── IO14
                 IO14 ──┤ 6       35  ├── IO2
                  IO2 ──┤ 7       34  ├── IO4 (Flash LED)
                  IO4 ──┤ 8       33  ├── IO16 (UART RX)
                 IO16 ──┤ 9       32  ├── IO17 (UART TX)
                 IO17 ──┤10       31  ├── IO5
                  IO5 ──┤11       30  ├── IO18
                 IO18 ──┤12       29  ├── IO19
                 IO19 ──┤13       28  ├── IO21
                 IO21 ──┤14       27  ├── IO22
                  RX0 ──┤15       26  ├── IO23
                  TX0 ──┤16       25  ├── GND
                  IO22 ──┤17       24  ├── GND
                  IO23 ──┤18       23  ├── 5V
                  GND ──┤19       22  ├── 5V
                        │    USB     │
                        └─────────────┘
```

## Programming Setup (FTDI)

### Standard Connection

```
     ESP32-CAM              FTDI Adapter
  ┌────────────┐        ┌──────────────┐
  │            │        │              │
  │  5V        ├────────┤ 5V (or VCC)  │
  │  GND       ├────────┤ GND          │
  │  U0R (RX0) ├────────┤ TX           │
  │  U0T (TX0) ├────────┤ RX           │
  │  IO0       ├───┐    │              │
  │            │   │    │              │
  └────────────┘   │    └──────────────┘
                   │
              To GND for programming
             (disconnect to run)
```

### Upload Procedure

1. **Connect wiring** as shown above
2. **Connect IO0 to GND** (programming mode)
3. **Plug in FTDI** to computer
4. **Press RESET** button on ESP32-CAM (if available)
5. **Upload code** from IDE
6. **Disconnect IO0** from GND
7. **Press RESET** again to run normally

## Optional Button Connection

### Simple Button

```
     ESP32-CAM              Button
  ┌────────────┐        ┌──────────┐
  │            │        │          │
  │  GPIO14    ├────────┤ Terminal │
  │            │        │          │
  │  GND       ├────────┤ Terminal │
  │            │        │          │
  └────────────┘        └──────────┘
```

ESP32-CAM has internal pull-up resistors, so no external resistor needed.

### Button with External Pull-up (optional)

```
     ESP32-CAM
  ┌────────────┐
  │            │    10kΩ
  │  5V        ├────/\/\/\────┐
  │            │              │
  │  GPIO14    ├──────────────┤
  │            │              │
  │  GND       ├──────┐       │
  │            │      │   ┌───┴───┐
  └────────────┘      │   │ Button│
                      └───┤       │
                          └───────┘
```

## Power Supply

### USB Power Supply

```
                 ┌─────────────┐
  ┌──────────┐   │             │
  │   USB    ├───┤ 5V Regulator├───► ESP32-CAM 5V
  │ Charger  │   │  (optional) │
  │  (2A+)   ├───┤ GND         ├───► ESP32-CAM GND
  └──────────┘   │             │
                 └─────────────┘
```

**Important:**
- Minimum 1A, recommended 2A
- Use quality USB cable (not thin charging cables)
- Consider adding 100μF capacitor near ESP32-CAM power pins

### Battery Power (Optional)

```
  ┌──────────┐      ┌──────────┐
  │ Li-Ion   │      │  Boost   │
  │ Battery  ├──────┤ Converter├───► ESP32-CAM 5V
  │ 3.7V     │      │  to 5V   │
  └──────────┘      └──────────┘
```

## Camera Module Connection

Camera module comes pre-connected with flat ribbon cable. If disconnected:

1. **Locate camera socket** on ESP32-CAM board
2. **Lift black latch** gently
3. **Insert ribbon cable** with contacts facing down
4. **Push latch down** to lock

```
     ESP32-CAM Board                Camera Module
  ┌─────────────────┐            ┌──────────────┐
  │                 │            │              │
  │  ┌───────────┐  │            │   OV2640     │
  │  │ Camera    │  │ ◄────────► │   Sensor     │
  │  │ Socket    │  │  Ribbon    │              │
  │  └───────────┘  │   Cable    │              │
  │                 │            │              │
  └─────────────────┘            └──────────────┘
```

## LED Indicators

### Built-in LEDs

```
  ┌────────────┐
  │  ESP32-CAM │
  │            │
  │   [●] ──── Power LED (always on when powered)
  │   [●] ──── Red LED (GPIO 33, usually for status)
  │   [●] ──── Flash LED (GPIO 4, controllable)
  │            │
  └────────────┘
```

### External Status LED (Optional)

```
     ESP32-CAM
  ┌────────────┐
  │            │     220Ω
  │  GPIO2     ├─────/\/\/\────┐
  │            │               │
  │  GND       ├──────┐       LED
  │            │      │        │
  └────────────┘      └────────┘
```

## Complete Setup Diagram

```
                                        ┌──────────────┐
                                        │ Kodak Step   │
    ┌──────────┐                        │ Printer      │
    │   USB    │                        │              │
    │ 5V Power │                        │ Bluetooth    │
    │  Supply  │                        │              │
    └────┬─────┘                        └──────────────┘
         │                                     ▲
         │ 5V, GND                             │
         ▼                                     │ Bluetooth
  ┌──────────────┐                             │ Classic SPP
  │  ESP32-CAM   │                             │
  │              │─────────────────────────────┘
  │  [Camera]    │
  │  [Bluetooth] │
  │              │
  │   [Flash]    │
  │              │
  └──────┬───────┘
         │
         │ GPIO14
         ▼
    ┌─────────┐
    │ Button  │
    │  (opt)  │
    └─────────┘
```

## Capacitor for Stability (Recommended)

Add a 100μF capacitor between power pins for stable operation:

```
     ESP32-CAM
  ┌────────────┐
  │            │
  │  5V    ────┼───────┐
  │            │       │
  │            │     ┴ ┴  100μF
  │            │     ─ ─  Capacitor
  │            │       │  16V+
  │  GND   ────┼───────┘
  │            │
  └────────────┘
```

Place capacitor as close as possible to ESP32-CAM power pins.

## Troubleshooting Wiring Issues

### Camera Not Working
- Check ribbon cable orientation (contacts down)
- Ensure cable is fully inserted
- Check for damaged ribbon cable

### Can't Upload Code
- IO0 must be connected to GND during upload
- Try pressing RESET while clicking Upload
- Check RX/TX aren't swapped (RX→TX, TX→RX)
- Verify FTDI TX/RX voltage is 3.3V compatible

### Brown-out/Resets
- Use better power supply (2A+)
- Add 100μF capacitor
- Check USB cable quality
- Reduce cable length from power supply

### Button Not Working
- Check GPIO14 connection
- Verify GND connection
- Test with internal pull-up enabled

## Safety Notes

⚠️ **Important:**
- Never connect 5V directly to GPIO pins (they are 3.3V)
- Use proper polarity for capacitors and power
- Don't short 5V to GND
- Ensure stable power before camera operations

## Testing Setup

1. **Power test:** LED should light up
2. **Upload test:** Upload simple blink sketch
3. **Camera test:** Upload camera example from ESP32 examples
4. **Bluetooth test:** Upload KodakStepTest.ino
5. **Full test:** Upload KodakStepPrint.ino

---

For software setup and usage, see [README.md](README.md)
