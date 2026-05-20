# -*- coding: utf-8 -*-
"""
动态止盈模块快速验证脚本（PowerShell版本）

功能：
1. 验证修复后的代码可以正常导入
2. 检查当前持仓的止盈状态
3. 输出诊断摘要

使用方法：
    .\test_take_profit_quick.ps1
"""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "动态止盈模块 - 快速验证脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 激活虚拟环境
Write-Host "[步骤1] 激活虚拟环境..." -ForegroundColor Yellow
& .\quant_env\Scripts\Activate.ps1

# 2. 运行诊断脚本
Write-Host "[步骤2] 运行诊断测试..." -ForegroundColor Yellow
python diagnose_take_profit_prefix.py

# 3. 检查日志文件（如果存在）
Write-Host ""
Write-Host "[步骤3] 检查最近的止盈日志..." -ForegroundColor Yellow
$logDir = "logs"
if (Test-Path $logDir) {
    $latestLog = Get-ChildItem -Path $logDir -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestLog) {
        Write-Host "最新日志文件: $($latestLog.Name)" -ForegroundColor Green
        Write-Host "最后修改时间: $($latestLog.LastWriteTime)" -ForegroundColor Green
        
        # 搜索止盈相关日志
        $takeProfitLogs = Select-String -Path $latestLog.FullName -Pattern "\[止盈" | Select-Object -Last 10
        if ($takeProfitLogs) {
            Write-Host ""
            Write-Host "最近10条止盈日志:" -ForegroundColor Cyan
            $takeProfitLogs | ForEach-Object {
                Write-Host $_.Line -ForegroundColor White
            }
        } else {
            Write-Host "未找到止盈相关日志（可能还未触发或未到执行时间）" -ForegroundColor Gray
        }
    } else {
        Write-Host "未找到日志文件" -ForegroundColor Gray
    }
} else {
    Write-Host "日志目录不存在" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "验证完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 下一步操作建议：" -ForegroundColor Yellow
Write-Host "1. 查看上面的诊断测试结果，确认所有测试通过" -ForegroundColor White
Write-Host "2. 检查是否有止盈日志输出" -ForegroundColor White
Write-Host "3. 如果当前时间 < 09:51，止盈不会执行（时间窗口限制）" -ForegroundColor White
Write-Host "4. 如需调整最早执行时间，修改 settings.py 中的 TAKE_PROFIT_EARLIEST_TIME" -ForegroundColor White
Write-Host ""
