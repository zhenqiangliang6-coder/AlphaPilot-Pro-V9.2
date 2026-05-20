# AlphaPilot Pro V9.2 → V10.0 升级路线图 / Upgrade Roadmap

**AlphaPilot Pro V9.2 → V10.0 Upgrade Roadmap**

## 总目标 / Overall Goal

**V10.0 = AI 直接做交易决策**

**V10.0 = AI Makes Trading Decisions Directly**

V10.0 的核心是：AI 不再预测涨跌，而是直接输出买入 / 卖出 / 加仓 / 减仓 / 空仓动作。系统从"信号驱动"升级为"策略驱动"。

The core of V10.0 is: AI no longer predicts price direction, but directly outputs actions: buy / sell / add position / reduce position / go flat. The system upgrades from "signal-driven" to "strategy-driven".

---

## 升级路线图总览 / Upgrade Roadmap Overview

| 版本 / Version | 核心成果 / Key Achievement | 难度 / Difficulty | 是否需要改架构 / Architecture Change |
|---|---|---|---|
| V9.2 (当前 / Current) | 事件驱动 + 双策略 + 风控体系 / Event-driven + Dual Strategy + Risk Control | - | - |
| V9.3 | AI 预测模块 / AI Prediction Module | - | - |
| V9.4 | 多因子融合 (AI + 技术因子 + 量比) / Multi-factor Fusion (AI + Technical Factors + Volume Ratio) | - | - |
| V10.0 | 强化学习策略 (RL) 直接做决策 / Reinforcement Learning (RL) Direct Decision Making | - | 轻微 (Minor) |
| V10.1-V10.6 | 真实交易成本、滑点、短线奖励 shaping / Real Trading Costs, Slippage, Short-term Reward Shaping | - | - |

---

## 第一阶段 / Phase 1: V9.4 多因子融合 / Multi-factor Fusion (Preparation for RL)

### 目标 / Goal

让 AI 的输入更丰富，让 RL 有更好的"世界模型"。

Enrich AI input and provide RL with a better "world model".

### 任务 / Tasks

- 加入更多因子：量比、换手率、分时强弱、大盘联动、板块热度、资金流向
- Add more factors: volume ratio, turnover rate, intraday strength, market correlation, sector heat, capital flow
- 统一因子格式 → 生成 1×N 因子向量
- Standardize factor format → Generate 1×N factor vector
- 升级信号文件格式 (兼容旧版)
- Upgrade signal file format (backward compatible)

```json
{
  "code": "600821.SH",
  "factors": {
    "volume_ratio": 3.8,
    "turnover": 0.023,
    "market_strength": 0.7,
    "sector_heat": 0.82
  }
}
```

---

## 第二阶段 / Phase 2: V10.0 强化学习策略 / Reinforcement Learning Strategy (Core Version)

### 定义 / Definition

AI 直接输出动作：

AI directly outputs actions:

- `0` = 不动 / Do Nothing
- `1` = 买入 / Buy
- `2` = 卖出 / Sell
- `3` = 加仓 / Add Position
- `4` = 减仓 / Reduce Position

### 新增模块 (兼容现有架构) / New Modules (Compatible with Existing Architecture)

```
env/
  ├── state_builder.py      # 构建状态向量 / Build state vector
  ├── reward_engine.py      # 奖励函数 (短线风格) / Reward function (short-term style)
  ├── simulator.py          # 仿真撮合 (含滑点、手续费) / Simulation matching (incl. slippage, fees)
  └── env.py                # 主环境 / Main environment

strategies/
  └── rl_strategy.py        # RL 策略模块 / RL Strategy Module

train_rl_agent.py          # 训练脚本 / Training script
```

---

## 第三阶段 / Phase 3: V10.1-V10.6 (短线风格强化学习优化 / Short-term Style RL Optimization)

### V10.1: 加入真实交易成本 / Add Real Trading Costs

- 手续费 / Commission Fees
- 印花税 / Stamp Tax
- 滑点 (0.02%-0.08%) / Slippage (0.02%-0.08%)
- T+1 限制 / T+1 Restriction

### V10.2: 短线奖励 Shaping / Short-term Reward Shaping (3-4 Day Holding Style)

- 持仓超过 4 天 → 惩罚 / Holding over 4 days → Penalty
- 盈利超过 2% → 奖励加倍 / Profit over 2% → Double Reward
- 亏损超过 -1.2% → 惩罚加倍 / Loss over -1.2% → Double Penalty
- 快速止盈 (1-3 天) → 奖励加成 / Quick Profit Taking (1-3 days) → Bonus Reward

### V10.3: RL 风控 / RL Risk Control (Learn Your Stop-Loss System)

- -0.5% 进入观察 / -0.5% Enter Monitoring
- -1.2% 减半 / -1.2% Reduce by Half
- -2.5% 清仓 / -2.5% Close Position

### V10.4: RL 大盘联动 / RL Market-Wide Coordination

- 大盘弱 → 不买 / Weak Market → Don't Buy
- 大盘强 → 放宽阈值 / Strong Market → Relax Thresholds
- 下午量比更严格 / Stricter Volume Ratio in Afternoon

### V10.5: 多股票并行训练 / Multi-Stock Parallel Training (Portfolio RL)

- 单股票 → 多股票 / Single Stock → Multiple Stocks
- 单仓位 → 多仓位 / Single Position → Multiple Positions

### V10.6: 实盘级 RL 策略 / Live Trading RL Strategy (Final Version)

- 3-4 天持仓 / 3-4 Day Holding
- 高频但不乱交易 / High Frequency but Disciplined Trading
- 止损果断 / Decisive Stop Loss
- 止盈灵活 / Flexible Profit Taking
- 资金利用率高 / High Capital Utilization
- 交易成本低 / Low Trading Costs
- 适应震荡行情 / Adapt to Volatile Markets

---

## 升级时间表 (工程可执行) / Upgrade Timeline (Executable Plan)

| 阶段 / Stage | 版本 / Version | 时间 / Duration | 产出 / Deliverable |
|---|---|---|---|
| 阶段1 / Stage 1 | V9.4 | 1-2 周 / 1-2 weeks | 多因子融合 / Multi-factor Fusion |
| 阶段2 / Stage 2 | V10.0 | 3-6 周 / 3-6 weeks | RL 环境 + RL 策略 / RL Environment + RL Strategy |
| 阶段3 / Stage 3 | V10.1 | 1 周 / 1 week | 交易成本 / Trading Costs |
| 阶段4 / Stage 4 | V10.2 | 1 周 / 1 week | 短线奖励 shaping / Short-term Reward Shaping |
| 阶段5 / Stage 5 | V10.3 | 1 周 / 1 week | RL 风控 / RL Risk Control |
| 阶段6 / Stage 6 | V10.4 | 1 周 / 1 week | 大盘联动 / Market-Wide Coordination |
| 阶段7 / Stage 7 | V10.5 | 1 周 / 1 week | 多股票训练 / Multi-Stock Training |
| 阶段8 / Stage 8 | V10.6 | 1 周 / 1 week | 实盘级 RL 策略 / Live Trading RL Strategy |

---

## 结语 / Conclusion

这份路线图完全基于你当前的 V9.2 架构、短线风格、事件驱动框架设计，是未来 1-2 个月可直接落地的工程蓝图。

This roadmap is fully based on your current V9.2 architecture, short-term trading style, and event-driven framework design. It is an engineering blueprint that can be directly implemented in the next 1-2 months.
