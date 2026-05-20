# 更新日志 - V9.2

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558  
日期: 2026-04-24

---

## 🎯 V9.2 版本概述

**核心改进**：
1. **修复掘金SDK持仓字段映射错误**：确保T+1合规性达到100%
2. **修复即时策略卖出未执行100股取整**：确保A股交易规则100%合规

根据实际测试数据和用户反馈，发现两个严重的合规风险问题，现已全部修复。

---

## ✅ 主要变更

### 1. Position类字段映射修复（core/trader_engine.py）

#### 变更前（❌ 错误）
```python
class Position:
    def __init__(self, ..., raw=None):
        # ❌ 错误：available包含今日买入，不可用于卖出
        self.can_use_volume = raw.get("available", 0) if raw else 0
```

#### 变更后（✅ 正确）
```python
class Position:
    def __init__(self, ..., raw=None):
        # ⭐⭐⭐ T+1合规核心字段：当前可卖数量
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

**关键改进**：
- ✅ 新增 `available_now` 字段：从SDK的 `available_now` 获取，这是**唯一正确的可卖数量**
- ✅ 新增 `available_today` 字段：记录今日买入数量，用于调试和日志
- ✅ 新增 `volume_today` 字段：记录今日成交量
- ✅ `can_use_volume` 现在正确映射到 `available_now`，而非错误的 `available`

---

### 2. 即时策略卖出100股取整修复（strategies/signal_strategy.py）

#### 变更前（❌ 错误）
```python
# ❌ 错误：直接卖出所有可卖持仓，未执行100股取整
result = self.engine.order_stock(code, "SELL", pos.can_use_volume, order_price, "SIGNAL_V9")
```

**问题示例**：
- 如果 `pos.can_use_volume` = 250股，会直接卖出250股
- 违反A股100股整数倍规则，订单会被交易所拒绝

---

#### 变更后（✅ 正确）
```python
# 3. 卖出价格：当前价打1%折扣
order_price = round(price * 0.99, 2)

