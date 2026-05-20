# AlphaPilot Pro V9.1 - 快速启动指南 / Quick Start Guide

## 🚀 一键启动 (推荐) / One-Click Startup (Recommended)

### 方式1: 双击运行 (最简单) / Method 1: Double-click (Easiest)

在Windows资源管理器中双击此文件:
```
start_with_sync.bat
```

### 方式2: 命令行运行 / Method 2: Command Line

在CMD或PowerShell中运行:
```bash
start_with_sync.bat
```

### 脚本自动完成以下操作 / What It Does

1. ✅ 检查Python环境 / Check Python environment
2. ✅ 清理Python缓存文件 / Clean Python cache files
3. ✅ 启动**信号同步器**(独立窗口) / Start **Signal Syncer** (separate window)
4. ✅ 等待3秒初始化 / Wait 3 seconds for initialization
5. ✅ 启动**主策略引擎**(另一窗口) / Start **Main Strategy Engine** (another window)

---

## 📂 两个窗口的功能 / Two Windows Will Open

### 窗口1: 信号同步器 / Window 1: Signal Syncer

**窗口标题**: `Signal Syncer - Auto Sync Latest Signals`

**功能**:
- 每30秒扫描 `D:\mpython\signals\processed` 目录
- 自动复制新信号文件到 `D:\main_data\signals`
- 防止重复处理同一文件
- **纯本地文件操作,无需掘金环境**

### 窗口2: 主策略引擎 / Window 2: Main Strategy Engine

**窗口标题**: `AlphaPilot Pro - Main Strategy Engine`

**功能**:
- 连接掘金量化平台
- Watchdog监听 `D:\main_data\signals` 目录
- 新信号文件立即触发策略处理
- 执行交易决策和风控逻辑
- **需要掘金终端运行并登录**

---

## 📁 目录结构 / Directory Structure

```
D:\mpython\signals\processed\          ← 源目录(外部信号归档)
├── signal_batch_20260426_163619_*.txt  ← 在此放入测试信号文件
└── ...

D:\main_data\signals\                   ← 目标目录(策略监听)
├── signal_batch_20260426_163619_*.txt  ← 同步过来的文件触发策略
├── .sync_history.json                  ← 同步历史(防重复)
└── processed/                          ← 已处理信号归档
```

---

## 💡 使用流程 / Usage Workflow

### 步骤说明 / Step-by-Step

#### 1️⃣ 准备测试信号 / Prepare Test Signal

在源目录放入信号文件:
```
D:\mpython\signals\processed\signal_batch_YYYYMMDD_HHMMSS_*.txt
```

**文件名格式要求**:
- ✅ 正确: `signal_batch_20260426_143000_123456.txt`
- ❌ 错误: `test.txt`, `signal.json`

#### 2️⃣ 运行启动脚本 / Run Startup Script

```bash
start_with_sync.bat
```

#### 3️⃣ 观察日志输出 / Observe Logs

**同步器窗口日志**:
```
======================================================================
🔄 AlphaPilot Pro - 信号文件同步器(独立运行模式)
======================================================================
[配置] 源目录: D:\mpython\signals\processed
[配置] 目标目录: D:\main_data\signals
[配置] 同步间隔: 30秒

[同步器] 初始化完成
  已同步文件数: 3

🚀 [启动同步] 同步最新信号文件...
[同步器] ✅ 同步成功: signal_batch_20260426_163619_412742.txt
  修改时间: 2026-04-26 14:12:27
  目标路径: D:\main_data\signals\signal_batch_20260426_163619_412742.txt
✅ 启动同步成功!

⏰ [自动同步] 每 30 秒检查一次...
[同步器] 自动同步线程已启动

💡 [提示] 同步器已在后台运行
   - 检测到新文件会自动复制到目标目录
   - 已同步的文件不会重复处理
   - 保持此窗口开启,按 Ctrl+C 停止
======================================================================
```

**主策略窗口日志**:
```
============================================================
启动 AlphaPilot Pro V9.1 (工业级事件驱动架构)
============================================================
[配置] 运行模式: live
[配置] 账户ID: simulation
[配置] 订阅股票: SHSE.600000, SZSE.000001
============================================================
👁️  [watchdog] 开始监听信号目录: D:\main_data\signals
💡 [提示] 新信号文件将立即触发处理（零扫描开销）
📩 [watchdog] 检测到新信号: signal_batch_20260426_163619_412742.txt
[策略] 开始处理信号...
```

#### 4️⃣ 保持窗口开启 / Keep Windows Open

- 两个窗口必须保持开启才能持续工作
- 关闭任意窗口会停止对应服务

---

## 🔧 配置说明 / Configuration

### 修改同步路径 / Change Sync Paths

