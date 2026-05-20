# AlphaPilot Pro V9.2 - Quick Start Guide / 快速启动指南

## 🚀 One-Click Startup (Recommended) / 一键启动 (推荐)

### Method 1: Double-click (Easiest) / 方式1: 双击运行 (最简单)

Double-click this file in Windows Explorer:
在Windows资源管理器中双击此文件:
```
start_with_sync.bat
```

### Method 2: Command Line / 方式2: 命令行运行

Run in CMD or PowerShell:
在CMD或PowerShell中运行:
```bash
start_with_sync.bat
```

### What It Does / 脚本自动完成以下操作

1. ✅ Check Python environment / 检查Python环境
2. ✅ Clean Python cache files / 清理Python缓存文件
3. ✅ Start **Signal Syncer** (separate window) / 启动**信号同步器**(独立窗口)
4. ✅ Wait 3 seconds for initialization / 等待3秒初始化
5. ✅ Start **Main Strategy Engine** (another window) / 启动**主策略引擎**(另一窗口)

---

## 📂 Two Windows Will Open / 两个窗口的功能

### Window 1: Signal Syncer / 窗口1: 信号同步器

**Window Title**: `Signal Syncer - Auto Sync Latest Signals`
**窗口标题**: `Signal Syncer - Auto Sync Latest Signals`

**Functionality / 功能**:
- Scans `D:\mpython\signals\processed` directory every 30 seconds
- 每30秒扫描 `D:\mpython\signals\processed` 目录
- Automatically copies new signal files to `D:\main_data\signals`
- 自动复制新信号文件到 `D:\main_data\signals`
- Prevents duplicate processing of the same file
- 防止重复处理同一文件
- **Pure local file operations, no Juejin environment required**
- **纯本地文件操作,无需掘金环境**

### Window 2: Main Strategy Engine / 窗口2: 主策略引擎

**Window Title**: `AlphaPilot Pro - Main Strategy Engine`
**窗口标题**: `AlphaPilot Pro - Main Strategy Engine`

**Functionality / 功能**:
- Connects to Juejin Quantitative Platform
- 连接掘金量化平台
- Watchdog monitors `D:\main_data\signals` directory
- Watchdog监听 `D:\main_data\signals` 目录
- Triggers strategy processing immediately upon new signal files
- 新信号文件立即触发策略处理
- Executes trading decisions and risk control logic
- 执行交易决策和风控逻辑
- **Requires Juejin terminal to be running and logged in**
- **需要掘金终端运行并登录**

---

## 📁 Directory Structure / 目录结构

```
D:\mpython\signals\processed\          ← Source directory (external signal archive) / 源目录(外部信号归档)
├── signal_batch_20260426_163619_*.txt  ← Place test signal files here / 在此放入测试信号文件
└── ...

D:\main_data\signals\                   ← Target directory (strategy monitoring) / 目标目录(策略监听)
├── signal_batch_20260426_163619_*.txt  ← Synced files trigger strategy / 同步过来的文件触发策略
├── .sync_history.json                  ← Sync history (prevent duplicates) / 同步历史(防重复)
└── processed/                          ← Processed signal archive / 已处理信号归档
```

---

## 💡 Usage Workflow / 使用流程

### Step-by-Step / 步骤说明

#### 1️⃣ Prepare Test Signal / 准备测试信号

Place signal file in source directory:
在源目录放入信号文件:
```
D:\mpython\signals\processed\signal_batch_YYYYMMDD_HHMMSS_*.txt
```

**Filename Format Requirements / 文件名格式要求**:
- ✅ Correct / 正确: `signal_batch_20260426_143000_123456.txt`
- ❌ Incorrect / 错误: `test.txt`, `signal.json`

#### 2️⃣ Run Startup Script / 运行启动脚本

```bash
start_with_sync.bat
```

#### 3️⃣ Observe Logs / 观察日志输出