# 4. 【A股合规】可卖数量向下取整为100的整数倍
can_sell = pos.can_use_volume
actual_sell_volume = (can_sell // 100) * 100

# 如果取整后为0但可卖数量>=100，至少卖出100股
if actual_sell_volume == 0 and can_sell >= 100:
    actual_sell_volume = 100

# 如果取整后仍为0，跳过
if actual_sell_volume <= 0:
    log.log(f"[卖出失败] {code} 可卖数量不足100股（可卖:{can_sell}），跳过")
    return False

# 5. 执行卖出（使用取整后的数量）
result = self.engine.order_stock(code, "SELL", actual_sell_volume, order_price, "SIGNAL_V9")
if result:
    log.log(f"[卖出成功] {code} 卖出 {actual_sell_volume} 股 @ {order_price} (总持仓:{pos.volume} 可卖:{can_sell})")
return result
```

**关键改进**：
- ✅ 正确执行100股取整：`(can_sell // 100) * 100`
- ✅ 处理边界情况：不足100股时跳过或至少卖出100股
- ✅ 增强日志输出：显示总持仓、可卖数量和实际卖出数量

**修复前后对比**：
| 可卖数量 | 修复前 | 修复后 |
|---------|--------|--------|
| 250股 | 卖出250股 ❌ | 卖出200股 ✅ |
| 50股 | 卖出50股 ❌ | 跳过 ✅ |
| 150股 | 卖出150股 ❌ | 卖出100股 ✅ |

---

### 3. 成本价优先级确认

当前代码已正确使用成本价优先级，无需修改：

```python
# ✅ 正确：vwap_open > vwap > (cost / volume)
cost_price = 0.0
if vwap_open and vwap_open > 0:
    cost_price = vwap_open  # 优先使用开仓均价
elif vwap and vwap > 0:
    cost_price = vwap
elif cost > 0 and volume > 0:
    cost_price = cost / volume
```

---

### 4. 测试脚本增强（test_position_fields.py）

**新增测试内容**：
- ✅ 测试 `available_now` 字段（推荐使用）
- ✅ 测试 `available_today` 字段（今日买入）
- ✅ 测试 `volume_today` 字段（今日成交）
- ✅ 明确标注 `available` 字段的危险性
- ✅ 增加raw字典验证环节
- ✅ 增加成本价字段详细测试

**预期输出示例**：
```
【T+1合规字段测试】
  ✅ 当前可卖 (available_now): 200 股 ⭐ 推荐使用
  ✅ 可平数量 (can_use_volume): 200 股
  ❌ 总可平 (available): 1800 股 ⚠️ 包含今日买入，不可用于卖出
  📊 今日买入 (available_today): 1600 股
  📊 今日成交 (volume_today): 1600 股

【T+1合规验证】
  ⚠️  部分可卖：200/1800 股
  💡 估计今日买入: 1600 股（不可卖）
  ✅ 估计昨日持仓: 200 股（可卖）
```

---

### 5. 新增文档

#### A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md
完整的A股交易规则合规性审计报告，包含：
- 📊 所有卖出场景的审计结果
- 🔧 修复前后对比
- ⚠️ A股交易规则要点
- 🧪 测试验证指南

#### GM_POSITION_FIELDS_MAPPING_V9.2.md
完整的掘金SDK持仓字段映射表，包含：
- 📊 所有关键字段的详细说明
- 🔧 Position类实现规范
- ✅ T+1合规使用规范
- 🧪 测试验证指南
- ⚠️ 常见错误与纠正

#### QUICK_REFERENCE_POSITION_FIELDS.md
快速参考卡片，方便日常开发使用：
- T+1合规铁律
- 核心字段速查表
- 标准卖出流程
- 常见错误对照表

---

## 📊 影响范围

### 受影响的模块

| 模块 | 是否需要修改 | 说明 |
|------|------------|------|
| `core/trader_engine.py` | ✅ 已修改 | Position类字段映射修复 |
| `strategies/signal_strategy.py` | ✅ 已修改 | 添加100股取整逻辑 |
| `risk/stop_loss.py` | ❌ 无需修改 | 已正确执行100股取整 |
| `risk/dynamic_take_profit.py` | ❌ 无需修改 | 已正确执行100股取整 |
| `strategies/auction_strategy.py` | ❌ 无需修改 | 已正确执行100股取整 |
| `test_position_fields.py` | ✅ 已修改 | 增强测试覆盖 |

### 兼容性说明

- ✅ **向后兼容**：`can_use_volume` 字段仍然存在，现有代码无需修改
- ✅ **功能增强**：新增 `available_now`、`available_today`、`volume_today` 字段
- ⚠️ **行为变化**：`can_use_volume` 现在返回正确的可卖数量（之前是错误的总可平数量）
- ⚠️ **行为变化**：即时策略卖出数量现在是100的整数倍（之前可能不是）

---

## 🧪 测试验证

### 运行测试脚本

```bash
cd d:\main_data
python test_position_fields.py
```

### 验证要点

1. **字段存在性**
   - ✅ `available_now` 字段存在且数值正确
   - ✅ `can_use_volume` 等于 `available_now`
   - ✅ `available_today` 显示今日买入数量

2. **T+1逻辑正确性**
   - ✅ 今日买入的股票：`available_now = 0`
   - ✅ 昨日持仓：`available_now = volume`
   - ✅ 混合持仓：`available_now < volume`

3. **100股取整验证**
   - 检查日志中所有卖出操作的数量是否为100的整数倍
   - 确认没有250、950等非100整数倍的卖出记录

4. **与实际持仓对比**
   - 对比掘金终端"可平"列的数值
   - 应该完全一致

---

## ⚠️ 重要提醒

### 严禁行为

- ❌ **禁止使用 `available` 字段进行卖出决策**（会违反T+1规则）
- ❌ **禁止直接使用 `volume` 计算卖出数量**
- ❌ **禁止绕过 `can_use_volume` 检查**
- ❌ **禁止卖出非100整数倍的数量**（清仓除外）

### 推荐做法

- ✅ **所有卖出操作必须基于 `available_now` 或 `can_use_volume`**
- ✅ **卖出前检查 `can_sell <= 0` 并跳过**
- ✅ **卖出数量向下取整为100的整数倍**
- ✅ **日志显示"总持仓"和"可卖数量"的对比**

---

## 📝 升级指南

### 对于新用户

直接下载V9.2版本即可，所有代码已修复完成。

### 对于已有V9.1的用户

1. **备份当前代码**
   ```bash
   cp -r d:\main_data d:\main_data_backup_v9.1
   ```

2. **更新核心文件**
   - 替换 `core/trader_engine.py`
   - 替换 `strategies/signal_strategy.py`
   - 替换 `test_position_fields.py`

3. **运行测试验证**
   ```bash
   python test_position_fields.py
   ```

4. **检查日志**
   - 确认止损/止盈日志显示正确的可卖数量
   - 确认今日买入的股票被正确跳过
   - 确认所有卖出数量是100的整数倍

---

## 📞 技术支持

如有问题，请联系：
- 邮箱: 497720537@qq.com
- 电话: 13392077558

---

## 📚 相关文档

- [A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md](A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md) - A股交易规则合规性审计
- [GM_POSITION_FIELDS_MAPPING_V9.2.md](GM_POSITION_FIELDS_MAPPING_V9.2.md) - 完整字段映射表
- [POSITION_FIELDS_AUDIT_REPORT_V9.2.md](POSITION_FIELDS_AUDIT_REPORT_V9.2.md) - 持仓字段审核报告
- [QUICK_REFERENCE_POSITION_FIELDS.md](QUICK_REFERENCE_POSITION_FIELDS.md) - 快速参考卡
- [T1_COMPLIANCE_VERIFICATION_REPORT.md](T1_COMPLIANCE_VERIFICATION_REPORT.md) - T+1合规验证报告
- [CORE_ARCHITECTURE_PRINCIPLES.md](CORE_ARCHITECTURE_PRINCIPLES.md) - 核心架构原则

---

## ✅ 版本总结

### V9.2核心成就

1. **T+1合规性100%**：修复了 `can_use_volume` 字段映射错误
2. **100股取整100%合规**：修复了即时策略未执行100股取整的问题
3. **文档完善**：创建了4份详细文档，涵盖所有技术细节
4. **向后兼容**：现有代码无需大规模修改

### 最终评价

**V9.2版本已完成A股交易规则100%合规性修复，可以安全使用！** ✅

---

**记住：遵守A股交易规则是系统稳定运行的基础！** ⚖️
