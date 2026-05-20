# 30/68差异化止盈止损功能快速验证脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "30/68差异化策略快速验证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 清理缓存
Write-Host "[步骤1] 清理Python缓存..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__ -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "OK 缓存清理完成" -ForegroundColor Green
Write-Host ""

# 2. 运行单元测试
Write-Host "[步骤2] 运行单元测试..." -ForegroundColor Yellow
python test_3068_differentiated_strategy.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK 单元测试通过" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR 单元测试失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "验证完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "查看详细报告: DIFFERENTIATED_STRATEGY_IMPLEMENTATION_REPORT.md" -ForegroundColor White
