@echo off
chcp 65001 >nul
REM ============================================
REM AlphaPilot Pro V9.1 - One-Click Startup Script
REM Alphapilot AI Team
REM Author: Liang Ziyi, Hou Fengrui, Liang Ruzhen
REM ============================================

echo.
echo ================================================================
echo    AlphaPilot Pro V9.1 - One-Click Startup
echo ================================================================
echo.

REM Check Python environment
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.6+ first.
    pause
    exit /b 1
)

echo [Step 1] Checking project configuration...
if not exist "config\settings.py" (
    echo [ERROR] Configuration file not found. Please run this script from project root directory.
    pause
    exit /b 1
)

echo [Step 2] Checking source directory...
if not exist "D:\mpython\signals\processed" (
    echo [WARNING] Source directory D:\mpython\signals\processed not found.
    echo           Using default path: D:\main_data\signals\processed
    set SOURCE_DIR=D:\main_data\signals\processed
) else (
    set SOURCE_DIR=D:\mpython\signals\processed
)

echo.
echo [Step 3] Activating virtual environment...
if exist "quant_env\Scripts\activate.bat" (
    call quant_env\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARNING] Virtual environment not found, using system Python
)

echo.
echo [Step 4] Cleaning Python cache...
if exist "__pycache__" (
    rmdir /s /q "__pycache__" 2>nul
)
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
echo [OK] Cache cleaned

echo.
echo [Step 5] Starting Signal Syncer (separate window)...
start "Signal Syncer - Auto Sync Latest Signals" cmd /k "call quant_env\Scripts\activate.bat && python signal_sync_standalone.py"

echo.
echo [Waiting 3 seconds for syncer initialization...]
timeout /t 3 /nobreak >nul

echo.
echo [Step 6] Starting Main Strategy Engine (Goldminer Quant)...
start "AlphaPilot Pro - Main Strategy Engine" cmd /k "call quant_env\Scripts\activate.bat && python main.py"

echo.
echo ================================================================
echo    [SUCCESS] Two windows started!
echo ================================================================
echo.
echo    Window 1: Signal Syncer
echo      - Scans D:\mpython\signals\processed every 30 seconds
echo      - Auto copies new signals to D:\main_data\signals
echo      - Prevents duplicate processing
echo      - Pure local file operation, no Goldminer required
echo.
echo    Window 2: Main Strategy Engine
echo      - Connects to Goldminer Quant Platform
echo      - Watchdog monitors D:\main_data\signals
echo      - New signal files trigger strategy immediately
echo      - Executes trading decisions and risk control
echo.
echo    Tips:
echo      1. Place test signals in D:\mpython\signals\processed
echo      2. Observe log output in both windows
echo      3. Close any window to stop corresponding service
echo      4. Syncer runs continuously, no need to restart
echo ================================================================
echo.
echo Press any key to close this window (services will continue running)...
pause >nul