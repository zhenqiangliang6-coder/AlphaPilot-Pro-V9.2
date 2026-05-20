Write-Host "========================================"
Write-Host "AlphaPilot Pro Cleanup Tool (Safe Version)"
Write-Host "========================================"
Write-Host ""

$filesToDelete = @(
    "AlphaPilot_V8.8.py",

    # problematic filenames replaced with wildcard
    "1.0*",
    "2.0*",
    "david.py",
    "dir",

    "AUCTION_STRATEGY_FIX.md",
    "DATA_DIR_PATH_FIX.md",
    "DELAYED_STRATEGY_CODE_MATCH_FIX.md",
    "DELAYED_STRATEGY_FIX.md",
    "DYNAMIC_STOP_LOSS.md",
    "FIX_SUMMARY.md",
    "LISTENER_PATH_FIX.md",
    "LOG_SYSTEM_GUIDE.md",
    "MIGRATION_COMPLETE.md",
    "MIGRATION_GUIDE.md",
    "PATH_CONFIG.md",
    "PERFORMANCE_ANALYSIS.md",
    "PROJECT_DELIVERY.md",
    "QQ_EMAIL_SETUP.md",
    "QUICK_REF_STOP_LOSS.md",
    "QUICK_START.md",
    "SIGNAL_AUTO_CONVERT_FIX.md",
    "SIGNAL_CONTINUOUS_READ_FIX.md",
    "SIGNAL_READ_DEBUG.md",
    "TESTING.md",

    "pythonbalance.py",
    "jp.py",
    "yesterday_holdings.json"
)

$deletedCount = 0
$notFoundCount = 0

Write-Host "[START] Scanning files..."
Write-Host ""

foreach ($file in $filesToDelete) {
    $matches = Get-ChildItem -Path . -Filter $file -ErrorAction SilentlyContinue
    if ($matches) {
        foreach ($m in $matches) {
            try {
                Remove-Item -Path $m.FullName -Force -ErrorAction Stop
                Write-Host "[DELETED] $($m.Name)"
                $deletedCount++
            } catch {
                Write-Host "[FAILED] $($m.Name) - $_"
            }
        }
    } else {
        Write-Host "[NOT FOUND] $file"
        $notFoundCount++
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "[FINISHED]"
Write-Host "  Deleted: $deletedCount"
Write-Host "  Not Found: $notFoundCount"
Write-Host "========================================"
Write-Host ""
Write-Host "Cleanup completed."
