# AlphaPilot Pro V9.2 - 工业级事件驱动量化交易系统

![Version](https://img.shields.io/badge/version-9.2-blue)
![Platform](https://img.shields.io/badge/platform-掘金量化/QMT-green)
![Python](https://img.shields.io/badge/python-3.6+-yellow)
![Architecture](https://img.shields.io/badge/architecture-事件驱动-orange)

---

## 🧠⚡ 核心架构原则：大脑-手脚分离模式

### **Alphapilot智能体 = 大脑（决策中枢）**
- **职责**：生成交易信号、计算量比指标、决定买卖时机
- **输出**：JSON/TXT信号文件（包含股票代码、量比、动作等）
- **不可变性**：核心决策逻辑不因平台差异而改变

### **交易平台 = 手脚（执行终端）**
- **支持平台**：掘金量化、QMT、其它量化平台
- **职责**：接收信号、查询持仓/资产、执行下单操作
- **适配要求**：**运行策略前必须先测试平台接口字段**

---

## ⚠️ 重要提示：接口测试与VSCode独立运行必读

### 🔴 **1. 平台接口字段测试（必须执行）**

**在运行任何策略之前，必须完成以下步骤：**

#### **为什么需要测试？**
- 不同平台的SDK返回字段可能不同（如掘金v3.0.183 vs QMT）
- 持仓字段映射错误会导致T+1违规或订单失败
- 成本价字段优先级影响止损止盈准确性

#### **测试清单**
- [ ] **持仓字段测试**：运行 `python test_position_fields.py`
  - 验证 `available_now` 字段存在且数值正确
  - 确认 `can_use_volume` 映射到正确的可卖数量
  - 检查成本价字段（`vwap_open` > `vwap` > `cost/volume`）
  
- [ ] **资产字段测试**：确认可用资金、总资产字段正确
- [ ] **下单接口测试**：验证市价单/限价单参数格式
- [ ] **行情接口测试**：确认实时价格获取方式

#### **测试结果验证**
```
# 运行持仓字段测试
cd d:\main_data
python test_position_fields.py

# 预期输出应显示：
# ✅ available_now: 200 股（当前可卖）
# ❌ available: 1800 股（包含今日买入，不可用于卖出）
# ✅ vwap_open: 57.29 元（优先使用的成本价）
```

**详细文档**：
- [GM_POSITION_FIELDS_MAPPING_V9.2.md](GM_POSITION_FIELDS_MAPPING_V9.2.md) - 掘金SDK字段完整映射
- [A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md](A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md) - A股交易规则合规性审计

---

### 🔴 **2. VSCode 独立运行 Strategy ID 强同步要求**

**如果你要在 VSCode 中独立运行策略，必须严格遵守以下规范：**

- 代码中的 `strategy_id` 必须与掘金终端（IDE）中创建的策略实例 ID **完全一致**
- 若 ID 不匹配，会导致 `{"status": 1020, "message": "无效的ACCOUNT_ID"}` 错误
- **详细操作流程请查看**: [VSCODE_INDEPENDENT_RUN_MANDATORY.md](VSCODE_INDEPENDENT_RUN_MANDATORY.md)

**快速检查清单**：
- [ ] 掘金终端已启动并登录账户
- [ ] 在掘金终端中创建了策略实例
- [ ] 代码中的 `strategy_id` 与掘金终端中的策略实例 ID 完全一致
- [ ] 掘金终端中的策略实例状态为"已连接"
- [ ] `filename` 参数使用相对路径（如 `'main.py'`）

---

## 📖 项目简介

**AlphaPilot Pro** 是一个基于**掘金量化平台**的工业级智能量化交易策略系统。V9.2 版本采用**事件驱动架构**，实现了信号处理的零扫描开销与毫秒级响应，专为风险厌恶型投资者和震荡市场环境优化。

### ✨ 核心特性 (V9.2)

#### 🚀 工业级事件驱动架构
- **Watchdog 实时监听**: 文件 CREATE 事件触发，零轮询延迟
- **异步日志队列**: 独立线程处理 I/O，高频决策不阻塞
- **信号总线模式**: 生产者-消费者解耦，支持多策略并行
- **心跳线程瘦身**: 仅负责健康检查，性能恒定无衰退

#### 📊 双模策略体系
- **即时策略 (Signal Strategy)**: 
  - 大盘联动风控：以上证指数开盘价为基准动态调整阈值
  - 时段差异化控制：下午自动提高量比要求（≥ 3.6），防止尾盘诱多
  - 卖出优先原则：独立执行通道，不受买入限制影响
- **延时策略 (Delayed Strategy)**: 
  - T+N 日智能观察：三阶段时间窗口控制（目标日前/当天/之后）
  - 量比触发机制：盘中达标立即买入或 14:39 保底买入
  - 自动过期清理：目标日后自动从观察名单删除

#### 🛡️ 多层风控体系
- **动态分级止损 (V9.2)**: 
  - 监控触发：亏损 -0.5% 进入观察
  - 一级止损：亏损 -1.2% 减半仓
  - 二级止损：亏损 -2.5% 清仓
  - 反弹保护：股价超过成本价后重置止损状态
  - 时间窗口：10:45 - 14:50 执行，避开开盘和尾盘噪音
- **动态止盈策略**: 三级动态止盈逻辑，最早 09:52 执行
- **持仓有效性检查**: 卖出前确认可卖数量，避免无效下单

#### 💰 智能仓位管理
- **无限加仓策略 (Rocket Boost)**: 
  - Level 1: 资金 ≥ 30,000 元触发一级加仓
  - Level 2: 资金 ≥ 70,000 元触发二级加仓
  - 重复保护：9 分钟内禁止重复下单
- **集合竞价策略 (Auction)**: 
  - 精英名单筛选：浮盈 > 13% 的股票
  - 竞价卖出：以现价 95% 报价快速离场
- **资金分配**: 单次买入最多使用 80% 可用现金，上限 50,000 元

---

## 👥 团队信息

**Alphapilot智能体团队**
- **振强** - 导师 Alphapilot OS核心架构师
- **梁子羿** - 广东外语外贸大学数字运营系人工智能
- **侯沣睿** - 惠州城市职业学院大数据筛选
- **梁茹真** - 北京工商大学

📧 邮箱: 497720537@qq.com  
📱 电话: 13392077558

---

## 🛠️ 快速配置与热更新指南

如果你想修改策略参数，请参考下表。大部分参数修改后**无需重启程序**即可生效。

| 我想修改... | 请打开这个文件 | 找到这个关键词/位置 | 建议操作 |
| :--- | :--- | :--- | :--- |
| **买入/卖出的量比阈值** | `strategies/signal_strategy.py` | `_decide_action` 方法 (约 L210) | 修改 `threshold = 3.6` 等数值 |
| **大盘涨跌幅安全区间** | `strategies/signal_strategy.py` | `_decide_action` 方法 (约 L215) | 修改 `-0.35` 或 `1.9` 等区间值 |
| **交易时间窗口** | `strategies/signal_strategy.py` | `_decide_action` 方法 (约 L205) | 修改 `"1300" <= time_str <= "1500"` |
| **单笔最大买入金额** | `config/settings.py` | `FIXED_ORDER_AMOUNT` | 修改 `50000` 为你想要的金额 |
| **止损触发比例** | `config/settings.py` | `STOP_LOSS_LEVEL1_THRESHOLD` | 修改 `0.012` (即 1.2%) |
| **延时股票名单** | `data/stock_personalities.json` | 股票代码 (如 `"600821.SH"`) | 修改 `"type": "delayed"` |
| **精英卖出名单** | `signals/yesterday_holdings.json` | `positions` 字典 | 添加/删除待卖出股票 |
| **账户 ID / Token** | `.env` (根目录) | `GM_ACCOUNT_ID` / `GM_TOKEN` | 填入你的掘金实盘/模拟账户信息 |
| **火箭加仓阈值** | `config/settings.py` | `LEVEL_1_THRESHOLD` / `LEVEL_2_THRESHOLD` | 修改资金触发金额 |
| **集合竞价卖出系数** | `config/settings.py` | `AUCTION_SELL_RATIO` | 修改 `0.95` (现价 95%) |

> **💡 专家提示**: 修改 Python 代码后，如果运行结果没变，请记得清理缓存：
> ```powershell
> Get-ChildItem -Path . -Include __pycache__ -Recurse | Remove-Item -Recurse -Force
> ```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install gm python-dotenv watchdog

# 或者使用虚拟环境
python -m venv quant_env
quant_env\Scripts\activate
pip install gm python-dotenv watchdog
```

### 2. 配置环境变量 (`.env`)

在项目根目录创建 `.env` 文件：

```env
# 掘金量化平台配置
GM_TOKEN=your_token_here
GM_ACCOUNT_ID=your_account_id_here
GM_RUN_MODE=live

# 测试安全模式（可选，防止误下大单）
TEST_SAFE_MODE=1
TEST_FIXED_ORDER_AMOUNT=5000.0
TEST_MIN_ORDER_VALUE=1000
TEST_SINGLE_ORDER_CASH_RATIO=0.1
```

### 3. **⚠️ 接口字段测试（必须执行）**

```bash
# 测试持仓字段映射
python test_position_fields.py

# 验证输出是否正确
# - available_now 应该显示当前可卖数量
# - can_use_volume 应该等于 available_now
# - vwap_open 应该是优先使用的成本价
```

### 4. 运行策略

```bash
# 方式1: 直接运行
python main.py

# 方式2: 使用 PowerShell 脚本（推荐，自动清理缓存）
.\start_v9_1.ps1

# 方式3: VSCode 独立运行（需先配置 strategy_id）
python run_strategy_in_vscode.py
```

---

## 📂 项目结构

```
mpython/
├── main.py                          # 🎯 主程序入口（事件驱动架构）
├── listener.py                      # 信号监听器（生成信号文件）
│
├── config/                          # ⚙️ 配置中心
│   ├── settings.py                  # 核心配置文件（止损、资金、策略参数）
│   └── __init__.py
│
├── core/                            # 🔧 核心引擎
│   ├── trader_engine.py             # 交易执行引擎（下单/查询持仓/资产）
│   ├── state_manager.py             # 状态管理器（精英名单/持仓状态）
│   ├── signal_bus.py                # 信号总线（消息队列分发）
│   └── __init__.py
│
├── strategies/                      # 📈 策略模块
│   ├── signal_strategy.py           # ⭐ 即时策略（大盘联动+量比过滤）
│   ├── delayed_strategy.py          # ⭐ 延时策略（T+N观察+保底买入）
│   ├── rocket_boost.py              # 火箭加仓策略（分级加仓）
│   ├── auction_strategy.py          # 集合竞价策略（精英卖出）
│   └── __init__.py
│
├── risk/                            # 🛡️ 风控模块
│   ├── stop_loss.py                 # 动态分级止损（监控→减半→清仓）
│   ├── dynamic_take_profit.py       # 动态止盈策略（三级止盈）
│   └── __init__.py
│
├── utils/                           # 🛠️ 工具模块
│   ├── logger.py                    # 异步日志系统（非阻塞 I/O）
│   ├── signal_watcher.py            # Watchdog 文件监听器
│   ├── heartbeat.py                 # 心跳监控器
│   ├── helpers.py                   # 辅助函数（时间判断/代码转换）
│   └── __init__.py
│
├── signals/                         # 📨 信号输入区
│   ├── processed/                   # 已处理信号归档
│   └── yesterday_holdings.json      # 昨日持仓/精英卖出名单
│
├── data/                            # 📊 数据文件
│   ├── stock_personalities.json     # 个股个性化配置（延时策略名单）
│   ├── delayed_watchlist.json       # 延时观察名单（运行时维护）
│   └── qmt_delay_config.json        # QMT 延时配置（兼容旧版）
│
├── logs/                            # 📝 日志输出目录
│
├── docs/                            # 📚 详细文档
│   └── SIGNAL_STRATEGY_MARKET_LINKAGE.md  # V9.2 交易规范详解
│
├── ARCHITECTURE_V9.1.md             # 架构设计文档
├── CHANGELOG_V9.2.md                # 版本更新日志（V9.2）
├── QUICK_START_V9.1.md              # 快速入门指南
├── VSCODE_INDEPENDENT_RUN_MANDATORY.md  # VSCode 运行强制规范
├── GM_POSITION_FIELDS_MAPPING_V9.2.md     # 掘金SDK字段映射表
├── A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md  # A股合规性审计
├── POSITION_FIELDS_AUDIT_REPORT_V9.2.md        # 持仓字段审核报告
├── QUICK_REFERENCE_A_SHARE_COMPLIANCE.md       # A股规则快速参考
│
└── requirements.txt                 # Python 依赖列表
```

---

## 📊 策略逻辑流程图 (V9.2)

```
【信号输入】
    ↓
[listener.py 生成 JSON 信号文件]
    ↓
[Watchdog 捕获 CREATE 事件] → [SignalWatcher 解析信号]
    ↓
[SignalBus 消息总线分发]
    ├─→ Immediate 信号 → SignalStrategy._decide_action
    │                     ├─ 获取上证指数涨跌幅
    │                     ├─ 判断当前时段 (上午/下午)
    │                     ├─ 校验大盘区间 (-0.35% ~ 1.9%)
    │                     ├─ 校验量比阈值 (2.0/3.6/5.0)
    │                     └─ 执行下单
    │
    ├─→ Delayed 信号 → DelayedStrategy.check_and_execute
    │                   ├─ 目标日之前: 禁止买入
    │                   ├─ 目标日当天: 量比达标或14:39保底买入
    │                   └─ 目标日之后: 自动过期删除
    │
    └─→ Rocket 信号 → RocketBoost.execute
                      ├─ 检查资金是否达到 Level 1/2 阈值
                      ├─ 计算加仓金额
                      └─ 执行买入

【风控监控】(独立心跳线程，每 30 秒检查)
    ├─→ StopLossMonitor: 亏损 -0.5% 监控 → -1.2% 减半 → -2.5% 清仓
    └─→ DynamicTakeProfit: 盈利达标后动态止盈

【持仓管理】
    └─→ TraderEngine: 查询资产/持仓 → 计算可买数量 → 执行下单
```

---

## ⚙️ 核心参数说明

### 1. 大盘联动阈值 (`strategies/signal_strategy.py`)

| 大盘区间 (涨跌幅) | 上午买入量比 | 下午买入量比 | 卖出量比要求 |
| :--- | :--- | :--- | :--- |
| **-0.35% ~ +1.9%** (正常) | ≥ 2.0 | ≥ 3.6 | ≥ 1.5 |
| **-1.0% ~ -0.35%** (弱势) | ≥ 3.6 | ≥ 5.0 | ≥ 0.8 |
| **其他区间** | ❌ 禁止买入 | ❌ 禁止买入 | - |

### 2. 止损参数 (`config/settings.py`)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `STOP_LOSS_MONITOR_THRESHOLD` | 0.005 | 监控起点 (-0.5%) |
| `STOP_LOSS_LEVEL1_THRESHOLD` | 0.012 | 一级止损 (-1.2%，减半仓) |
| `STOP_LOSS_LEVEL2_THRESHOLD` | 0.025 | 二级止损 (-2.5%，清仓) |
| `STOP_LOSS_CHECK_INTERVAL` | 30 | 检查频率（每 30 秒） |
| `STOP_LOSS_START_TIME` | "1045" | 开始执行时间（10:45） |
| `STOP_LOSS_END_TIME` | "1450" | 结束执行时间（14:50） |

### 3. 资金管理参数 (`config/settings.py`)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FIXED_ORDER_AMOUNT` | 50000.0 | 单次买入金额上限（5 万元） |
| `SINGLE_ORDER_CASH_RATIO` | 0.8 | 每次买入可用现金比例（80%） |
| `MIN_ORDER_VALUE` | 15000 | 最小下单金额（1.5 万元） |
| `LEVEL_1_THRESHOLD` | 30000.0 | 火箭加仓一级阈值 |
| `LEVEL_2_THRESHOLD` | 70000.0 | 火箭加仓二级阈值 |
| `REPEAT_PROTECT_SECONDS` | 540 | 重复下单保护时间（9 分钟） |

### 4. 集合竞价参数 (`config/settings.py`)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ELITE_PROFIT_THRESHOLD` | 0.13 | 精英筛选阈值（浮盈 >13%） |
| `AUCTION_SELL_RATIO` | 0.95 | 竞价卖出报价系数（现价 95%） |

---

## 🐛 常见问题

### Q1: 为什么日志显示的时间比现在慢几分钟？
**A**: 这是**异步日志**的特性。策略在 `13:17` 已经执行完下单，但日志线程在 `13:26` 才把消息打印到屏幕。这证明系统没有卡顿，只是在排队输出日志，确保交易决策不被 I/O 阻塞。

### Q2: 周末或非交易时间能测试吗？
**A**: 可以！运行沙盒测试脚本验证逻辑：
```bash
python test_signal_logic_sandbox.py
```
它会模拟大盘数据，帮你验证逻辑是否正确，而不需要真实的行情推送。

### Q3: 报错 `无效的ACCOUNT_ID`？
**A**: 检查以下几点：
1. `.env` 文件中的 `GM_ACCOUNT_ID` 是否正确
2. 该账户在掘金终端中处于登录状态
3. 代码中的 `strategy_id` 与掘金终端中的策略实例 ID 完全一致
4. 详见 [VSCODE_INDEPENDENT_RUN_MANDATORY.md](VSCODE_INDEPENDENT_RUN_MANDATORY.md)

### Q4: 如何添加新的延时观察股票？
**A**: 编辑 `data/stock_personalities.json`，添加如下格式：
```json
{
  "600821.SH": {
    "type": "delayed",
    "target_date": "2024-01-15",
    "trigger_volume_ratio": 3.6
  }
}
```

### Q5: 如何查看昨天的持仓作为今天卖出的精英名单？
**A**: 编辑 `signals/yesterday_holdings.json`，格式如下：
```json
{
  "positions": {
    "SHSE.600821": {
      "volume": 1000,
      "cost_price": 25.5,
      "profit_ratio": 0.15
    }
  }
}
```

### Q6: 止损为什么没有在预期位置触发？
**A**: 检查以下几点：
1. 当前时间是否在 10:45 - 14:50 之间（止损时间窗口）
2. 亏损是否达到监控阈值（-0.5%）
3. 查看日志中是否有 `[止损监控]` 相关输出
4. 确认 `ENABLE_HARD_STOP` 参数为 `True`

### Q7: 切换到QMT平台需要注意什么？
**A**: 
1. **必须先测试QMT接口字段**：运行 `test_position_fields.py` 验证QMT返回的持仓字段
2. **修改trader_engine.py**：替换掘金API为QMT API调用
3. **保持大脑逻辑不变**：量比计算、信号分流、止损阈值等由Alphapilot决定
4. **验证T+1合规**：确认QMT的可卖数量字段名称（可能是 `available` 或 `can_sell`）

### Q8: 为什么卖出订单被交易所拒绝？
**A**: 检查卖出数量是否为100股的整数倍：
- ✅ 正确：100股、200股、1000股
- ❌ 错误：250股、950股、150股
- 查看日志确认实际卖出数量，应该显示"实际卖出:XXX股"

---

## 📚 详细文档索引

### 核心架构文档
- **[ARCHITECTURE_V9.2.md](ARCHITECTURE_V9.2.md)** - V9.2完整架构设计与技术细节(⭐推荐)
- **[UPGRADE_SUMMARY_V9.2.md](UPGRADE_SUMMARY_V9.2.md)** - V9.2升级总结与V9.1内容整合说明

### V9.2策略优化文档
- **[CHANGELOG_V9.2_STRATEGY_OPTIMIZATION.md](CHANGELOG_V9.2_STRATEGY_OPTIMIZATION.md)** - V9.2策略优化详细说明(分时段量比+33%仓位)
- **[V9.2_QUICK_REFERENCE.md](V9.2_QUICK_REFERENCE.md)** - V9.2快速参考指南
- **[CONFIG_GUIDE_V9.2.md](CONFIG_GUIDE_V9.2.md)** - V9.2配置项完整说明

### 快速入门
- **[QUICKSTART.md](QUICKSTART.md)** - 快速入门指南(中英双语,⭐首选)
- **[一键启动指南.md](一键启动指南.md)** - 一键启动脚本使用说明

### 接口测试与合规性文档
- **[GM_POSITION_FIELDS_MAPPING_V9.2.md](GM_POSITION_FIELDS_MAPPING_V9.2.md)** - 掘金SDK v3.0.183字段完整映射表
- **[POSITION_FIELDS_AUDIT_REPORT_V9.2.md](POSITION_FIELDS_AUDIT_REPORT_V9.2.md)** - 持仓字段审核与修复报告
- **[A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md](A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md)** - A股交易规则合规性审计
- **[QUICK_REFERENCE_A_SHARE_COMPLIANCE.md](QUICK_REFERENCE_A_SHARE_COMPLIANCE.md)** - A股规则快速参考卡
- **[QUICK_REFERENCE_POSITION_FIELDS.md](QUICK_REFERENCE_POSITION_FIELDS.md)** - 持仓字段快速参考卡

### 信号同步功能
- **[SIGNAL_SYNC_DELIVERY_SUMMARY.md](SIGNAL_SYNC_DELIVERY_SUMMARY.md)** - 跨目录信号同步功能交付总结
- **[SIGNAL_SYNC_GUIDE.md](SIGNAL_SYNC_GUIDE.md)** - 信号同步器使用指南

### 工作流指南
- **[GM_IDE_WORKFLOW_GUIDE.md](GM_IDE_WORKFLOW_GUIDE.md)** - 掘金 IDE 工作流指南
- **[docs/SIGNAL_STRATEGY_MARKET_LINKAGE.md](docs/SIGNAL_STRATEGY_MARKET_LINKAGE.md)** - V9.2 大盘联动交易规范详解

---

## 🔒 安全提示

1. **严禁在生产环境使用测试账户进行大额交易**
2. **启用 `TEST_SAFE_MODE=1` 进行联调，防止误下大单**
3. **定期检查 `logs/` 目录下的日志文件，监控系统运行状态**
4. **修改关键参数前，务必备份配置文件**
5. **止损策略仅在交易时间窗口内生效，非窗口期不会执行**
6. **⚠️ 切换平台前必须先测试接口字段，确保T+1合规和100股取整**

---

## 📞 技术支持

如遇问题，请联系 Alphapilot 智能体团队：

- 📧 邮箱: 497720537@qq.com
- 📱 电话: 13392077558
- 📖 文档: 查看项目根目录下的 `.md` 文档

---

**祝交易顺利！🚀 AlphaPilot Pro V9.2 与你同行。**

*最后更新: 2026-04-26 | 版本: V9.2 (分时段量比阈值 + 33%精细化仓位控制)*
