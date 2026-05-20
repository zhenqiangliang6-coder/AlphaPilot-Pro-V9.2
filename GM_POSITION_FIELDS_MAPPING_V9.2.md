# 掘金SDK v3.0.183 持仓字段完整映射表

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558  
日期: 2026-04-24  
版本: V9.2

---

## 📊 掘金SDK持仓对象完整字段映射

根据实际测试，掘金SDK v3.0.183返回的持仓对象包含以下关键字段：

### 核心T+1合规字段（⭐ 必须严格遵守）

| SDK字段 | 含义 | 示例值 | 用途 | 是否可用于卖出 |
|---------|------|--------|------|--------------|
| `symbol` | 股票代码 | "SHSE.603538" | 标识股票 | - |
| `volume` | 总持仓数量 | 1800 | 显示用 | ❌ **不可直接用于卖出** |
| `available` | 总可平数量 | 1800 | ❌ **包含今日买入** | ❌ **不可用于卖出** |
| `available_now` | **当前可卖数量** | 200 | ✅ **止损/止盈必须用此字段** | ✅ **唯一正确的卖出依据** |
| `available_today` | 今日买入数量 | 1600 | 调试用，T+1不可卖 | ❌ |
| `volume_today` | 今日成交量 | 1600 | 调试用 | - |

### 成本价字段（按优先级排序）

| SDK字段 | 含义 | 示例值 | 用途 | 优先级 |
|---------|------|--------|------|--------|
| `vwap_open` | 开仓加权平均价 | 57.29 | ✅ **优先使用的成本价** | ⭐⭐⭐ 最高 |
| `vwap` | 加权平均价 | 57.29 | 成本价备选 | ⭐⭐ 次高 |
| `cost` | 持仓成本总额 | 103123.20 | 计算成本价（cost/volume） | ⭐ 最低 |

### 价格与盈亏字段

| SDK字段 | 含义 | 示例值 | 用途 |
|---------|------|--------|------|
| `last_price` | 最新价格 | 58.63 | 实时价格 |
| `market_value` | 持仓市值 | 103680.00 | 资产计算 |
| `fpnl` | 浮动盈亏 | 556.80 | 盈亏监控 |
| `fpnl_open` | 开仓浮动盈亏 | 556.80 | 盈亏监控备选 |

### 其他辅助字段

| SDK字段 | 含义 | 示例值 | 用途 |
|---------|------|--------|------|
| `account_id` | 账户ID | ae22ac8e-... | 账户标识 |
| `side` | 持仓方向 | 1 (多头) | 多空标识 |
| `order_frozen` | 订单冻结数量 | 0 | 挂单冻结 |
| `updated_at` | 更新时间 | 2026-04-24 13:41:31 | 最后更新时刻 |

---

## 🔧 Position类实现规范

### 正确实现（V9.2版本）

```python
class Position:
    """统一的持仓对象（包含成本价字段）"""
    def __init__(
        self,
        stock_code,
        volume,
        side=None,
        open_price=0.0,
        cost_price=0.0,
        avg_price=0.0,
        last_price=0.0,
        fpnl=0.0,
        market_value=0.0,
        raw=None
    ):
        self.stock_code = stock_code
        self.volume = volume
        self.side = side

        # 三个成本价字段全部写入真实成本价
        self.open_price = open_price
        self.cost_price = cost_price
        self.avg_price = avg_price

        self.last_price = last_price
        self.fpnl = fpnl
        self.market_value = market_value

        # 保存掘金原始持仓，便于调试
        self.raw = raw
        
        # ⭐⭐⭐ T+1合规核心字段：当前可卖数量（止损/止盈必须用此字段）
        # 根据掘金SDK v3.0.183实测：
        # - available: 总可平数量（含今日买入，❌不可用于卖出）
        # - available_now: 当前可卖数量（✅止损/止盈必须用此字段）
        # - available_today: 今日买入数量（仅用于调试）
        if raw:
            self.available_now = raw.get("available_now", 0)  # ✅ 当前可卖数量
            self.available_today = raw.get("available_today", 0)  # 今日买入数量
            self.volume_today = raw.get("volume_today", 0)  # 今日成交量
            
            # can_use_volume 作为兼容字段，映射到 available_now
            self.can_use_volume = self.available_now
        else:
            self.available_now = 0
            self.available_today = 0
            self.volume_today = 0
            self.can_use_volume = 0
```

### query_positions方法中的成本价映射

```python
def query_positions(self):
    raw_positions = get_position(account_id=self.account_id)
    positions = []

    for p in raw_positions:
        # ⭐ 成本价优先级：vwap_open > vwap > (cost / volume)
        vwap_open = p.get("vwap_open", 0.0)
        vwap = p.get("vwap", 0.0)
        cost = p.get("cost", 0.0)
        volume = p.get("volume", 0)

        # 计算最终成本价
        cost_price = 0.0
        if vwap_open and vwap_open > 0:
            cost_price = vwap_open  # ✅ 优先使用开仓均价
        elif vwap and vwap > 0:
            cost_price = vwap
        elif cost > 0 and volume > 0:
            cost_price = cost / volume

        # 三个字段全部写入成本价
        open_price = cost_price
        avg_price = cost_price

        pos = Position(
            stock_code=p["symbol"],
            volume=volume,
            side=p.get("side", None),
            open_price=open_price,
            cost_price=cost_price,
            avg_price=avg_price,
            last_price=p.get("last_price", 0.0),
            fpnl=p.get("fpnl", 0.0),
            market_value=p.get("market_value", 0.0),
            raw=p,
        )

        positions.append(pos)

    return positions
```

