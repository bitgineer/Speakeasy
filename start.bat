@echo off
REM Alias for install.bat. Sets up anything missing, then starts the app.
call "%~dp0install.bat" --launch %*
