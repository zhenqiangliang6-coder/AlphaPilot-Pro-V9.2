@echo off
title AlphaPilot Pro V9.1 - Multi-Account Parallel Test
color 0E

echo.
echo ================================================================================
echo    AlphaPilot Pro V9.1 - Multi-Account Parallel Test Mode
echo    Launch 3 strategies with different parameters simultaneously
echo ================================================================================
echo.

:: ==================== Environment Check ====================
if not exist "quant_env\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    pause
    exit /b 1
)

call quant_env\Scripts\activate.bat

:: ==================== Clear Sync History ====================
if exist "signals\.sync_history.json" (
    del "signals\.sync_history.json" >nul 2>&1
    echo OK: Sync history cleared.
)

echo.
echo Launching 3 simulation accounts:
echo    +---------------------------------------------+
echo    | Account A: Volume Ratio Threshold 2.0       |
echo    | Account B: Volume Ratio Threshold 3.0       |
echo    | Account C: Volume Ratio Threshold 4.0       |
echo    +---------------------------------------------+
echo.
echo NOTE: Please ensure 3 different simulation accounts are created in Goldminer terminal.
echo.

pause

echo.
echo Launching 3 test windows...
echo.

:: Launch Account A - Conservative Strategy (Threshold 2.0)
start "Account A - Conservative (Threshold 2.0)" cmd /k "cd /d %~dp0 && set VOLUME_RATIO_THRESHOLD=2.0 && python lazy_replay_all.py"

:: Wait 1 second to avoid conflicts
timeout /t 1 /nobreak >nul

:: Launch Account B - Balanced Strategy (Threshold 3.0)
start "Account B - Balanced (Threshold 3.0)" cmd /k "cd /d %~dp0 && set VOLUME_RATIO_THRESHOLD=3.0 && python lazy_replay_all.py"

:: Wait 1 second
timeout /t 1 /nobreak >nul

:: Launch Account C - Aggressive Strategy (Threshold 4.0)
start "Account C - Aggressive (Threshold 4.0)" cmd /k "cd /d %~dp0 && set VOLUME_RATIO_THRESHOLD=4.0 && python lazy_replay_all.py"

echo.
echo ================================================================================
echo    3 test windows launched successfully!
echo ================================================================================
echo.
echo Operation Guide:
echo    1. Each window runs replay test independently
echo    2. Observe buy count, success rate, and profit in each window
echo    3. Compare results and select the best parameter
echo    4. Close any window to stop that account's test
echo.
echo Suggested Metrics:
echo    - Number of buy signals (more = more aggressive)
echo    - Trading success rate (higher = more stable)
echo    - Cumulative profit rate (final goal)
echo.
echo TIP: 
echo    - To adjust parameters, modify VOLUME_RATIO_THRESHOLD values above
echo    - To add more accounts, copy start command with different parameters
echo.

pause
