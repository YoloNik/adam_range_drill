@echo off
rem Range Drill - start the server for the local Wi-Fi network (Windows).
rem First start creates a private Python environment in .venv and installs packages (needs internet once).
setlocal
cd /d "%~dp0"
title Range Drill server
chcp 65001 >nul

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python 3 is not installed.
  echo Download it from https://www.python.org/downloads/ and tick "Add python.exe to PATH" during setup.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo First start: creating the environment, this takes a minute...
  %PY% -m venv .venv
  if errorlevel 1 ( pause & exit /b 1 )
)

".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements-local.txt
if errorlevel 1 echo Warning: could not install/update packages. Trying to start anyway...

".venv\Scripts\python.exe" serve.py %*
echo.
echo Server stopped.
pause