**Syncer Window Logs / 同步器窗口日志**:
```
======================================================================
🔄 AlphaPilot Pro - Signal File Syncer (Standalone Mode)
🔄 AlphaPilot Pro - 信号文件同步器(独立运行模式)
======================================================================
[Configuration] Source directory: D:\mpython\signals\processed
[配置] 源目录: D:\mpython\signals\processed
[Configuration] Target directory: D:\main_data\signals
[配置] 目标目录: D:\main_data\signals
[Configuration] Sync interval: 30 seconds
[配置] 同步间隔: 30秒

[Syncer] Initialization complete
[同步器] 初始化完成
  Files synced: 3
  已同步文件数: 3

🚀 [Start Sync] Syncing latest signal files...
🚀 [启动同步] 同步最新信号文件...
[Syncer] ✅ Sync successful: signal_batch_20260426_163619_412742.txt
[同步器] ✅ 同步成功: signal_batch_20260426_163619_412742.txt
  Modified time: 2026-04-26 14:12:27
  修改时间: 2026-04-26 14:12:27
  Target path: D:\main_data\signals\signal_batch_20260426_163619_412742.txt
  目标路径: D:\main_data\signals\signal_batch_20260426_163619_412742.txt
✅ Sync startup successful!
✅ 启动同步成功!

⏰ [Auto Sync] Checking every 30 seconds...
⏰ [自动同步] 每 30 秒检查一次...
[Syncer] Auto sync thread started
[同步器] 自动同步线程已启动

💡 [Tip] Syncer is running in the background
💡 [提示] 同步器已在后台运行
   - New files detected will be automatically copied to target directory
   - 检测到新文件会自动复制到目标目录
   - Synced files will not be processed repeatedly
   - 已同步的文件不会重复处理
   - Keep this window open, press Ctrl+C to stop
   - 保持此窗口开启,按 Ctrl+C 停止
======================================================================
```

**Main Strategy Window Logs / 主策略窗口日志**:
```
============================================================
Starting AlphaPilot Pro V9.2 (Industrial-grade Event-Driven Architecture)
启动 AlphaPilot Pro V9.2 (工业级事件驱动架构)
============================================================
[Configuration] Run mode: live
[配置] 运行模式: live
[Configuration] Account ID: simulation
[配置] 账户ID: simulation
[Configuration] Subscribed stocks: SHSE.600000, SZSE.000001
[配置] 订阅股票: SHSE.600000, SZSE.000001
============================================================
👁️  [watchdog] Start listening to signal directory: D:\main_data\signals
👁️  [watchdog] 开始监听信号目录: D:\main_data\signals
💡 [Tip] New signal files will trigger processing immediately (zero scan overhead)
💡 [提示] 新信号文件将立即触发处理（零扫描开销）
📩 [watchdog] Detected new signal: signal_batch_20260426_163619_412742.txt
📩 [watchdog] 检测到新信号: signal_batch_20260426_163619_412742.txt
[Strategy] Starting signal processing...
[策略] 开始处理信号...
```

#### 4️⃣ Keep Windows Open / 保持窗口开启

- Both windows must remain open to continue working
- 两个窗口必须保持开启才能持续工作
- Closing either window will stop the corresponding service
- 关闭任意窗口会停止对应服务

---

## 🔧 Configuration / 配置说明

### Change Sync Paths / 修改同步路径

Edit `signal_sync_standalone.py`:
编辑 `signal_sync_standalone.py`:

```python
# ==================== Configuration / 配置区 ====================
SOURCE_DIR = r"D:\mpython\signals\processed"   # Source directory (external signal archive) / 源目录(外部信号归档)
TARGET_DIR = r"D:\main_data\signals"            # Target directory (strategy monitoring) / 目标目录(策略监听)
SYNC_INTERVAL = 30                              # Sync interval (seconds) / 同步间隔(秒)
SYNC_ON_STARTUP = True                          # Sync immediately on startup / 启动时立即同步
```

### Adjust Sync Interval / 调整同步间隔

Edit in `signal_sync_standalone.py`:
在 `signal_sync_standalone.py` 中修改:
```python
SYNC_INTERVAL = 30  # Change to 60 to check every 1 minute / 改为60表示1分钟检查一次
```

---

## 🐛 Troubleshooting / 故障排查

### Issue 1: "ModuleNotFoundError: No module named 'dotenv'"

**Error Message / 错误信息**:
```
ModuleNotFoundError: No module named 'dotenv'
```

**Cause / 原因**:
The newly opened CMD window has not activated the virtual environment, causing installed dependencies to not be found.
新打开的CMD窗口没有激活虚拟环境,导致找不到已安装的依赖包。

**Solution / 解决方案**:

**Method 1: Use the fixed one-click startup script (Recommended) / 方法1: 使用修复后的一键启动脚本(推荐)**
```bash
start_with_sync.bat
```
The script automatically activates the virtual environment in each new window.
脚本已自动在每个新窗口中激活虚拟环境。

**Method 2: Manually activate the virtual environment / 方法2: 手动激活虚拟环境**
```bash
# In CMD / 在CMD中
quant_env\Scripts\activate.bat
python main.py

# In PowerShell / 在PowerShell中
quant_env\Scripts\Activate.ps1
python main.py
```

**Method 3: Check if dependencies are installed / 方法3: 检查依赖是否安装**
```bash
# After activating virtual environment / 激活虚拟环境后
pip install python-dotenv watchdog gm
```

---

### Issue 2: "Python not found" Error / 问题2: "Python not found" 错误

