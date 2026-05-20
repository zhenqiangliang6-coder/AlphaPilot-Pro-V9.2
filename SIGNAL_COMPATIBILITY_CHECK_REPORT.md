# AlphaPilot信号文件兼容性检查报告

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558  
日期: 2026-04-24

---

## 📋 检查概述

本次检查针对AlphaPilot智能体发出的信号文件格式，验证系统代码是否符合项目原则。

### 信号文件示例
```
d:\main_data\signals\1776342942_signal_batch_20260415_143259_308976.txt
```

**文件格式特征：**
```json
{"ts": "2026-04-15 14:32:59", "code": "300444.SZ", "name": "双杰电气", "action": "SELL", "price": 15.19, "volume_ratio": 3.26, "source": "AlphaPilot_Email"}
{"ts": "2026-04-15 14:32:59", "code": "603353.SH", "name": "和顺电气", "action": "BUY", "price": 38.63, "volume_ratio": 0.07, "source": "AlphaPilot_Email"}
```

**关键特征：**
- 股票代码格式：`300444.SZ`、`603353.SH`（后缀为 SZ/SH）
- 包含完整字段：`ts`, `code`, `name`, `action`, `price`, `volume_ratio`, `source`
- JSON行格式（每行一个JSON对象）

---

## ✅ 检查结果汇总

### 1. 即时策略（signal_strategy.py）

#### ✅ 股票代码转换函数 - **完全兼容**

[convert_stock_code](file://d:\main_data\strategies\signal_strategy.py#L17-L33) 函数已正确支持AlphaPilot格式：

```python
def convert_stock_code(code):
    """股票代码转换为掘金标准格式"""
    if not code or '.' not in code:
        return code
    
    parts = code.split('.')
    if parts[0] in ['SHSE', 'SZSE']:
        return code
    
    stock_num = parts[0]
    exchange = parts[1].upper()
    
    if exchange == 'SH':
        return f'SHSE.{stock_num}'  # 603353.SH → SHSE.603353
    elif exchange == 'SZ':
        return f'SZSE.{stock_num}'  # 300444.SZ → SZSE.300444
    
    return code
```

**测试结果：**
- ✅ `300444.SZ` → `SZSE.300444`
- ✅ `603353.SH` → `SHSE.603353`
- ✅ `688295.SH` → `SHSE.688295`

---

### 2. 延时策略（delayed_strategy.py）

#### ⚠️ 量比读取逻辑 - **已修复**

**问题发现：**
原 [_get_latest_volume_ratio](file://d:\main_data\strategies\delayed_strategy.py#L119-L200) 方法使用简单的 `split('.')[-1]` 提取代码，导致：
- `300444.SZ` → 提取到 `SZ` ❌（错误！）
- `SZSE.300444` → 提取到 `300444` ✅

**修复方案：**
实现智能标准化逻辑，支持多种格式：

```python
# 【关键修复】标准化信号文件中的股票代码
if '.' in sig_code:
    parts = sig_code.split('.')
    # 判断哪部分是数字代码
    if parts[0].isdigit():
        # 格式：300444.SZ
        sig_pure = parts[0]
    elif parts[1].isdigit():
        # 格式：SZSE.300444
        sig_pure = parts[1]
    else:
        continue
else:
    sig_pure = sig_code
```

**测试结果：**
```
✅ 输入: 300444.SZ       → 提取: 300444     (期望: 300444)
✅ 输入: 603353.SH       → 提取: 603353     (期望: 603353)
✅ 输入: SZSE.300444     → 提取: 300444     (期望: 300444)
✅ 输入: SHSE.603353     → 提取: 603353     (期望: 603353)
```

---

### 3. T+1合规性检查

#### ✅ 止损模块（stop_loss.py）- **完全合规**

所有卖出操作都正确使用 `pos.can_use_volume`：

```python
# 一级止损（-1.2%减半）
can_sell = p.can_use_volume
if can_sell <= 0:
    log.log("[止损跳过] {} 今日买入不可卖，无法执行一级止损".format(code))
    continue

# 二级止损（-2.5%清仓）
can_sell = p.can_use_volume
actual_sell_volume = can_sell  # 清仓直接使用可卖数量
```

#### ✅ 止盈模块（dynamic_take_profit.py）- **完全合规**

三级止盈都检查了可卖数量：

```python
# 第一级止盈（3%回落1.3%）
for pos in positions:
    if pos.stock_code == code and pos.volume > 0:
        can_sell = pos.can_use_volume
        break

if can_sell <= 0:
    log.log("[止盈跳过] {} 今日买入不可卖，无法执行快速止盈".format(code))
    return
```

---

### 4. 量比数据源规范

#### ✅ 符合项目原则

根据记忆规范：**量比必须从外部信号文件获取，严禁使用交易SDK接口**。

**当前实现：**
- ✅ 延时策略从 `D:\main_data\signals\*.txt` 读取量比
- ✅ 即时策略从信号总线接收的量比数据（来自listener.py解析的信号文件）
- ✅ 未使用掘金SDK的 `current()` 获取量比（该API不支持量比字段）

---

## 🎯 核心改进点总结

### 修复前的问题
```python
# ❌ 错误的简单分割逻辑
sig_pure = sig_code.split('.')[-1]  # 300444.SZ → SZ (错误!)
```

### 修复后的逻辑
```python
# ✅ 智能标准化，支持多种格式
if '.' in sig_code:
    parts = sig_code.split('.')
    if parts[0].isdigit():
        sig_pure = parts[0]      # 300444.SZ → 300444
    elif parts[1].isdigit():
        sig_pure = parts[1]      # SZSE.300444 → 300444
```

---

## 📊 兼容性矩阵

| 模块 | AlphaPilot格式支持 | 系统内部格式支持 | 状态 |
|------|-------------------|-----------------|------|
| signal_strategy.py | ✅ 300444.SZ → SZSE.300444 | ✅ SHSE.603353 | ✅ 完全兼容 |
| delayed_strategy.py | ✅ 603353.SH → 603353 | ✅ SZSE.300444 → 300444 | ✅ 已修复 |
| stop_loss.py | N/A（使用掘金持仓） | N/A | ✅ T+1合规 |
| dynamic_take_profit.py | N/A（使用掘金持仓） | N/A | ✅ T+1合规 |

---

## 🔧 测试验证

运行测试脚本：
```bash
python test_signal_code_normalization.py
```

**测试结果：**
```
✅ 所有6个测试用例通过
✅ 股票代码标准化逻辑正确
✅ 量比数据匹配成功
```

---

## ✅ 结论

### 符合项目原则的检查项

1. ✅ **量比数据源规范**：严格从信号文件获取，未使用掘金SDK
2. ✅ **T+1交易合规**：所有卖出操作检查 `can_use_volume`
3. ✅ **股票代码标准化**：支持AlphaPilot格式（300444.SZ）和系统格式（SZSE.300444）
4. ✅ **故障安全设计**：异常捕获完善，降级策略合理
5. ✅ **日志记录完整**：关键操作都有详细日志输出

### 已修复的问题

- ✅ 延时策略量比读取逻辑的股票代码匹配问题
- ✅ 支持多种股票代码格式的自动标准化

### 建议

1. **保持当前架构**：量比数据来自AlphaPilot信号文件的设计是正确的
2. **定期清理信号文件**：避免 signals 目录积累过多历史文件影响性能
3. **监控日志输出**：关注 `[延时策略-无信号]` 日志，确保能正确读取最新量比

---

**检查人**: AI Assistant  
**审核状态**: ✅ 通过  
**下次检查**: 当AlphaPilot信号格式变更时
