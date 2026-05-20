打折
# AlphaPilot Pro V10 — 数据管线设计（DATA PIPELINE）

## 📌 概述

本文件定义 AlphaPilot Pro V10 的数据管线（Data Pipeline）设计，目标是：

- 为 **强化学习环境（RL Env）** 提供稳定、结构化、可复现的数据输入  
- 统一历史数据、实时数据、因子数据的格式  
- 确保 **训练环境 与 实盘环境 使用同一套数据接口与字段定义**

V10 的数据管线遵循三个原则：

1. **单一事实源（Single Source of Truth）**  
2. **离线训练 / 在线推理 一致性（Train–Inference Consistency）**  
3. **与 V9.2 事件驱动架构兼容**

---

## 1. 数据总体流程（Data Flow Overview）

```text
原始行情数据（行情源 / 本地缓存）
        │
        ▼
数据清洗与对齐（Data Cleaning & Alignment）
        │
        ▼
特征工程（Feature Engineering / 因子计算）
        │
        ├──> 保存为训练集（Training Dataset）
        │
        └──> 实时特征流（Real-time Feature Stream）
                     │
                     ▼
              RL 环境 / 策略模块
2. 数据源（数据来源）
2.1 历史行情数据（历史市场数据）
日线 / 分钟线（建议：1min / 5min）

字段：

开盘、高、低、收盘、成交量、金额

pre_close

limit_up， limit_down（如有）

来源：

掘金 / QMT / 本地 CSV / Parquet

2.2 实时行情数据（Real-time Market Data）
与 V9.2 使用的实时行情接口保持一致

字段：

last_price

 bid_price1，ask_price1

体积，数量

time（精确到秒）

2.3 衍生数据 / 因子数据（Factor Data）
量比（体积比）

换手率（Turnover）

板块热度（Sector Heat）

大盘强弱（Market Strength）

分时强弱（Intraday Momentum）

资金流向（资本流动）

3. 特征工程（特征工程）
3.1 K 线特征（K 线特征）
过去 N 根 K 线（例如 N=30）

特征：

收盘价 / pre_close - 1（收益率）

高/低（波动幅度）

成交量（成交量）

金额（成交额）

3.2 技术指标（技术指标）
可选（按需启用）：

文学学士 / EMA

RSI

MACD

ATR

波林带

3.3 行为特征（行为特征）
量比（相对过去一段时间的成交量）

换手率

分时强弱（当前价相对当日 VWAP / 开盘价）

大盘联动（标的相对指数的超额收益）

3.4 因子向量格式（统一格式）
统一为一个固定长度的向量，例如：

JSON
{
  "code": "600821.SH",
  "datetime": "2025-04-25 10:32:00",
  "features": {
    "kbar": [...],
    "tech": [...],
    "behavior": [...],
    "market": [...]
  }
}
RL 环境中会将这些展开为一个 numpy 向量 / torch 张量。

4. 训练数据集构建（Training Dataset）
4.1 样本定义（示例定义）
每一个训练样本包含：

state_t：时间 t 的状态向量（由特征工程生成）

action_t：在 t 时刻采取的动作（来自历史策略 / 模拟策略 / 行为策略）

reward_t：在 t→t+1 之间获得的奖励（由奖励函数计算）

state_t+1：下一时刻的状态

done：是否结束（如：到达样本末尾 / 触发强制平仓）

4.2 数据切片（Rolling Window）
对每只股票、每一段时间，按时间顺序滚动生成：

文本
(state_t, action_t, reward_t, state_t+1, done)
用于：

PPO / DQN / A2C 等 RL 算法训练

行为克隆（Behavior Cloning）预训练（可选）

5. 实盘特征流（实时特征流）
5.1 与训练数据一致的特征构建
实盘时，必须使用与训练时 完全一致 的特征构建逻辑：

同样的 K 线长度 N

同样的技术指标参数

同样的因子标准化方式

同样的字段顺序

建议将特征构建逻辑封装在：

文本
env/state_builder.py
训练与实盘共用。

5.2 实时数据 → 状态向量
流程：

文本
实时行情 → 更新本地缓存 → 调用 state_builder → 生成 state 向量 → 输入 RL 策略
6. 数据存储与格式（Storage & Format）
6.1 离线数据格式
建议使用：

Parquet（高效、列式存储）

或 HDF5 / 羽毛

按以下维度分区：

Symbol（股票代码）

date（交易日）

6.2 在线缓存
实盘运行时：

使用内存缓存最近 N 根 K 线

使用环形缓冲区（Ring Buffer）结构

避免频繁 IO

7. 与 V9.2 架构的兼容性
7.1 复用现有行情接口
V9.2 中用于即时策略 / 延时策略的行情接口可以直接复用

新增一层：Feature Layer（特征层），专门为 RL 构建状态

7.2 复用现有风控与执行模块
数据管线只负责“喂数据给大脑”

下单、风控、资金管理仍由 V9.2 的 TraderEngine 与 RiskControl 负责

8. 数据质量与风控（数据质量与保障）
8.1 缺失值处理
缺 K 线 → 丢弃样本或前向填充

缺因子 → 使用中性值（如 0）或均值填充

8.2 异常值处理
极端价格波动（如 > ±20%）→ 标记为异常

成交量为 0 → 视为停牌

8.3 训练 / 验证 / 测试集划分
按时间划分（基于时间的分割）

避免未来信息泄露（Look-ahead Bias）

9. 未来扩展（未来扩展）
加入 Level-2 盘口数据（Order Book）

加入资金流向（北向资金 / 主力资金）

加入新闻 / 公告情绪因子（NLP）

加入多资产（指数 / 期货 / 期权）数据

10. 结语
数据管线是 AlphaPilot Pro V10 的“血液系统”。 只有当数据流干净、一致、可复现，强化学习策略才能学到 真实、稳定、可实盘的交易行为。

本文件与以下文档配合使用：

V10_ARCHITECTURE.md

RL_ENV_DESIGN.md

REWARD_SHAPING_V10.md

代码

---

接下来，如果你愿意，我们可以顺着这份数据管线文档，继续做两件非常关键、也非常“爽”的事：

1. 把这里定义的 **state_builder.py 代码骨架** 写出来  
2. 设计一份 **训练数据构建脚本 build_training_dataset.py**，把历史数据真正转成 RL 可用的 