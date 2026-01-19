# Bluetooth Service Discovery for Kodak Step Printer
# This script attempts to find Bluetooth services for the Kodak Step

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kodak Step Bluetooth Service Discovery" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the Kodak Step device
$kodakDevice = Get-PnpDevice -Class Bluetooth | Where-Object {$_.FriendlyName -like '*KODAK*'}

if ($kodakDevice) {
    Write-Host "Found device:" -ForegroundColor Green
    Write-Host "  Name: $($kodakDevice.FriendlyName)" -ForegroundColor White
    Write-Host "  Status: $($kodakDevice.Status)" -ForegroundColor White
    Write-Host "  InstanceId: $($kodakDevice.InstanceId)" -ForegroundColor White
    Write-Host ""

    # Try to get device properties
    Write-Host "Device Properties:" -ForegroundColor Yellow
    $properties = Get-PnpDeviceProperty -InstanceId $kodakDevice.InstanceId
    $properties | Where-Object {$_.KeyName -like '*Bluetooth*' -or $_.KeyName -like '*Address*' -or $_.KeyName -like '*Service*'} | Format-Table KeyName, Data -AutoSize

    Write-Host ""
    Write-Host "All COM Ports:" -ForegroundColor Yellow
    Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID, Description | Format-Table -AutoSize

    Write-Host ""
    Write-Host "Bluetooth Device Registry Info:" -ForegroundColor Yellow

    # Try to find registry entries for Bluetooth devices
    $btRegistry = "HKLM:\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
    if (Test-Path $btRegistry) {
        Get-ChildItem $btRegistry | ForEach-Object {
            $devicePath = $_.PSPath
            $deviceName = Get-ItemProperty -Path $devicePath -Name "Name" -ErrorAction SilentlyContinue
            if ($deviceName -and $deviceName.Name -like '*KODAK*') {
                Write-Host "Found registry entry for Kodak device:"
                Get-ItemProperty -Path $devicePath | Format-List
            }
        }
    }

} else {
    Write-Host "Kodak Step printer not found in Bluetooth devices!" -ForegroundColor Red
    Write-Host ""
    Write-Host "All Bluetooth devices:" -ForegroundColor Yellow
    Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, Status | Format-Table -AutoSize
}

Write-Host ""
Write-Host "Checking if printer needs to be in pairing mode..." -ForegroundColor Yellow
Write-Host "For Zink printers, you typically need to:"
Write-Host "  1. Power on the printer"
Write-Host "  2. Press and hold the power button for 3-5 seconds"
Write-Host "  3. Wait for the LED to blink (pairing mode)"
Write-Host "  4. Then try connecting"
