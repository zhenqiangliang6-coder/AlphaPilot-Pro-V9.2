Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AlphaPilot Pro V9.2 - Quick Push" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

git status
Write-Host ""

$commit_msg = Read-Host "Enter commit message"

if ([string]::IsNullOrWhiteSpace($commit_msg)) {
    Write-Host "Error: Commit message cannot be empty!" -ForegroundColor Red
    exit 1
}

git add .
git commit -m $commit_msg
git push

Write-Host ""
Write-Host "Success! Pushed to GitHub." -ForegroundColor Green