---

## ✅ T+1合规使用规范

### 场景1：止损模块

```python
# ❌ 错误做法：使用 available 或 volume
sell_volume = pos.volume // 2  # 违反T+1！
sell_volume = pos.available // 2  # 违反T+1！

# ✅ 正确做法：使用 available_now 或 can_use_volume
can_sell = pos.available_now  # 或 pos.can_use_volume
if can_sell <= 0:
    log("[止损跳过] {} 今日买入不可卖".format(code))
    return

sell_volume = min(pos.volume // 2, can_sell)
actual_sell = (sell_volume // 100) * 100  # 100股取整
```

### 场景2：止盈模块

```python
# ✅ 正确做法
positions = self.engine.query_positions()
for pos in positions:
    if pos.stock_code == code:
        can_sell = pos.available_now  # 或 pos.can_use_volume
        if can_sell <= 0:
            log("[止盈跳过] {} 今日买入不可卖".format(code))
            continue
        
        # 执行止盈逻辑
        actual_sell = min(sell_volume, can_sell)
```

### 场景3：集合竞价策略

```python
# ✅ 正确做法
for pos in positions:
    can_sell = pos.available_now
    if can_sell <= 0:
        log("[竞价跳过] {} 今日买入不可卖".format(pos.stock_code))
        continue
    
    # 执行卖出
    self.engine.order_stock(pos.stock_code, "SELL", can_sell, price, "集合竞价")
```

---

## 🧪 测试验证

### 测试脚本：test_position_fields.py

运行测试脚本验证字段映射是否正确：

```bash
cd d:\main_data
python test_position_fields.py
```

### 预期输出示例

```
================================================================================
📈 持仓 #1
================================================================================

【基本信息】
  股票代码: SHSE.603538
  股票名称: 美诺华

【持仓数量 - 核心字段】
  📦 总持仓 (volume): 1800 股
  ✅ 当前可卖 (available_now): 200 股
  ✅ 可平数量 (can_use_volume): 200 股
  ❌ 总可平 (available): 1800 股（⚠️ 包含今日买入，不可用于卖出）

【T+1合规验证】
  📊 今日买入: 1600 股
  ⚠️  部分可卖：200/1800 股
  💡 昨日持仓: 200 股（可卖）

【成本价字段】
  ✅ VWAP_Open (vwap_open): 57.29 元（优先使用）
  ✅ VWAP (vwap): 57.29 元
  ✅ 成本总额 (cost): 103123.20 元
  💡 计算成本价: 57.29 元

【价格与盈亏】
  最新价 (last_price): 58.63 元
  持仓市值 (market_value): 103680.00 元
  浮动盈亏 (fpnl): 556.80 元
```

---

## ⚠️ 常见错误与纠正

### 错误1：误用 available 字段

```python
# ❌ 错误
can_sell = pos.available  # 包含今日买入，会违反T+1规则

# ✅ 正确
can_sell = pos.available_now  # 或 pos.can_use_volume
```

### 错误2：直接使用 volume 计算卖出数量

```python
# ❌ 错误
sell_volume = pos.volume // 2  # 可能包含今日买入的股票

# ✅ 正确
can_sell = pos.available_now
sell_volume = min(pos.volume // 2, can_sell)
```

### 错误3：忽略100股取整

```python
# ❌ 错误
self.engine.order_stock(code, "SELL", sell_volume, price)  # 可能不是100的倍数

# ✅ 正确
actual_sell = (sell_volume // 100) * 100
if actual_sell == 0 and can_sell >= 100:
    actual_sell = 100  # 至少卖出1手
self.engine.order_stock(code, "SELL", actual_sell, price)
```

---

## 📝 总结

### 核心原则

1. **T+1合规第一**：所有卖出操作必须基于 `available_now` 或 `can_use_volume`
2. **成本价优先级**：`vwap_open` > `vwap` > `(cost / volume)`
3. **100股取整**：买入和卖出都必须符合A股交易规则
4. **日志透明**：记录总持仓、可卖数量、今日买入数量的对比

### 代码审查清单

- [ ] 所有卖出操作使用 `pos.available_now` 或 `pos.can_use_volume`
- [ ] 检查 `can_sell <= 0` 的情况并跳过
- [ ] 卖出数量向下取整为100的整数倍
- [ ] 日志显示"总持仓"和"可卖数量"的对比
- [ ] 成本价使用 `vwap_open` 优先

---

## 📞 技术支持

如有问题，请联系：
- 邮箱: 497720537@qq.com
- 电话: 13392077558

---

**记住：T+1是A股铁律，任何绕过此规则的行为都会导致合规风险！** ⚖️
