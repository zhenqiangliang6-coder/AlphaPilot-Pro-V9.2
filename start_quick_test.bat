@echo off
title AlphaPilot Pro - Quick Test Mode
color 0B

echo.
echo ================================================================================
echo    AlphaPilot Pro V9.1 - Quick Test Mode (Skip All Confirmations)
echo ================================================================================
echo.

:: Activate virtual environment
if exist "quant_env\Scripts\activate.bat" (
    call quant_env\Scripts\activate.bat
)

:: Clear sync history automatically
if exist "signals\.sync_history.json" (
    del "signals\.sync_history.json" >nul 2>&1
    echo OK: Sync history cleared.
)

:: Run directly
echo Starting replay of all historical signals...
echo.

python lazy_replay_all.py

echo.
echo Done!
pause
