# 动态止盈模块BUG修复 - 快速参考

## 🚨 问题现象

> "兄弟帮我查检止盈部分是否有个股前缀错误，因为掘金量化的个股前缀和一般的不一样，和逻辑问题，我总发觉止盈好像没有执行的？？"

**根本原因**：股票代码前缀判断逻辑错误，导致 Level 2 和 Level 3 止盈策略完全失效。

---

## ✅ 已修复内容

### 1. 核心修复文件

- **`risk/dynamic_take_profit.py`** - 动态止盈模块
  - ✅ 新增 `_extract_numeric_code()` 方法：从掘金格式代码中提取纯数字部分
  - ✅ 修改 `_check_level2()` 方法：使用正确的前缀判断逻辑
  - ✅ 修改 `_check_level3()` 方法：使用正确的前缀判断逻辑
  - ✅ 增加调试日志：显示原始代码和提取的数字码

### 2. 诊断工具

- **`diagnose_take_profit_prefix.py`** - 完整诊断测试脚本
  - 验证股票代码提取功能
  - 测试前缀判断逻辑
  - 模拟真实场景
  - 检查时间窗口

- **`test_take_profit_quick.ps1`** - PowerShell快速验证脚本
  - 一键运行诊断
  - 自动检查日志

### 3. 文档

- **`DYNAMIC_TAKE_PROFIT_PREFIX_FIX_REPORT.md`** - 详细修复报告
- **`DYNAMIC_TAKE_PROFIT_QUICK_REFERENCE.md`** - 快速参考（本文档）

---

## 🔍 问题详解

### 掘金SDK返回格式

```python
# 掘金持仓数据中的股票代码格式
symbol = "SZSE.300444"  # 深圳股票
symbol = "SHSE.688295"  # 上海股票
```

### 原代码错误

```python
# ❌ 错误逻辑
code_prefix = code[:2]  # 对于 "SZSE.300444"，得到的是 "SZ"，不是 "30"
if code_prefix not in ['60', '00']:
    return  # Level 2 永远无法执行
```

### 修复后逻辑

```python
# ✅ 正确逻辑
numeric_code = self._extract_numeric_code(code)  # 提取 "300444"
code_prefix = numeric_code[:2]  # 现在得到的是 "30"
if code_prefix not in ['60', '00']:
    return  # 现在可以正确判断
```

---

## 🧪 快速验证

### 方法1：运行诊断脚本

```bash
# 激活虚拟环境后运行
python diagnose_take_profit_prefix.py
```

**预期输出**：所有测试用例通过 ✅

### 方法2：使用PowerShell脚本

```powershell
.\test_take_profit_quick.ps1
```

**功能**：自动运行诊断 + 检查日志

---

## ⚠️ 重要提醒

### 1. 时间窗口限制

动态止盈默认在 **09:51** 之后才执行。

- 当前时间 < 09:51 → 不会执行
- 如需调整，修改 `settings.py`：
  ```python
  TAKE_PROFIT_EARLIEST_TIME = "0930"  # 9:30开盘后立即执行
  ```

### 2. T+1 规则

今日买入不可今日卖出。如果持仓是今天买的，止盈会跳过：

```
[止盈跳过] SZSE.300444 今日买入不可卖（总持仓:100 可卖:0），无法执行
```

### 3. 检查频率

止盈检查每 **15秒** 执行一次（由心跳线程控制）。

### 4. 查看日志

关注以下日志关键字：

- `[止盈-快速]` - Level 1 触发
- `[止盈-波段]` - Level 2 触发（60/00开头）
- `[止盈-强势]` - Level 3 触发（68/30开头）
- `[止盈跳过]` - 因T+1或其他原因跳过

---

## 📊 修复效果

| 止盈级别 | 修复前 | 修复后 |
|---------|-------|-------|
| Level 1 (快速) | ✅ 正常 | ✅ 正常 |
| Level 2 (波段) | ❌ 永不执行 | ✅ 正常执行 |
| Level 3 (强势) | ❌ 永不执行 | ✅ 正常执行 |

---

## 🔧 配置调整

### 修改最早执行时间

```python
# settings.py
TAKE_PROFIT_EARLIEST_TIME = "0930"  # 更早执行
# 或
TAKE_PROFIT_EARLIEST_TIME = "1000"  # 更晚执行
```

### 修改止盈阈值

```python
# settings.py

# 第一级：快速止盈
TAKE_PROFIT_LEVEL1_GAIN = 0.03      # 上涨3%
TAKE_PROFIT_LEVEL1_DROP = 0.013     # 回落1.3%

# 第二级：波段止盈
TAKE_PROFIT_LEVEL2_GAIN = 0.09      # 上涨9%
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 12 # 持有12分钟

# 第三级：强势止盈
TAKE_PROFIT_LEVEL3_GAIN = 0.18      # 上涨18%
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 12 # 持有12分钟
```

---

## 📝 下一步

1. ✅ **已完成**：修复代码并验证
2. 🔄 **建议操作**：
   - 运行 `diagnose_take_profit_prefix.py` 确认修复成功
   - 观察日志，确认 Level 2 和 Level 3 开始正常工作
   - 如有需要，调整 `TAKE_PROFIT_EARLIEST_TIME` 参数

3. 🎯 **预期结果**：
   - Level 2（60/00开头股票）涨9%后会开始计时，12分钟后卖出
   - Level 3（68/30开头股票）涨18%后会开始计时，12分钟后卖出
   - 日志中会出现 `[止盈-波段]` 和 `[止盈-强势]` 记录

---

**修复版本**: V9.2.1  
**修复日期**: 2026-05-07  
**相关文档**: `DYNAMIC_TAKE_PROFIT_PREFIX_FIX_REPORT.md`
