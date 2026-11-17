param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Serial,

    [string]$AdbPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($AdbPath)) {
    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    if (-not $adbCommand) {
        throw "ADB_NOT_FOUND: Download official Android SDK Platform-Tools and set -AdbPath or PATH."
    }
    $AdbPath = $adbCommand.Source
}

if (-not (Test-Path -LiteralPath $AdbPath -PathType Leaf)) {
    throw "ADB_PATH_NOT_FOUND"
}

$deviceLines = & $AdbPath devices
if ($LASTEXITCODE -ne 0) {
    throw "ADB_DEVICE_DISCOVERY_FAILED"
}

$matching = @($deviceLines | Where-Object {
    $_ -match '^\s*([^\s]+)\s+([^\s]+)' -and $Matches[1] -eq $Serial
})

if ($matching.Count -ne 1) {
    throw "DEVICE_SERIAL_NOT_FOUND_OR_AMBIGUOUS"
}

if ($matching[0] -notmatch '^\s*([^\s]+)\s+device(?:\s|$)') {
    throw "DEVICE_NOT_AUTHORIZED_OR_NOT_READY: Unlock the phone and inspect its USB debugging authorization prompt."
}

python -m vxruntime.android_adb_cli --serial $Serial --adb-path $AdbPath
if ($LASTEXITCODE -ne 0) {
    throw "VX_ANDROID_INSPECTION_FAILED"
}