**Solution / 解决方案**:
```bash
# Check if Python is installed / 检查Python是否安装
python --version

# If not installed, download from https://www.python.org/downloads/
# 如未安装,从 https://www.python.org/downloads/ 下载
# When installing, be sure to check "Add Python to PATH"
# 安装时务必勾选 "Add Python to PATH"
```

### Issue 3: Syncer Not Detecting Files / 问题3: 同步器未检测到文件

**Checklist / 检查清单**:
```bash
# 1. Confirm .txt files exist in source directory / 确认源目录有.txt文件
dir "D:\mpython\signals\processed\*.txt"

# 2. Check filename format / 检查文件名格式
# Correct / 正确: signal_batch_20260426_143000_123456.txt
# Incorrect / 错误: test.txt, signal.json

# 3. View sync history / 查看同步历史
type "D:\main_data\signals\.sync_history.json"
```

### Issue 4: Watchdog Not Triggering After Sync / 问题4: 同步后watchdog未触发

**Possible Causes / 可能原因**:
- File already exists, overwritten but did not trigger CREATE event
- 文件已存在,被覆盖但未触发CREATE事件
- Watchdog monitoring directory differs from actual
- watchdog监听的目录与实际不同

**Solution / 解决方案**:
```bash
# Look for watchdog listening directory in main.py logs / 在main.py日志中查找watchdog监听目录
# Find: "👁️  [watchdog] Start listening to signal directory: D:\main_data\signals"
# 寻找: "👁️  [watchdog] 开始监听信号目录: D:\main_data\signals"

# Ensure target directory is correct / 确保目标目录正确
echo $env:SIGNAL_DIR_INPUT  # Should be / 应为 D:\main_data\signals
```

### Issue 5: File Already Synced, Cannot Retest / 问题5: 文件已同步过,无法重新测试

**Solution Methods / 解决方法**:

**Method 1: Delete sync history / 方法1: 删除同步历史**
```bash
Remove-Item "D:\main_data\signals\.sync_history.json"
```

**Method 2: Use a new signal file / 方法2: 使用新的信号文件**
- Create a new file with different timestamp in filename
- 在源目录创建文件名时间戳不同的新文件

**Method 3: Force resync (code level) / 方法3: 强制重新同步(代码层面)**
```python
# In signal_sync_standalone.py or test script / 在signal_sync_standalone.py或测试脚本中
syncer.sync_latest_file(force=True)
```

---

## ⚠️ Important Notes / 注意事项

1. **Keep syncer window open / 保持同步器窗口开启**: New files will no longer be auto-synced after closing / 关闭后不再自动同步新文件
2. **Filename format / 文件名格式**: Must be `signal_batch_YYYYMMDD_HHMMSS_*.txt` / 必须为 `signal_batch_YYYYMMDD_HHMMSS_*.txt`
3. **Duplicate prevention mechanism / 防重复机制**: Already synced files will not be processed repeatedly / 已同步的文件不会重复处理
4. **Timestamp extraction / 时间戳提取**: Extract from 3rd and 4th parts of filename (see technical specification) / 从文件名第3、4部分提取(见技术规范)
5. **Testing recommendation / 测试建议**: Run `test_signal_sync.py` first to verify functionality / 首次使用先运行 `test_signal_sync.py` 验证功能

---

## 🎯 Core Advantages / 核心优势

✅ **Separation of Concerns / 职责分离**: Syncer focuses on file operations, main strategy focuses on trading decisions / 同步器专注文件操作,主策略专注交易决策  
✅ **Independent Operation / 独立运行**: Syncer requires no Juejin environment, reducing dependency complexity / 同步器无需掘金环境,降低依赖复杂度  
✅ **One-Click Startup / 一键启动**: Simplifies workflow, no need to manually open multiple terminals / 简化操作流程,无需手动开多个终端  
✅ **Flexible Configuration / 灵活配置**: Can independently adjust sync interval and paths / 可独立调整同步间隔和路径  
✅ **Duplicate Prevention / 防重复处理**: Automatically records history to avoid redundant operations / 自动记录历史,避免冗余操作  

---

## 📚 Related Documentation / 相关文档

- **SIGNAL_SYNC_QUICKSTART.md** - Detailed Chinese Quick Start Guide / 中文版详细快速入门指南
- **SIGNAL_SYNC_GUIDE.md** - Detailed Chinese Technical Documentation / 中文版详细技术文档
- **VSCODE_INDEPENDENT_RUN_MANDATORY.md** - Juejin Strategy Execution Guide / 掘金策略运行指南
- **test_signal_sync.py** - Independent Sync Test Script / 独立同步测试脚本

---

**Author / 作者**: AlphaPilot Intelligence Team / Alphapilot智能体团队  
**Version / 版本**: V9.2  
**Last Updated / 更新日期**: 2026-05-20
