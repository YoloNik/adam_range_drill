@echo off
rem Range Drill - allow phones/computers in the local network to reach the server port.
rem Double-click it once. It asks for administrator rights automatically.
rem Optional: allow-firewall.bat 8080   (if you start the server on another port)
setlocal
set "PORT=8000"
if not "%~1"=="" set "PORT=%~1"

net session >nul 2>&1
if errorlevel 1 (
  echo Requesting administrator rights...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '%PORT%' -Verb RunAs"
  exit /b
)

netsh advfirewall firewall delete rule name="Range Drill" >nul 2>&1
netsh advfirewall firewall add rule name="Range Drill" dir=in action=allow protocol=TCP localport=%PORT% profile=private,domain
if errorlevel 1 (
  echo Could not add the firewall rule.
) else (
  echo Done: TCP port %PORT% is open for private networks.
)
echo.
echo Your network profile must be "Private", not "Public":
powershell -NoProfile -Command "Get-NetConnectionProfile | Format-Table Name, InterfaceAlias, NetworkCategory -AutoSize"
echo If it says Public: Settings - Network and Internet - Wi-Fi - your network - Network profile type - Private.
pause
