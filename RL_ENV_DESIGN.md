RL_ENV_DESIGN.md
AlphaPilot Pro V10 - 强化学习环境设计(RL Environment Design)​
 概述
本文件定义 AlphaPilot Pro V10 的强化学习环境(RL Environment)​,​包括:​
状态空间(State Space)​
动作空间(Action Space)​
奖励函数接口
撮合系统(Execution Simulator)​
交易成本模型
T+1 规则
环境重置与步进逻辑
环境遵循 OpenAI Gym 接口规范,​确保训练与实盘行为一致(Isomorphic Design)​。​

1. 环境结构
env/
 ├── env.py
 ├── state_builder.py
 ├── reward_engine.py
 ├── simulator.py
 └── utils.py

2. 状态空间设计(State Space)​
V10 的状态由三大类特征组成:​市场特征、​持仓特征、​环境特征。​
2.1 市场特征(Market Features)​
OHLCV(过去 N 根 K 线)​
量比(Volume Ratio)​
换手率(Turnover)​
板块热度(Sector Heat)​
大盘强弱(Market Strength)​
分时强弱(Intraday Momentum)​
2.2 持仓特征(Position Features)​
当前持仓量
成本价
浮盈浮亏
持仓天数
是否可卖(T+1)​
2.3 环境特征(Env Features)​
当前时间(分钟级)​
是否在交易窗口
是否触发风控

3. 动作空间(Action Space)​
0 = 不动
1 = 买入
2 = 卖出
3 = 加仓
4 = 减仓
动作经过 simulator.py 执行,​包含:​
手续费
滑点
T+1 限制
100 股取整

4. 奖励函数接口
奖励函数由 reward_engine.py 实现:​
reward = reward_engine.compute(
    pnl=pnl,
    position=position,
    holding_days=holding_days,
    action=action,
    market_state=market_state
)
奖励函数细节见 REWARD_SHAPING_V10.md。​

5. 撮合系统(Execution Simulator)​
模拟真实交易所行为,​确保训练与实盘一致。​
5.1 手续费模型
买入:​万分之 2.5
卖出:​万分之 2.5 + 印花税 0.1%
5.2 滑点模型
默认 0.02%-0.08%
5.3 T+1 限制
今日买入 → 今日不可卖
5.4 100 股取整
买卖必须为 100 的整数倍

6. 环境步进逻辑(Step Function)​
action → simulator → 更新持仓 → 计算奖励 → 构建下一个状态

7. 环境重置(Reset)​
清空持仓
重置资金
重置时间指针
重置奖励累计

8. 训练与实盘一致性(Isomorphic Design)​
所有规则(T+1、​滑点、​手续费)​与实盘一致
所有状态特征与实盘一致
所有动作与实盘一致

9. 结语
RL 环境是 V10 的核心基础,​决定了策略能否学到真实可用的交易行为。​