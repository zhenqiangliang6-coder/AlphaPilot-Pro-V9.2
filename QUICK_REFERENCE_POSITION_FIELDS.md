# 掘金SDK持仓字段快速参考卡

**版本**: V9.2 | **日期**: 2026-04-24 | **团队**: Alphapilot智能体

---

## 🚨 T+1合规铁律（必须遵守）

```python
# ✅ 唯一正确的卖出依据
can_sell = pos.available_now  # 或 pos.can_use_volume

# ❌ 严禁使用的字段
can_sell = pos.available      # 包含今日买入，违反T+1！
can_sell = pos.volume         # 总持仓，违反T+1！
```

---

## 📊 核心字段速查表

| 字段名 | SDK来源 | 含义 | 用途 | 优先级 |
|--------|---------|------|------|--------|
| `available_now` | `raw['available_now']` | **当前可卖数量** | ✅ 止损/止盈卖出 | ⭐⭐⭐ |
| `can_use_volume` | 映射到`available_now` | 兼容字段 | ✅ 同available_now | ⭐⭐⭐ |
| `available_today` | `raw['available_today']` | 今日买入数量 | 📊 调试用 | - |
| `volume` | `raw['volume']` | 总持仓 | 📦 显示用 | - |
| `available` | `raw['available']` | 总可平（含今日） | ❌ **禁止用于卖出** | 🚫 |

---

## 💰 成本价优先级

```python
# 优先级：vwap_open > vwap > (cost / volume)
if pos.raw.get('vwap_open', 0) > 0:
    cost_price = pos.raw['vwap_open']  # ⭐ 优先
elif pos.raw.get('vwap', 0) > 0:
    cost_price = pos.raw['vwap']
else:
    cost_price = pos.raw['cost'] / pos.raw['volume']
```

---

## ✅ 标准卖出流程

```python
# 1. 查询持仓
positions = engine.query_positions()
pos = next((p for p in positions if p.stock_code == code), None)

if not pos:
    return False

# 2. 检查可卖数量（T+1合规）
can_sell = pos.available_now  # ✅ 正确
if can_sell <= 0:
    log(f"[跳过] {code} 今日买入不可卖")
    return False

# 3. 计算卖出数量
sell_volume = min(calculated_volume, can_sell)

# 4. 100股取整
actual_sell = (sell_volume // 100) * 100
if actual_sell == 0 and can_sell >= 100:
    actual_sell = 100  # 至少1手

# 5. 执行卖出
engine.order_stock(code, "SELL", actual_sell, price, reason)
```

---

## 🔍 调试技巧

### 查看完整持仓信息

```python
for pos in positions:
    print(f"股票: {pos.stock_code}")
    print(f"  总持仓: {pos.volume}")
    print(f"  可卖: {pos.available_now} ⭐")
    print(f"  今日买入: {pos.available_today}")
    print(f"  成本价: {pos.cost_price:.2f}")
    print(f"  最新价: {pos.last_price:.2f}")
    print(f"  盈亏: {pos.fpnl:.2f}")
```

### 验证T+1逻辑

```bash
# 运行测试脚本
python test_position_fields.py
```

---

## ⚠️ 常见错误

| 错误代码 | 问题 | 修正 |
|---------|------|------|
| `pos.available` | 包含今日买入 | 改用 `pos.available_now` |
| `pos.volume // 2` | 可能包含今日买入 | 先检查 `available_now` |
| 未检查 `can_sell <= 0` | 可能对0股下单 | 添加检查并跳过 |
| 未100股取整 | 订单被拒 | `(vol // 100) * 100` |

---

## 📞 紧急联系

- 邮箱: 497720537@qq.com
- 电话: 13392077558

---

**记住：T+1是A股铁律，违规会导致账户风险！** ⚖️
