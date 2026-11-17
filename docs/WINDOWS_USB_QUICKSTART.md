# Windows USB quick start

1. Download the official Windows SDK Platform-Tools ZIP from
   https://developer.android.com/tools/releases/platform-tools
2. Extract it, for example to `C:\Android\platform-tools`.
3. On the phone, enable Developer options and USB debugging only for this
   supervised session. Keep the phone unlocked.
4. Connect with a known-good USB data cable and approve the RSA prompt on the
   phone only if you trust this Windows computer.
5. From the repository root, run:

   ```powershell
   .\scripts\vx-android-inspect.ps1 -Serial "YOUR_EXACT_ADB_SERIAL" -AdbPath "C:\Android\platform-tools\adb.exe"
   ```

6. The script verifies the selected serial and calls the VX read-only inspector.
   It does not install packages, reboot, change settings, transfer files, or root
   the phone.

If the device is `unauthorized`, unlock it and accept the RSA prompt. If it is
missing, try another USB data cable/port and install the OEM ADB USB driver if
Windows requires one. When finished, disable USB debugging and revoke this
computer's debugging authorization if it should no longer be trusted.

The real handset has not been connected or inspected by this repository change.