编辑 `signal_sync_standalone.py`:

```python
# ==================== 配置区 ====================
SOURCE_DIR = r"D:\mpython\signals\processed"   # 源目录(外部信号归档)
TARGET_DIR = r"D:\main_data\signals"            # 目标目录(策略监听)
SYNC_INTERVAL = 30                              # 同步间隔(秒)
SYNC_ON_STARTUP = True                          # 启动时立即同步
```

### 调整同步间隔 / Adjust Sync Interval

在 `signal_sync_standalone.py` 中修改:
```python
SYNC_INTERVAL = 30  # 改为60表示1分钟检查一次
```

---

## 🐛 故障排查 / Troubleshooting

### 问题1: "ModuleNotFoundError: No module named 'dotenv'" / Issue 1: Missing dotenv Module

**错误信息 / Error**:
```
ModuleNotFoundError: No module named 'dotenv'
```

**原因 / Cause**:
新打开的CMD窗口没有激活虚拟环境,导致找不到已安装的依赖包。

**解决方案 / Solution**:

**方法1: 使用修复后的一键启动脚本(推荐)**
```bash
start_with_sync.bat
```
脚本已自动在每个新窗口中激活虚拟环境。

**方法2: 手动激活虚拟环境**
```bash
# 在CMD中
quant_env\Scripts\activate.bat
python main.py

# 在PowerShell中
quant_env\Scripts\Activate.ps1
python main.py
```

**方法3: 检查依赖是否安装**
```bash
# 激活虚拟环境后
pip install python-dotenv watchdog gm
```

---

### 问题2: "Python not found" 错误 / Issue 2: Python Not Found

**解决方案**:
```bash
# 检查Python是否安装
python --version

# 如未安装,从 https://www.python.org/downloads/ 下载
# 安装时务必勾选 "Add Python to PATH"
```

### 问题3: 同步器未检测到文件 / Issue 3: Syncer Not Detecting Files

**检查清单**:
```bash
# 1. 确认源目录有.txt文件
dir "D:\mpython\signals\processed\*.txt"

# 2. 检查文件名格式
# 正确: signal_batch_20260426_143000_123456.txt
# 错误: test.txt, signal.json

# 3. 查看同步历史
type "D:\main_data\signals\.sync_history.json"
```

### 问题4: 同步后watchdog未触发 / Issue 4: Watchdog Not Triggering

**可能原因**:
- 文件已存在,被覆盖但未触发CREATE事件
- watchdog监听的目录与实际不同

**解决方案**:
```bash
# 在main.py日志中查找watchdog监听目录
# 寻找: "👁️  [watchdog] 开始监听信号目录: D:\main_data\signals"

# 确保目标目录正确
echo $env:SIGNAL_DIR_INPUT  # 应为 D:\main_data\signals
```

### 问题5: 文件已同步过,无法重新测试 / Issue 5: File Already Synced

**解决方法**:

**方法1: 删除同步历史**
```bash
Remove-Item "D:\main_data\signals\.sync_history.json"
```

**方法2: 使用新的信号文件**
- 在源目录创建文件名时间戳不同的新文件

**方法3: 强制重新同步(代码层面)**
```python
# 在signal_sync_standalone.py或测试脚本中
syncer.sync_latest_file(force=True)
```

---

## ⚠️ 注意事项 / Important Notes

1. **保持同步器窗口开启**: 关闭后不再自动同步新文件
2. **文件名格式**: 必须为 `signal_batch_YYYYMMDD_HHMMSS_*.txt`
3. **防重复机制**: 已同步的文件不会重复处理
4. **时间戳提取**: 从文件名第3、4部分提取(见技术规范)
5. **测试建议**: 首次使用先运行 `test_signal_sync.py` 验证功能

---

## 🎯 核心优势 / Core Advantages

✅ **职责分离**: 同步器专注文件操作,主策略专注交易决策  
✅ **独立运行**: 同步器无需掘金环境,降低依赖复杂度  
✅ **一键启动**: 简化操作流程,无需手动开多个终端  
✅ **灵活配置**: 可独立调整同步间隔和路径  
✅ **防重复处理**: 自动记录历史,避免冗余操作  

---

## 📚 相关文档 / Related Documentation

- **SIGNAL_SYNC_QUICKSTART.md** - 中文版详细快速入门指南
- **SIGNAL_SYNC_GUIDE.md** - 中文版详细技术文档
- **VSCODE_INDEPENDENT_RUN_MANDATORY.md** - 掘金策略运行指南
- **test_signal_sync.py** - 独立同步测试脚本

---

**作者**: Alphapilot智能体团队  
**版本**: V9.1  
**更新日期**: 2026-04-26