# WSL2 Options for Kodak Step Printer

## TL;DR: WSL2 Bluetooth is Possible but Complex

**Short Answer**: Yes, WSL2 can work, but it requires either:
1. **USB Bluetooth adapter passthrough** (easier, requires external adapter)
2. **Custom kernel compilation** (complex, works with built-in Bluetooth)

## The Problem on Windows

Windows enforces **Secure Simple Pairing (SSP)** mode and provides no way to disable it for legacy Bluetooth devices like the Kodak Step printer. This is why the connection keeps flickering - Windows can't properly negotiate with the printer's legacy pairing requirements.

**Sources:**
- [Microsoft Q&A: Cannot disable SSP on Windows](https://learn.microsoft.com/en-us/answers/questions/2636358/disable-bluetooth-secure-simple-pairing-(ssp))
- [Windows Bluetooth Registry Entries](https://learn.microsoft.com/en-us/windows-hardware/drivers/bluetooth/bluetooth-registry-entries) (no SSP disable option)

---

## Option 1: USB Bluetooth Adapter Passthrough (RECOMMENDED)

### What You Need:
- External USB Bluetooth adapter (~$10-20)
- usbipd-win tool
- BlueZ in WSL2

### Pros:
✅ No kernel compilation needed
✅ Full Bluetooth control in Linux
✅ Can disable SSP mode easily
✅ Well-documented process

### Cons:
❌ Requires purchasing external Bluetooth adapter
❌ Need to detach/reattach for Windows use

### Setup Steps:

#### 1. Install usbipd-win (Windows)

**PowerShell (as Administrator):**
```powershell
winget install --interactive --exact dorssel.usbipd-win
```

**Or download from:** [usbipd-win releases](https://github.com/dorssel/usbipd-win/releases)

#### 2. Install Linux Tools (WSL2)

```bash
sudo apt update
sudo apt install linux-tools-generic hwdata bluez python3-pip
pip3 install PyBluez loguru pillow pyserial
```

#### 3. Attach Bluetooth Adapter

**Windows PowerShell (Administrator):**
```powershell
# List USB devices
usbipd list

# Find your Bluetooth adapter (look for "Bluetooth" in description)
# Note the BUSID (e.g., 2-4)

# Bind it (one-time, persists across reboots)
usbipd bind --busid <BUSID>

# Attach to WSL2
usbipd attach --wsl --busid <BUSID>
```

**Verify in WSL2:**
```bash
lsusb  # Should show your Bluetooth adapter
hciconfig  # Should show hci0
```

#### 4. Disable SSP Mode (WSL2)

```bash
# Enable legacy pairing mode
sudo hciconfig hci0 sspmode 0

# Start Bluetooth service
sudo service bluetooth start

# Use bluetoothctl to pair
bluetoothctl
```

#### 5. Pair and Test

**In bluetoothctl:**
```
agent on
default-agent
scan on
# Wait for "KODAK STEP" to appear
pair A4:62:DF:A9:72:D4
trust A4:62:DF:A9:72:D4
connect A4:62:DF:A9:72:D4
```

#### 6. Find the RFCOMM Device

```bash
# After pairing, bind to SPP
sudo rfcomm bind 0 A4:62:DF:A9:72:D4 1

# Device should appear as /dev/rfcomm0
ls -la /dev/rfcomm0
```

#### 7. Test the Protocol

Copy the Python files to WSL2 and run:
```bash
# Copy files
cp /mnt/c/Users/benhe/Projects/Code/bt-printer/*.py .

# Edit kodak_prinics_protocol.py to use /dev/rfcomm0
# Change: port='COM6' to port='/dev/rfcomm0'

python3 kodak_prinics_protocol.py
```

**Sources:**
- [Microsoft Docs: Connect USB to WSL](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)
- [usbipd-win WSL Support](https://github.com/dorssel/usbipd-win/wiki/WSL-support)
- [Bluetooth Adapter in WSL Discussion](https://github.com/dorssel/usbipd-win/discussions/310)

---

## Option 2: Custom Kernel with Built-in Bluetooth (ADVANCED)

### What You Need:
- Time and patience
- Kernel compilation experience helpful

### Pros:
✅ Uses your built-in Bluetooth
✅ No external hardware needed

### Cons:
❌ Very complex setup
❌ Requires kernel compilation
❌ May need to rebuild on WSL updates
❌ Built-in Bluetooth passthrough is tricky

### Overview:
You need to compile a custom WSL2 kernel with Bluetooth support enabled, then use usbipd-win to passthrough your built-in Bluetooth controller.

**This is NOT recommended** unless you're experienced with kernel compilation. The USB Bluetooth adapter approach (Option 1) is much simpler.

**Sources:**
- [WSL2 Kernel Bluetooth Support Issue](https://github.com/microsoft/WSL/issues/12234)
- [Bluetooth Support in WSL Issue #4960](https://github.com/microsoft/WSL/issues/4960)

---

## Option 3: Just Use a Raspberry Pi (EASIEST)

### What You Need:
- Raspberry Pi (any model with Bluetooth)
- MicroSD card
- Power supply

### Pros:
✅ Works out of the box
✅ Original code was tested on RPi
✅ Full Bluetooth control
✅ No Windows issues

### Cons:
❌ Requires separate hardware
❌ Need to set up separate system

### Setup:
1. Flash Raspberry Pi OS
2. Copy the code over
3. Follow the original README instructions:
   ```bash
   sudo apt install bluetooth bluez libbluetooth-dev
   pip install -r requirements.txt
   pip install git+https://github.com/pybluez/pybluez.git#egg=pybluez
   sudo hciconfig 0 sspmode 0
   bluetoothctl  # Pair the printer
   ```
4. Run the code

---

## Option 4: Dual Boot Linux (NUCLEAR OPTION)

If you have a spare partition or want to try Linux:
- Install Ubuntu 24.04 alongside Windows
- Full native Bluetooth support
- No WSL limitations

---

## Recommendation

**For testing the Kodak/Prinics protocol:**

1. **Quickest**: Buy a $15 USB Bluetooth adapter and use Option 1
2. **If you have RPi**: Use Option 3
3. **If you're determined to use Windows native**: Continue with the current approach, but you'll need to deal with the flickering connection

## What We've Achieved So Far

✅ Identified COM6 as the correct port
✅ Confirmed the printer accepts data on COM6
✅ Found the actual Kodak/Prinics Zink protocol (not Canon Ivy 2)
✅ Implemented the correct protocol in `kodak_prinics_protocol.py`
✅ Identified Windows SSP as the blocking issue

## Next Steps

**If using WSL2 + USB Bluetooth:**
1. Get external USB Bluetooth adapter
2. Follow Option 1 steps above
3. Test with `kodak_prinics_protocol.py` (modified for `/dev/rfcomm0`)

**If sticking with Windows:**
1. Keep printer connected in Windows Bluetooth settings
2. Run `python kodak_prinics_protocol.py` immediately when connected
3. Race against the timeout window
4. May need to try multiple times to catch it

---

## Files Ready for Testing

| File | Purpose |
|------|---------|
| `kodak_prinics_protocol.py` | Correct Kodak/Prinics protocol implementation |
| `test_kodak_serial.py` | Test script for Windows COM ports |
| `find_kodak_port.py` | Auto-detect working COM port |

All code is ready - we just need stable Bluetooth connectivity!
