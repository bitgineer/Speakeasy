@echo off
setlocal
cd /d "%~dp0"

REM SpeakEasy bootstrap for Windows.
REM Ensures uv and Python 3.12 exist, then hands off to install.py.

where uv >nul 2>&1
if errorlevel 1 (
  echo Installing uv...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%LOCALAPPDATA%\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

uv python install 3.12
if errorlevel 1 (
  echo Failed to prepare Python 3.12 with uv.
  pause
  exit /b 1
)

for /f "delims=" %%i in ('uv python find 3.12') do set "SPEAKEASY_PY=%%i"
if not defined SPEAKEASY_PY (
  echo Could not locate the Python 3.12 interpreter managed by uv.
  pause
  exit /b 1
)

"%SPEAKEASY_PY%" "%~dp0install.py" %*
if errorlevel 1 (
  echo.
  echo Setup failed. Review the messages above.
  pause
  exit /b 1
)
