# AlphaPilot Pro V9.1 - 信号文件同步器使用指南

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558

---

## 🎯 核心功能

**信号文件同步器**自动从 `D:\mpython\signals\processed` 检测最新信号文件,并复制到 `D:\main_data\signals`,触发策略执行。

### 工作原理

```
D:\mpython\signals\processed (源目录)
    └─ signal_batch_20260424_095753_864066.txt ← 最新文件
    
         ↓ 自动检测并复制
    
D:\main_data\signals (目标目录)
    └─ signal_batch_20260424_095753_864066.txt ← 触发watchdog监听
    
         ↓ watchdog检测到新文件
    
策略执行 → 买入/卖出操作
```

---

## 🚀 快速开始(三种方式)

### 方式一:集成到 main.py(推荐) ⭐

**已自动集成**,无需额外配置!

启动主程序时会自动:
1. 从 `D:\mpython\signals\processed` 同步最新文件
2. 每 30 秒检查一次新文件
3. 通过 watchdog 触发策略执行

```bash
python main.py
```

**日志输出示例:**
```
🔄 [同步器] 初始化完成
  源目录: D:\mpython\signals\processed
  目标目录: D:\main_data\signals
  已同步文件数: 0

🔄 [同步器] 启动时同步最新信号文件...
[同步器] ✅ 同步成功: signal_batch_20260424_095753_864066.txt
  修改时间: 2026-04-24 09:57:53
  目标路径: D:\main_data\signals\signal_batch_20260424_095753_864066.txt

📩 [watchdog] 检测到新信号: signal_batch_20260424_095753_864066.txt
[立即策略-启动] SZSE.301667 BUY | 价格:111.75 | 量比:1.46
...
```

---

### 方式二:独立运行同步器

**适用场景**: 在掘金仿真账户中单独测试同步功能

**步骤:**

1. 打开 [`signal_sync_standalone.py`](d:\main_data\signal_sync_standalone.py)
2. 修改第 28-29 行的路径(如果需要)
3. 修改第 77 行的策略ID
4. 在掘金终端运行

```python
# 配置区
SOURCE_DIR = r"D:\mpython\signals\processed"
TARGET_DIR = r"D:\main_data\signals"

# 策略ID
strategy_id='your_strategy_id_here'  # ← 替换为你的策略ID
```

---

### 方式三:手动触发同步

**适用场景**: 按需同步特定文件

**代码示例:**

```python
from utils.signal_syncer import SignalFileSyncer

# 创建同步器
syncer = SignalFileSyncer(
    source_dir=r"D:\mpython\signals\processed",
    target_dir=r"D:\main_data\signals"
)

# 同步最新文件
success = syncer.sync_latest_file()

if success:
    print("✅ 同步成功!")
else:
    print("❌ 无新文件或同步失败")
```

---

## 📋 核心功能详解

### 1. 智能文件检测

同步器会**按文件名中的时间戳排序**,找到最新的文件:

```python
# 文件名格式: signal_batch_20260424_095753_864066.txt
#                     ↓日期      ↓时间   ↓随机数

# 提取时间戳: 20260424_095753
# 排序后取最新的
```

**优势:**
- ✅ 不依赖文件修改时间(避免复制操作影响时间戳)
- ✅ 精确到秒级排序
- ✅ 支持批量文件中的最新选择

---

### 2. 防重复同步机制

同步器会记录已处理的文件,避免重复执行:

```json
// .sync_history.json (自动生成)
{
  "synced_files": [
    "signal_batch_20260424_095753_864066.txt",
    "signal_batch_20260424_100505_855524.txt"
  ],
  "last_update": "2026-04-24T10:30:00"
}
```

**工作流程:**
1. 检测到最新文件
2. 检查是否在历史记录中
3. 如果已同步 → 跳过
4. 如果未同步 → 复制并记录

---

### 3. 自动同步线程

后台线程每 30 秒检查一次新文件:

```python
# 在 main.py 中自动启动
signal_syncer.start_auto_sync(interval_seconds=30)
```

