@echo off
chcp 65001 >nul
echo ========================================
echo   AlphaPilot Pro V9.2 - Quick Push
echo ========================================
echo.

git status
echo.
set /p commit_msg="Enter commit message: "

if "%commit_msg%"=="" (
    echo Error: Commit message cannot be empty!
    pause
    exit /b 1
)

git add .
git commit -m "%commit_msg%"
git push

echo.
echo Success! Pushed to GitHub.
pause
