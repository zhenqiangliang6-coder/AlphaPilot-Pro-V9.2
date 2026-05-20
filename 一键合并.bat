@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Stock Config Merger Tool v1.0
echo   Merge qmt_delay_config into stock_personalities
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python first.
    pause
    exit /b 1
)

echo [INFO] Starting merge process...
echo.

REM Execute the merge script
python "%~dp0merge_stock_configs.py"
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% equ 0 (
    echo ========================================
    echo   Merge completed successfully!
    echo ========================================
) else (
    echo ========================================
    echo   Merge failed! Please check errors above.
    echo ========================================
)

echo.
pause