**特点:**
- ✅ 独立线程,不阻塞主策略
- ✅ daemon=True,程序退出时自动停止
- ✅ 异常捕获,不会因单次失败而中断

---

## 💡 实战案例

### 案例 1: 三个仿真账户测试不同参数

**目标**: 在三个掘金仿真账户中测试不同的量比阈值

**步骤:**

1. **准备三个策略实例:**
   - 实例 A: `strategy_A` - 量比阈值 2.0
   - 实例 B: `strategy_B` - 量比阈值 3.0
   - 实例 C: `strategy_C` - 量比阈值 4.0

2. **在每个实例中运行 main.py:**
   ```bash
   # 终端 1 (实例 A)
   python main.py  # 配置中设置 VOLUME_RATIO_THRESHOLD = 2.0
   
   # 终端 2 (实例 B)
   python main.py  # 配置中设置 VOLUME_RATIO_THRESHOLD = 3.0
   
   # 终端 3 (实例 C)
   python main.py  # 配置中设置 VOLUME_RATIO_THRESHOLD = 4.0
   ```

3. **观察同步日志:**
   ```
   [同步器] ✅ 同步成功: signal_batch_20260424_095753_864066.txt
   
   # 实例 A (阈值 2.0):
   [立即策略-终止] SZSE.301667 量比 1.46 < 2.0,跳过买入
   
   # 实例 B (阈值 3.0):
   [立即策略-终止] SZSE.301667 量比 1.46 < 3.0,跳过买入
   
   # 实例 C (阈值 4.0):
   [立即策略-终止] SZSE.301667 量比 1.46 < 4.0,跳过买入
   ```

4. **对比结果:**
   - 统计每个实例的买入次数
   - 分析不同阈值对策略表现的影响
   - 选择最优参数

---

### 案例 2: 调试特定信号的处理逻辑

**问题**: 某只股票应该被延时策略拦截,但实际买入了

**调试步骤:**

1. 找到包含该股票的信号文件:
   ```
   D:\mpython\signals\processed\signal_batch_20260424_095753_864066.txt
   ```

2. 查看文件内容:
   ```json
   {"ts": "2026-04-24 09:57:53", "code": "SZSE.301667", "name": "纳百川", 
    "action": "BUY", "price": 111.75, "volume_ratio": 1.46}
   ```

3. 检查 `data/stock_personalities.json`:
   ```json
   {
     "301667": {
       "type": "delayed",  // ← 应该是延时股票
       "target_date": "2026-04-27"
     }
   }
   ```

4. 运行同步器,观察日志:
   ```
   [同步器] ✅ 同步成功: signal_batch_20260424_095753_864066.txt
   [延时策略-检查] SZSE.301667 (纯代码:301667) | 类型: delayed | 量比: 1.46
   [延时策略] SZSE.301667 已加入观察名单，目标日: 2026-04-27
   [信号分流] SZSE.301667 已加入延时观察名单
   ```

5. 如果看到 `[立即策略-阻断]`,说明逻辑正确  
   如果看到 `[买入成功]`,检查配置文件是否正确

---

### 案例 3: 批量回测历史信号

**目标**: 测试过去一周所有信号的表现

**步骤:**

1. 清空同步历史记录:
   ```python
   # 删除 .sync_history.json
   os.remove(r"D:\main_data\signals\.sync_history.json")
   ```

2. 批量同步所有文件:
   ```python
   from utils.signal_syncer import SignalFileSyncer
   
   syncer = SignalFileSyncer(
       source_dir=r"D:\mpython\signals\processed",
       target_dir=r"D:\main_data\signals"
   )
   
   count = syncer.sync_all_new_files()
   print(f"同步了 {count} 个文件")
   ```

3. 观察策略执行日志,统计:
   - 买入次数
   - 卖出次数
   - 止损次数
   - 盈亏情况

---

## ⚙️ 高级配置

### 1. 调整同步间隔

在 [`main.py`](d:\main_data\main.py) 中修改:

