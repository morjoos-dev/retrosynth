@echo off
rem ---------------------------------------------------------------------------
rem  retrosynth studio - Windows launcher. Just double-click this file.
rem  The first time it creates a private Python environment in the ".venv"
rem  folder and installs retrosynth into it (needs internet, takes 1-2 minutes).
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"
title retrosynth studio

if exist ".venv\.installed" goto run

echo.
echo   retrosynth - first-time setup (only once, 1-2 minutes)
echo   ------------------------------------------------------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY goto nopython

if exist ".venv" rmdir /s /q ".venv"
echo   Creating the Python environment...
%PY% -m venv .venv || goto fail
echo   Installing retrosynth and its libraries...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade pip
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -e . || goto fail
echo ok> ".venv\.installed"
echo   Done.

:run
echo.
echo   Starting retrosynth studio in your browser...
echo   Keep this window open while you use it. Close it (or press Ctrl+C) to stop.
echo.
".venv\Scripts\python.exe" -m retrosynth studio %*
goto end

:nopython
echo.
echo   Python 3.10 or newer was not found on this computer.
echo.
echo   Install it from https://www.python.org/downloads/
echo   (on the first screen tick "Add python.exe to PATH"),
echo   or open PowerShell and run:   winget install Python.Python.3.12
echo.
echo   Then double-click this file again.
goto end

:fail
echo.
echo   Setup failed: read the messages above.
echo   See docs\INSTALL.md (section "Troubleshooting") for help.
if exist ".venv" rmdir /s /q ".venv"

:end
echo.
pause
