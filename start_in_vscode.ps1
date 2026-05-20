<#
.SYNOPSIS
    AlphaPilot Pro - VSCode一键启动脚本

.DESCRIPTION
    在VSCode中直接运行完整的AlphaPilot Pro量化策略
    
    功能:
    1. 检查Python环境和依赖
    2. 验证配置文件
    3. 启动策略（实盘/模拟模式）
    4. 监控运行状态
    
    使用方法:
    .\start_in_vscode.ps1
    
    参数:
    -Mode: 运行模式 (live/backtest)，默认live

.NOTES
    Alphapilot智能体团队
    作者: 梁子羿、侯沣睿、梁茹真
    邮箱: 497720537@qq.com | 电话: 13392077558
    
    重要提示:
    - 策略ID必须与掘金终端中创建的策略实例一致
    - 当前使用: a62d366d-3c78-11f1-8563-1ece51d839d6
    - 必须激活quant_env虚拟环境
#>

param(
    [ValidateSet('live', 'backtest')]
    [string]$Mode = 'live'
)

# 设置编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🚀 AlphaPilot Pro - VSCode一键启动" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 配置信息
$PROJECT_ROOT = "D:\mpython"
$MAIN_SCRIPT = Join-Path $PROJECT_ROOT "main.py"
$VENV_ACTIVATE = Join-Path $PROJECT_ROOT "quant_env\Scripts\Activate.ps1"
$STRATEGY_ID = "a62d366d-3c78-11f1-8563-1ece51d839d6"

Write-Host "`n📂 [配置信息]" -ForegroundColor Yellow
Write-Host "   项目根目录: $PROJECT_ROOT" -ForegroundColor Gray
Write-Host "   策略文件: $MAIN_SCRIPT" -ForegroundColor Gray
Write-Host "   策略ID: $STRATEGY_ID" -ForegroundColor Gray
Write-Host "   运行模式: $Mode" -ForegroundColor Gray

# 步骤1: 检查虚拟环境
Write-Host "`n🔍 [步骤1] 检查虚拟环境" -ForegroundColor Yellow

if (-not (Test-Path $VENV_ACTIVATE)) {
    Write-Host "   ❌ 虚拟环境不存在: $VENV_ACTIVATE" -ForegroundColor Red
    Write-Host "   💡 请先创建虚拟环境: python -m venv quant_env" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✅ 虚拟环境存在" -ForegroundColor Green

# 步骤2: 激活虚拟环境
Write-Host "`n🔧 [步骤2] 激活虚拟环境" -ForegroundColor Yellow

try {
    & $VENV_ACTIVATE
    Write-Host "   ✅ 虚拟环境已激活" -ForegroundColor Green
    Write-Host "   Python路径: $(Get-Command python | Select-Object -ExpandProperty Source)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ 激活虚拟环境失败: $_" -ForegroundColor Red
    exit 1
}

# 步骤3: 检查依赖
Write-Host "`n📦 [步骤3] 检查Python依赖" -ForegroundColor Yellow

$required_modules = @('gm', 'dotenv', 'watchdog')
$missing_modules = @()

foreach ($module in $required_modules) {
    try {
        python -c "import $module" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $module" -ForegroundColor Green
        } else {
            $missing_modules += $module
            Write-Host "   ❌ $module (未安装)" -ForegroundColor Red
        }
    } catch {
        $missing_modules += $module
        Write-Host "   ❌ $module (未安装)" -ForegroundColor Red
    }
}

if ($missing_modules.Count -gt 0) {
    Write-Host "`n   ⚠️  缺少依赖包: $($missing_modules -join ', ')" -ForegroundColor Yellow
    $install = Read-Host "   是否现在安装? (Y/N)"
    if ($install -eq 'Y' -or $install -eq 'y') {
        Write-Host "`n   正在安装依赖..." -ForegroundColor Cyan
        pip install gm python-dotenv watchdog
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ❌ 依赖安装失败" -ForegroundColor Red
            exit 1
        }
        Write-Host "   ✅ 依赖安装成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 依赖不完整，无法启动" -ForegroundColor Red
        exit 1
    }
}

# 步骤4: 检查配置文件
Write-Host "`n📋 [步骤4] 检查配置文件" -ForegroundColor Yellow

$env_file = Join-Path $PROJECT_ROOT ".env"
if (-not (Test-Path $env_file)) {
    Write-Host "   ❌ 配置文件不存在: $env_file" -ForegroundColor Red
    Write-Host "   💡 请从 .env.example 复制并填写配置" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✅ 配置文件存在" -ForegroundColor Green

# 检查.env中的关键配置
$env_content = Get-Content $env_file -Raw
if ($env_content -notmatch 'GM_TOKEN=') {
    Write-Host "   ⚠️  .env中缺少 GM_TOKEN 配置" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ GM_TOKEN 已配置" -ForegroundColor Green
}

if ($env_content -notmatch 'GM_ACCOUNT_ID=') {
    Write-Host "   ⚠️  .env中缺少 GM_ACCOUNT_ID 配置" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ GM_ACCOUNT_ID 已配置" -ForegroundColor Green
}

# 步骤5: 检查主策略文件
Write-Host "`n📄 [步骤5] 检查策略文件" -ForegroundColor Yellow

if (-not (Test-Path $MAIN_SCRIPT)) {
    Write-Host "   ❌ 策略文件不存在: $MAIN_SCRIPT" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 策略文件存在" -ForegroundColor Green

# 检查策略ID是否正确
$content = Get-Content $MAIN_SCRIPT -Raw
if ($content -match $STRATEGY_ID) {
    Write-Host "   ✅ 策略ID已配置: $STRATEGY_ID" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  策略文件中未找到策略ID: $STRATEGY_ID" -ForegroundColor Yellow
    Write-Host "   💡 请确保 run() 函数中的 strategy_id 正确" -ForegroundColor Gray
}

# 步骤6: 显示启动信息
Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "✅ 所有检查通过！准备启动策略" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n📊 [启动信息]" -ForegroundColor Yellow
Write-Host "   策略ID: $STRATEGY_ID" -ForegroundColor Cyan
Write-Host "   运行模式: $($Mode.ToUpper())" -ForegroundColor Cyan

if ($Mode -eq 'live') {
    Write-Host "`n⚠️  [重要提示]" -ForegroundColor Red
    Write-Host "   实盘/模拟模式需要注意:" -ForegroundColor White
    Write-Host "   1. 掘金终端必须已打开" -ForegroundColor Gray
    Write-Host "   2. 账户必须已连接（状态: 已连接）" -ForegroundColor Gray
    Write-Host "   3. 当前使用账户ID:" -ForegroundColor Gray
    Write-Host "      1103758f-395a-11f1-aecc-00163e022aa6" -ForegroundColor Cyan
    Write-Host "   4. 策略在交易时段（09:30-11:30, 13:00-15:00）才会执行交易" -ForegroundColor Gray
} else {
    Write-Host "`n💡 [回测模式]" -ForegroundColor Cyan
    Write-Host "   回测不需要连接掘金终端账户" -ForegroundColor Gray
}

Write-Host "`n🚀 [启动策略]" -ForegroundColor Yellow
Write-Host "   正在启动 AlphaPilot Pro..." -ForegroundColor Cyan
Write-Host "   按 Ctrl+C 停止策略" -ForegroundColor Gray
Write-Host ""

# 启动策略
try {
    python $MAIN_SCRIPT --mode $Mode
} catch {
    Write-Host "`n❌ 策略启动失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "✅ 策略已停止" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
