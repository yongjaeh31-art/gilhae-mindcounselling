@echo off
cd /d "%~dp0"

echo =====================================
echo Gilhae homepage server
echo =====================================
echo.

set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if %errorlevel%==0 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    set "PYTHON_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

if not exist "%PYTHON_CMD%" if not "%PYTHON_CMD%"=="py" if not "%PYTHON_CMD%"=="python" (
    echo Python is not installed or is not available from this terminal.
    echo Please install Python 3, then run this file again.
    pause
    exit /b 1
)

echo.
echo Starting server...
echo Open this address in your browser:
echo http://127.0.0.1:8765
echo.
echo Do not close this window while using the homepage.
echo.

echo Using Python:
echo %PYTHON_CMD%
echo.

"%PYTHON_CMD%" -u app.py

pause
