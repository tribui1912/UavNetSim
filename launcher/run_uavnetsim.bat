@echo off
REM UavNetSim Launcher for Windows
REM This script provides a menu-driven interface to run tests, simulations, and experiments

setlocal enabledelayedexpansion

:HEADER
cls
echo ========================================
echo    UavNetSim - UAV Network Simulator
echo ========================================
echo.

REM Check Python installation
:CHECK_PYTHON
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.12+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
python --version
echo [OK] Python is installed
echo.

REM Check uv installation
:CHECK_UV
echo [2/3] Checking uv installation...
uv --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] uv is not installed
    echo.
    echo Installing uv...
    pip install uv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install uv
        pause
        exit /b 1
    )
    echo [OK] uv installed successfully
) else (
    uv --version
    echo [OK] uv is installed
)
echo.

REM Check/Create virtual environment
:CHECK_VENV
echo [3/3] Checking virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)
echo.

REM Check dependencies
echo Checking dependencies...
uv pip list | findstr /C:"simpy" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Dependencies not installed
    echo Installing dependencies from requirements.txt...
    uv pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies are installed
)
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
timeout /t 2 >nul

:MENU
cls
echo ========================================
echo    UavNetSim - Main Menu
echo ========================================
echo.
echo Please select an option:
echo.
echo [1] Run Main Simulation (with GUI)
echo [2] Run All Tests
echo [3] Run Individual Test
echo [4] Run All Experiments (20-35 min)
echo [5] Run Individual Experiment
echo [6] Check System Status
echo [7] Install/Update Dependencies
echo [8] View Quick Reference
echo [9] Exit
echo.
echo ========================================
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto RUN_MAIN
if "%choice%"=="2" goto RUN_ALL_TESTS
if "%choice%"=="3" goto RUN_INDIVIDUAL_TEST
if "%choice%"=="4" goto RUN_ALL_EXPERIMENTS
if "%choice%"=="5" goto RUN_INDIVIDUAL_EXPERIMENT
if "%choice%"=="6" goto CHECK_STATUS
if "%choice%"=="7" goto INSTALL_DEPS
if "%choice%"=="8" goto VIEW_REFERENCE
if "%choice%"=="9" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:RUN_MAIN
cls
echo ========================================
echo    Running Main Simulation
echo ========================================
echo.
echo Starting UavNetSim with GUI...
echo (Press Ctrl+C to stop)
echo.
uv run main.py
echo.
echo Simulation ended.
pause
goto MENU

:RUN_ALL_TESTS
cls
echo ========================================
echo    Running All Tests
echo ========================================
echo.
uv run tests/run_all_tests.py
echo.
echo Tests completed.
pause
goto MENU

:RUN_INDIVIDUAL_TEST
cls
echo ========================================
echo    Run Individual Test
echo ========================================
echo.
echo [1] Sanity Test (~3 seconds)
echo [2] Formation Logic Test (~35 seconds)
echo [3] GUI Test (~1 second)
echo [4] Back to Main Menu
echo.
set /p test_choice="Select test (1-4): "

if "%test_choice%"=="1" (
    echo.
    echo Running Sanity Test...
    uv run tests/test_sanity.py
)
if "%test_choice%"=="2" (
    echo.
    echo Running Formation Logic Test...
    uv run tests/test_formation_logic.py
)
if "%test_choice%"=="3" (
    echo.
    echo Running GUI Test...
    uv run tests/test_gui.py
)
if "%test_choice%"=="4" goto MENU

echo.
pause
goto MENU

:RUN_ALL_EXPERIMENTS
cls
echo ========================================
echo    Running All Experiments
echo ========================================
echo.
echo WARNING: This will take 20-35 minutes!
echo.
echo Experiments to run:
echo  1. Mobility vs Latency (~5-10 min)
echo  2. Energy-Throughput (~5-10 min)
echo  3. Formation Transition (~10-15 min)
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

echo.
echo Starting experiments...
echo Results will be saved as CSV files.
echo.
uv run experiment_runner.py
echo.
echo ========================================
echo Experiments completed!
echo ========================================
echo.
echo Output files:
echo  - experiment_1_mobility_vs_latency.csv
echo  - experiment_2_energy_throughput.csv
echo  - experiment_3_formation_transition.csv
echo.
pause
goto MENU

:RUN_INDIVIDUAL_EXPERIMENT
cls
echo ========================================
echo    Run Individual Experiment
echo ========================================
echo.
echo [1] Experiment 1: Mobility vs Latency (~5-10 min)
echo [2] Experiment 2: Energy-Throughput (~5-10 min)
echo [3] Experiment 3: Formation Transition (~10-15 min)
echo [4] Back to Main Menu
echo.
set /p exp_choice="Select experiment (1-4): "

if "%exp_choice%"=="1" (
    echo.
    echo Running Experiment 1: Mobility vs Latency...
    uv run python -c "from experiment_runner import run_experiment_1_mobility_vs_latency; run_experiment_1_mobility_vs_latency()"
    echo.
    echo Results saved to: experiment_1_mobility_vs_latency.csv
)
if "%exp_choice%"=="2" (
    echo.
    echo Running Experiment 2: Energy-Throughput...
    uv run python -c "from experiment_runner import run_experiment_2_energy_throughput; run_experiment_2_energy_throughput()"
    echo.
    echo Results saved to: experiment_2_energy_throughput.csv
)
if "%exp_choice%"=="3" (
    echo.
    echo Running Experiment 3: Formation Transition...
    uv run python -c "from experiment_runner import run_experiment_3_formation_transition; run_experiment_3_formation_transition()"
    echo.
    echo Results saved to: experiment_3_formation_transition.csv
)
if "%exp_choice%"=="4" goto MENU

echo.
pause
goto MENU

:CHECK_STATUS
cls
echo ========================================
echo    System Status Check
echo ========================================
echo.

echo Python Version:
python --version
echo.

echo uv Version:
uv --version
echo.

echo Virtual Environment:
if exist ".venv" (
    echo [OK] Virtual environment exists at .venv
) else (
    echo [WARNING] Virtual environment not found
)
echo.

echo Installed Packages:
echo --------------------
uv pip list
echo.

echo Configuration:
echo --------------------
echo Project Directory: %CD%
echo.

pause
goto MENU

:INSTALL_DEPS
cls
echo ========================================
echo    Install/Update Dependencies
echo ========================================
echo.
echo Installing dependencies from requirements.txt...
echo.
uv pip install -r requirements.txt
if %ERRORLEVEL% equ 0 (
    echo.
    echo [OK] Dependencies installed successfully
) else (
    echo.
    echo [ERROR] Failed to install dependencies
)
echo.
pause
goto MENU

:VIEW_REFERENCE
cls
echo ========================================
echo    Quick Reference
echo ========================================
echo.
if exist "QUICK_REFERENCE.md" (
    type QUICK_REFERENCE.md | more
) else (
    echo QUICK_REFERENCE.md not found
    echo.
    echo Key Commands:
    echo  - Run simulation: uv run main.py
    echo  - Run tests: uv run tests/run_all_tests.py
    echo  - Run experiments: uv run experiment_runner.py
)
echo.
pause
goto MENU

:EXIT
cls
echo ========================================
echo    UavNetSim - Goodbye!
echo ========================================
echo.
echo Thank you for using UavNetSim
echo.
timeout /t 2 >nul
exit /b 0

