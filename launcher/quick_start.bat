@echo off
REM Quick Start Script - Just runs the main simulation

echo ========================================
echo    UavNetSim - Quick Start
echo ========================================
echo.

REM Navigate to root directory (one level up from launcher folder)
cd /d "%~dp0.."

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.12+ and add it to PATH
    pause
    exit /b 1
)

REM Check/Install uv
uv --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing uv...
    pip install uv
)

REM Run main simulation
echo.
echo Starting UavNetSim...
echo.
uv run main.py

pause

