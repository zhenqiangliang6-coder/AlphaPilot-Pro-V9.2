# 🎯 掘金量化实时行情API修复报告

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558

---

## 🔴 **问题根源**

### **症状**
止损模块报告所有持仓"成本价为0"，止盈模块也无法触发。

### **根本原因**

**交易引擎使用了错误的价格源！**

```python
# ❌ 错误的实现（旧代码）
def get_tick_data(self, symbols, count=1):
    """用 last_price 替代 tick"""
    positions = get_position(account_id=self.account_id)
    pos_map = {p["symbol"]: p for p in positions}
    
    for sym in symbols:
        result[sym] = {"last_price": pos_map[sym].get("last_price", None)}
    
    return result
```

**问题分析**：
1. `last_price` 来自**持仓快照**（不实时更新）
2. 止损模块看到的"现价 = 成本价"
3. 盈亏永远为 0，止损永远不会触发

---

## ✅ **修复方案**

### **核心修改：使用实时行情API**

```python
# ✅ 正确的实现（新代码）
from gm.api import current

def get_latest_prices(self, symbols):
    """获取最新价（使用 60s 行情）"""
    result = {}
    
    for sym in symbols:
        try:
            df = current(
                symbol=sym,
                frequency='60s',     # ✔ 一分钟最新价
                fields='close'       # ✔ 最新成交价
            )
            if df is not None and len(df) > 0:
                result[sym] = float(df.iloc[0]['close'])
            else:
                result[sym] = None
        except Exception as e:
            print(f"[TraderEngine] 获取最新价失败: {sym}, {e}")
            result[sym] = None
    
    return result
```

---

## 📋 **修改的文件**

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| [core/trader_engine.py](file://d:\mpython\core\trader_engine.py) | 替换 `get_tick_data` → `get_latest_prices` | ✅ 完成 |
| [risk/stop_loss.py](file://d:\mpython\risk\stop_loss.py) | 2处调用修改 | ✅ 完成 |
| [risk/dynamic_take_profit.py](file://d:\mpython\risk\dynamic_take_profit.py) | 1处调用修改 | ✅ 完成 |
| [strategies/rocket_boost.py](file://d:\mpython\strategies\rocket_boost.py) | 1处调用修改 | ✅ 完成 |
| [strategies/delayed_strategy.py](file://d:\mpython\strategies\delayed_strategy.py) | 2处调用修改 | ✅ 完成 |
| [strategies/auction_strategy.py](file://d:\mpython\strategies\auction_strategy.py) | 1处调用修改 | ✅ 完成 |
| [core/state_manager.py](file://d:\mpython\core\state_manager.py) | 1处调用修改 | ✅ 完成 |

---

## 🚀 **预期效果**

### **启动后15秒内应该看到**

```
💓 [心跳] 14:35:XX - 系统运行正常

[止损检查] 开始执行 (当前时间:14:35:XX, 窗口:10:45-14:50)
[止损检查] 发现 18 只持仓股票，开始检查...

[止损分析] SZSE.301165 成本:100.59 现价:92.69 盈亏:-7.85% 亏损:7.85%
[止损-二级] SZSE.301165 触发二级止损 (成本:100.59 现价:92.69 亏损:7.85%)
[止损执行] 成功卖出 SZSE.301165 500 股 @ 91.76 (二级止损(-2.5%清仓))
[止损] SZSE.301165 二级止损完成，已清仓 500 股

[止损分析] SZSE.002679 成本:10.77 现价:10.37 盈亏:-3.71% 亏损:3.71%
[止损-二级] SZSE.002679 触发二级止损 (成本:10.77 现价:10.37 亏损:3.71%)
[止损执行] 成功卖出 SZSE.002679 4600 股 @ 10.27 (二级止损(-2.5%清仓))
[止损] SZSE.002679 二级止损完成，已清仓 4600 股

[止盈检查] 开始执行 (当前时间:14:35:XX)
[止盈-监控] SZSE.301667 成本:109.77 现价:111.48 盈亏:1.56%
[止盈-监控] SHSE.600151 成本:14.93 现价:15.03 盈亏:0.70%

[止损总结] 本轮共执行 8 次止损操作
```

**关键变化**：
- ✅ `现价` 不再等于 `成本价`
- ✅ `盈亏` 显示真实亏损（如 -7.85%）
- ✅ 触发止损阈值后出现 `[止损执行]` 日志

---

## ⚠️ **重要提醒**

### **立即操作**

1. 在掘金终端中点击 **"断开"**
2. 重新 **"连接"** 策略
3. 等待 **15 秒**
4. 观察日志输出

### **预期日志特征**

- ✅ `[止损分析]` 显示真实的盈亏比例（不为0）
- ✅ `[止损执行]` 出现卖出操作
- ✅ `[止盈-监控]` 显示盈利的股票

---

## 📞 **技术支持**

如遇到问题，请提供：
1. 完整的控制台输出（从启动到现在）
2. 掘金终端的账户持仓截图
3. 当前系统时间

**Alphapilot智能体团队**  
邮箱: 497720537@qq.com | 电话: 13392077558

---

**修复完成时间**: 2026-04-21 16:45  
**修复版本**: V9.1.2  
**影响范围**: 所有行情获取模块（止损、止盈、火箭、延时、竞价、状态管理）
