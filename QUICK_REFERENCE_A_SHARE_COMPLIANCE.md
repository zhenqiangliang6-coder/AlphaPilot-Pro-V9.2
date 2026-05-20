# A股交易规则合规性快速参考卡

**版本**: V9.2 | **日期**: 2026-04-24 | **团队**: Alphapilot智能体

---

## 🚨 A股交易规则铁律（必须遵守）

### 1. 100股整数倍规则
```python
# ✅ 正确的卖出数量计算
can_sell = pos.available_now  # 或 pos.can_use_volume
actual_sell = (can_sell // 100) * 100

if actual_sell == 0 and can_sell >= 100:
    actual_sell = 100  # 至少卖出1手

if actual_sell <= 0:
    return False  # 可卖不足100股，跳过
```

### 2. T+1制度合规
```python
# ✅ 正确的T+1检查
can_sell = pos.available_now  # ✅ 当前可卖数量
if can_sell <= 0:
    log(f"今日买入不可卖，跳过 {code}")
    return False
```

---

## 📊 卖出场景合规性检查表

| 场景 | 文件 | 100股取整 | T+1检查 | 状态 |
|------|------|----------|---------|------|
| 一级止损 | `risk/stop_loss.py` | ✅ | ✅ | 合规 |
| 二级止损 | `risk/stop_loss.py` | ✅ | ✅ | 合规 |
| 快速止盈 | `risk/dynamic_take_profit.py` | ✅ | ✅ | 合规 |
| 波段止盈 | `risk/dynamic_take_profit.py` | ✅ | ✅ | 合规 |
| 强势止盈 | `risk/dynamic_take_profit.py` | ✅ | ✅ | 合规 |
| 精英卖出 | `strategies/auction_strategy.py` | ✅ | ✅ | 合规 |
| 即时卖出 | `strategies/signal_strategy.py` | ✅ | ✅ | **已修复** |

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

# 3. 100股取整
actual_sell = (can_sell // 100) * 100
if actual_sell == 0 and can_sell >= 100:
    actual_sell = 100  # 至少1手

# 4. 最终检查
if actual_sell <= 0:
    log(f"[跳过] {code} 可卖数量不足100股")
    return False

# 5. 执行卖出
success = engine.order_stock(code, "SELL", actual_sell, price, reason)
```

---

## ⚠️ 常见违规情况

| 违规代码 | 问题 | 修正 |
|---------|------|------|
| `pos.available` | 包含今日买入 | 改用 `pos.available_now` |
| `pos.volume` | 总持仓 | 先检查 `available_now` |
| `pos.can_use_volume = 250` | 非100倍数 | `(250 // 100) * 100 = 200` |
| `pos.can_use_volume = 50` | 不足1手 | 跳过或检查 `>= 100` |

---

## 🧪 验证方法

### 检查日志
```
# ✅ 正确日志（数量是100的倍数）
[卖出成功] SHSE.603538 卖出 200 股 @ 58.63

# ❌ 错误日志（数量不是100的倍数）
[卖出成功] SHSE.603538 卖出 250 股 @ 58.63  ← 违规！
```

### 运行测试
```bash
python test_position_fields.py
```

---

## 📞 紧急联系

- 邮箱: 497720537@qq.com
- 电话: 13392077558

---

**记住：100股整数倍是A股铁律，违规订单会被交易所拒绝！** ⚖️
