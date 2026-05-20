@echo off
title AlphaPilot Pro V9.1 - Lazy Mode Quick Start
color 0A

echo.
echo ================================================================================
echo    AlphaPilot Pro V9.1 - Lazy Mode: Replay All Historical Signals
echo ================================================================================
echo.

:: ==================== Environment Check ====================
echo [1/5] Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo OK: Python environment ready.

echo.
echo [2/5] Checking virtual environment...
if not exist "quant_env\Scripts\python.exe" (
    echo WARNING: Virtual environment not found. Creating now...
    python -m venv quant_env
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo OK: Virtual environment created successfully.
) else (
    echo OK: Virtual environment already exists.
)

echo.
echo [3/5] Activating virtual environment and installing dependencies...
call quant_env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Check critical dependencies
python -c "import gm" 2>nul
if %errorlevel% neq 0 (
    echo Installing Goldminer SDK...
    pip install gm -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import watchdog" 2>nul
if %errorlevel% neq 0 (
    echo Installing watchdog...
    pip install watchdog -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import dotenv" 2>nul
if %errorlevel% neq 0 (
    echo Installing python-dotenv...
    pip install python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo OK: Dependencies check completed.

:: ==================== Configuration Confirmation ====================
echo.
echo [4/5] Configuration confirmation...
echo.
echo Source Directory: D:\mpython\signals\processed
echo Target Directory: D:\main_data\signals
echo Signal Interval: 5 seconds (modify in lazy_replay_all.py)
echo Max Files: All (modify in lazy_replay_all.py)
echo.

:: Check if source directory has files
if not exist "D:\mpython\signals\processed\*.txt" (
    echo ERROR: No signal files found in source directory.
    echo Please ensure D:\mpython\signals\processed contains .txt files.
    pause
    exit /b 1
)

:: Count files
for /f %%i in ('dir /b "D:\mpython\signals\processed\*.txt" ^| find /c /v ""') do set FILE_COUNT=%%i
echo Found %FILE_COUNT% historical signal files.

:: ==================== Clear Sync History (Optional) ====================
echo.
set /p CLEAR_HISTORY="Clear sync history? (y/n, default n): "
if /i "%CLEAR_HISTORY%"=="y" (
    if exist "signals\.sync_history.json" (
        del "signals\.sync_history.json"
        echo OK: Sync history cleared.
    ) else (
        echo INFO: Sync history file does not exist.
    )
) else (
    echo INFO: Keeping sync history. Already processed files will be skipped.
)

:: ==================== Start Lazy Mode ====================
echo.
echo [5/5] Starting Lazy Mode...
echo.
echo ================================================================================
echo    Ready to replay all historical signals
echo    TIP: Press Ctrl+C to interrupt at any time
echo ================================================================================
echo.

pause

echo.
echo Starting execution...
echo.

python lazy_replay_all.py

:: ==================== Completion Message ====================
echo.
echo ================================================================================
echo    Lazy Mode Execution Completed!
echo ================================================================================
echo.
echo Next Steps:
echo    1. Check Goldminer terminal logs to confirm strategy execution
echo    2. To adjust parameters, edit configuration section in lazy_replay_all.py
echo    3. Run this script again to continue testing
echo.
echo Documentation: LAZY_MODE_GUIDE.md
echo.

pause