```python
# 默认 30 秒
signal_syncer.start_auto_sync(interval_seconds=30)

# 改为 10 秒(更频繁)
signal_syncer.start_auto_sync(interval_seconds=10)

# 改为 60 秒(更宽松)
signal_syncer.start_auto_sync(interval_seconds=60)
```

---

### 2. 修改源/目标目录

如果信号文件在其他位置:

```python
# 在 main.py 中修改
SOURCE_SIGNAL_DIR = r"D:\your_custom_path\processed"
TARGET_SIGNAL_DIR = r"D:\your_custom_path\signals"
```

---

### 3. 强制重新同步

如果需要重新处理某个文件:

```python
# 方式1: 删除历史记录
os.remove(r"D:\main_data\signals\.sync_history.json")

# 方式2: 强制同步
syncer.sync_latest_file(force=True)
```

---

### 4. 禁用自动同步

如果只想手动触发:

```python
# 注释掉自动同步代码
# signal_syncer.start_auto_sync(interval_seconds=30)

# 手动触发
syncer.sync_latest_file()
```

---

## 🐛 常见问题

### Q1: 同步器没有检测到新文件?

**检查清单:**
1. 确认源目录中有 `.txt` 文件
2. 确认文件名格式正确 (`signal_batch_YYYYMMDD_HHMMSS_*.txt`)
3. 查看日志中的 `[同步器] 未找到新的信号文件` 提示

**调试方法:**
```python
# 手动检查源目录
import os
import glob

source_dir = r"D:\mpython\signals\processed"
files = glob.glob(os.path.join(source_dir, "*.txt"))
print(f"找到 {len(files)} 个文件:")
for f in sorted(files):
    print(f"  - {os.path.basename(f)}")
```

---

### Q2: 文件被重复同步?

**原因**: 同步历史记录丢失或损坏

**解决:**
1. 检查 `.sync_history.json` 是否存在
2. 如果文件损坏,删除后重新生成
3. 确保程序有写入权限

---

### Q3: 同步后策略没有执行?

**可能原因:**
1. watchdog 未监听到文件创建事件
2. 文件格式不正确
3. 策略逻辑拦截了信号

**排查步骤:**
1. 检查日志中是否有 `[watchdog] 检测到新信号`
2. 检查文件格式(每行一个 JSON 对象)
3. 检查策略日志中的过滤条件

---

### Q4: 如何在多个掘金账户中独立运行?

**方案:**
每个掘金策略实例有独立的内存空间,互不影响:

```
掘金实例 A (strategy_id_A)
  ├─ 独立的 SignalFileSyncer 实例
  ├─ 独立的 .sync_history.json
  └─ 独立的策略状态

掘金实例 B (strategy_id_B)
  ├─ 独立的 SignalFileSyncer 实例
  ├─ 独立的 .sync_history.json
  └─ 独立的策略状态
```

**注意:**
- ✅ 可以共享同一个源目录(`D:\mpython\signals\processed`)
- ✅ 每个实例有独立的目标目录和同步历史
- ✅ 互不干扰,可并行运行

---

## 📊 性能优化建议

### 1. 定期清理同步历史

如果 `.sync_history.json` 过大:

```python
# 自动清理(只保留最近100条)
# 已在代码中实现,无需手动操作
```

### 2. 调整同步间隔

- **高频交易**: 10-15 秒
- **普通交易**: 30 秒(默认)
- **低频交易**: 60-120 秒

### 3. 监控同步状态

添加自定义日志:

```python
# 在 on_bar 中定期检查
def on_bar(context, bars):
    if context.bar_count % 10 == 0:  # 每10根K线检查一次
        latest = syncer.get_latest_signal_file()
        if latest:
            print(f"[监控] 最新信号文件: {os.path.basename(latest)}")
```

---

## 📞 技术支持

如有问题,请联系 Alphapilot智能体团队:
- 邮箱: 497720537@qq.com
- 电话: 13392077558

---

**祝您测试顺利!🚀**
