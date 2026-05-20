[Copy]REWARD_SHAPING_V10.md
AlphaPilot Pro V10 - 奖励函数设计(Reward Shaping)​
 概述
V10 奖励函数专为 短线交易(3-4 天持仓)​ 设计,​目标是让 AI 学会:​
快速止盈
果断止损
避免长时间持仓
提高资金利用率
避免无意义交易
避免尾盘追高
避免大盘弱势买入
奖励函数是整个 RL 策略的灵魂,​它决定了智能体最终会学成什么样的交易风格。​

1. 奖励函数总公式
Reward = 
    pnl_reward
  + holding_penalty
  + risk_penalty
  + action_penalty
  + market_alignment_bonus
奖励由五部分组成,​每一部分都对应你短线交易风格中的关键行为。​

2. 盈亏奖励(PNL Reward)​
pnl_reward = (current_value - previous_value) / previous_value
并加入短线加成:​
盈利 > 2% → 奖励 × 1.5
盈利 > 4% → 奖励 × 2
目的:​鼓励快速止盈,​而不是拖到大涨才卖。​

3. 持仓天数惩罚(Holding Penalty)​
if holding_days > 4:
    penalty = -0.002 * (holding_days - 4)
目的:​
强制 AI 遵守你的短线风格
避免“越亏越拿”或“死拿不动”

4. 风控惩罚(Risk Penalty)​
if pnl < -0.5%:  penalty -= 0.002
if pnl < -1.2%:  penalty -= 0.01
if pnl < -2.5%:  penalty -= 0.03
完全继承你 V9.2 的分级止损逻辑:​
-0.5% 进入观察
-1.2% 减半
-2.5% 清仓
目的:​让 RL 学会“亏损要快刀斩乱麻”。​

5. 动作惩罚(Action Penalty)​
频繁交易 → 惩罚
无意义加仓 → 惩罚
尾盘买入 → 惩罚
具体实现:​
每次下单固定小惩罚(避免乱点)​
同方向连续下单额外惩罚(避免无脑加仓)​
14:45 后买入额外惩罚(避免尾盘诱多)​

6. 大盘联动奖励(Market Alignment Bonus)​
大盘强 → 买入奖励
大盘弱 → 买入惩罚
与 V9.2 的大盘联动逻辑保持一致:​
大盘在安全区间(-0.35% ~ 1.9%)​→ 正常
大盘弱(<-1%)​→ 买入惩罚
大盘强(>1.5%)​→ 买入奖励
目的:​让 RL 学会“顺大盘而为”。​

7. 最终奖励示例
Reward = pnl_reward
       + short_term_bonus
       + holding_penalty
       + risk_penalty
       + action_penalty
       + market_alignment_bonus
这是一个高度可控、​可调节、​完全贴合你短线风格的奖励体系。​

8. 结语
V10 奖励函数的设计目标是:​
让 AI 学会“快、​准、​狠”的短线交易风格
避免长线拖拉
避免情绪化加仓
避免逆势操作
这是 AlphaPilot Pro V10 的核心灵魂模块之一。​