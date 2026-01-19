# Force Bluetooth reconnection for Kodak Step
# This attempts to disconnect and reconnect the device

Write-Host "Kodak Step Bluetooth Reconnection Tool" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

$kodakMac = "A462DFA972D4"

Write-Host "Step 1: Checking device status..." -ForegroundColor Yellow
$device = Get-PnpDevice -Class Bluetooth | Where-Object {$_.FriendlyName -like '*KODAK*'}

if ($device) {
    Write-Host "  Found: $($device.FriendlyName)" -ForegroundColor Green
    Write-Host "  Status: $($device.Status)" -ForegroundColor White
    Write-Host ""

    # Try to disable and re-enable the device
    Write-Host "Step 2: Attempting to refresh device connection..." -ForegroundColor Yellow
    Write-Host "  This may require administrator privileges" -ForegroundColor Gray

    try {
        # Disable
        Write-Host "  Disabling device..." -ForegroundColor Gray
        Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction Stop
        Start-Sleep -Seconds 2

        # Re-enable
        Write-Host "  Re-enabling device..." -ForegroundColor Gray
        Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false -ErrorAction Stop
        Start-Sleep -Seconds 3

        Write-Host "  Device refreshed!" -ForegroundColor Green

    } catch {
        Write-Host "  Could not refresh device (may need admin rights): $_" -ForegroundColor Red
        Write-Host "  Try running PowerShell as Administrator" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Step 3: Current device status:" -ForegroundColor Yellow
    $device = Get-PnpDevice -InstanceId $device.InstanceId
    Write-Host "  Status: $($device.Status)" -ForegroundColor White

} else {
    Write-Host "Kodak Step printer not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Manual Steps:" -ForegroundColor Yellow
Write-Host "1. Make sure the Kodak Step printer is powered ON"
Write-Host "2. On the printer, press and hold power button until LED blinks"
Write-Host "3. In Windows Settings > Bluetooth, click on 'KODAK STEP'"
Write-Host "4. Click 'Connect'"
Write-Host "5. Wait for Windows to say 'Connected'"
Write-Host "6. Then try the Python script again"
