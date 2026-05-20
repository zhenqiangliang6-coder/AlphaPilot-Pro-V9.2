# AlphaPilot Pro V9.2 - 工业级事件驱动量化交易系统

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558  
版本: V9.2 (2026-04-26)

---

## 🎯 系统概述

AlphaPilot Pro V9.2 是一个基于掘金量化平台的**工业级智能量化交易系统**,采用事件驱动架构实现毫秒级响应和零扫描开销。专为风险厌恶型投资者和震荡市场环境优化。

### 核心特性

✅ **事件驱动架构**: Watchdog文件监听替代轮询,零延迟触发策略  
✅ **分时段量比阈值**: 4个时段差异化标准,弱势市场动态调整(×1.5)  
✅ **精细化仓位控制**: 33%初始仓位 + 火箭加仓,金字塔式建仓  
✅ **多层风控体系**: 动态分级止损(-0.5%监控/-1.2%减半/-2.5%清仓)  
✅ **异步日志系统**: 非阻塞I/O,独立线程处理日志写入  
✅ **多策略并行**: 即时策略、延时策略、火箭加仓、集合竞价  

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    AlphaPilot Pro V9.2                       │
└─────────────────────────────────────────────────────────────┘

【外部输入】
    ↓
┌──────────────┐     文件CREATE事件      ┌──────────────────┐
│  信号生成器   │ ─────────────────────→ │  SignalWatcher   │
│  (listener)  │                         │  (watchdog监听)  │
└──────────────┘                         └────────┬─────────┘
                                                  │ publish()
                                                  ↓
                                         ┌──────────────────┐
                                         │   SignalBus      │
                                         │  (消息队列总线)   │
                                         └────────┬─────────┘
                                                  │ dispatch()
                                    ┌─────────────┼─────────────┐
                                    ↓             ↓             ↓
                          ┌──────────────┐ ┌──────────┐ ┌──────────┐
                          │SignalStrategy│ │Delayed   │ │Rocket    │
                          │(即时交易)     │ │Strategy  │ │Boost     │
                          └──────────────┘ └──────────┘ └──────────┘
                                    ↓
                          ┌──────────────┐
                          │TraderEngine  │
                          │(交易执行)     │
                          └──────────────┘

【独立线程】
┌──────────────────┐     ┌──────────────────┐
│ HeartbeatMonitor │     │ AsyncLogQueue    │
│ (心跳+账户信息)   │     │ (异步日志)        │
└──────────────────┘     └──────────────────┘

【掘金回调】
┌──────────────┐
│   on_bar()   │ → 止损/止盈检查 + 时间触发策略
└──────────────┘
```

### 架构设计原则

#### 1. **决策与执行分离**
- **策略模块**: 负责交易决策(买/卖/加仓),不直接调用SDK
- **交易引擎**: 统一封装下单、查询等SDK操作
- **优势**: 切换策略或调整参数时无需重构核心代码

#### 2. **生产者-消费者模式**
- **SignalWatcher**: 生产信号事件
- **SignalBus**: 消息队列缓冲
- **策略模块**: 消费信号并执行
- **优势**: 解耦信号生成与策略执行,支持多策略并行

#### 3. **异步I/O**
- **日志队列**: 主线程put()立即返回,工作线程异步写入
- **优势**: 高频交易决策不被日志写入阻塞

---

## 📁 核心模块说明

### 1. utils/logger.py - 异步日志系统

**职责**:
- 使用 `queue.Queue` 实现生产者-消费者模式
- 工作线程从队列消费日志并写入文件
- 使用 `RotatingFileHandler` 自动轮转(每个文件10MB,保留5个备份)

**关键代码**:
```python
class AsyncLogQueue:
    def put(self, message):
        """非阻塞放入日志"""
        try:
            self.queue.put_nowait(message)
        except queue.Full:
            # 队列满时丢弃最旧的日志
            self.queue.get_nowait()
            self.queue.put_nowait(message)
    
    def _worker(self, log_dir):
        """日志工作线程"""
        while self.running:
            message = self.queue.get(timeout=1)
            logger.info(message)  # 写入文件 + 控制台
```

**优势**:
- ✅ 主线程调用 `log.log()` 立即返回(不阻塞)
- ✅ 日志写入由独立线程完成
- ✅ 自动轮转避免单文件过大

---

### 2. utils/signal_watcher.py - Watchdog文件监听器

**职责**:
- 监听 `signals/` 目录的文件CREATE事件
- 检测到新文件后立即发布到SignalBus
- 替代传统轮询扫描,实现零延迟

**关键代码**:
```python
class SignalWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('.txt'):
            return
        
        log.log(f"📩 [watchdog] 检测到新信号: {os.path.basename(event.src_path)}")
        signal_bus.publish(event.src_path)
```

**优势**:
- ✅ 零扫描开销,仅处理新文件
- ✅ 毫秒级响应,无延迟
- ✅ processed目录膨胀不影响性能

---

### 3. core/signal_bus.py - 信号总线

**职责**:
- 接收SignalWatcher发布的信号文件路径
- 解析JSON信号内容
- 根据信号类型分发到对应策略模块

**关键代码**:
```python
class SignalBus:
    def publish(self, file_path):
        """发布信号到队列"""
        self.queue.put(file_path)
    
    def dispatch(self):
        """分发信号到策略"""
        while not self.queue.empty():
            file_path = self.queue.get()
            sig = self._parse_signal(file_path)
            
            if sig['action'] == 'BUY':
                self.signal_strategy.process_single_signal(file_path)
            elif sig['action'] == 'SELL':
                self.auction_strategy.process_sell_signal(file_path)
```

---

### 4. strategies/signal_strategy.py - 即时策略(V9.2核心)

**职责**:
- 处理实时买入/卖出信号
- 分时段量比过滤(4个时段差异化阈值)
- 大盘联动风控
- 33%精细化仓位控制

**V9.2核心改进**:

#### 功能1: 分时段差异化量比阈值

| 时间段 | 量比阈值 | 弱势市场阈值 | 设计理念 |
|--------|---------|------------|---------|
| **09:30-10:30** | ≥ 1.2 | ≥ 1.8 | 早盘宽松,快速捕捉机会 |
| **10:30-11:30** | ≥ 2.2 | ≥ 3.3 | 上午严格,过滤假突破 |
| **13:00-14:00** | ≥ 3.0 | ≥ 4.5 | 下午更严格,确认趋势 |
| **14:00-15:00** | ≥ 3.8 | ≥ 5.7 | 尾盘最严格,避免追高 |

**弱势市场定义**: 上证指数涨跌幅在 -1.0% 至 -0.35% 之间  
**弱势市场调整**: 所有时段量比阈值 × 1.5

**核心代码**:
```python
def _decide_action(self, action, vr):
    # 【V9.2 新增】分时段判断
    if "0930" <= time_str < "1030":
        period = "早盘(09:30-10:30)"
        time_slot = "morning_early"
    elif "1030" <= time_str <= "1130":
        period = "上午(10:30-11:30)"
        time_slot = "morning_late"
    elif "1300" <= time_str < "1400":
        period = "下午(13:00-14:00)"
        time_slot = "afternoon_early"
    elif "1400" <= time_str <= "1500":
        period = "尾盘(14:00-15:00)"
        time_slot = "afternoon_late"
    
    # 【V9.2 新增】分时段量比阈值
    vr_thresholds = {
        "morning_early": 1.2,    # 09:30-10:30
        "morning_late": 2.2,     # 10:30-11:30
        "afternoon_early": 3.0,  # 13:00-14:00
        "afternoon_late": 3.8,   # 14:00-15:00
    }
    
    threshold = vr_thresholds.get(time_slot, 999)
    
    # 弱势市场阈值提高50%
    if -1.0 <= index_change < -0.35:
        threshold *= 1.5
```

#### 功能2: 33%精细化仓位控制

| 阶段 | 仓位比例 | 触发条件 | 累计仓位 |
|------|---------|---------|---------|
| **首次买入** | 33% | 信号触发 | 33% |
| **一级火箭** | +33% | 总浮盈≥3万 | 66% |
| **二级火箭** | +33% | 总浮盈≥7万 | 99% |

**核心代码**:
```python
def _check_position_and_calculate_volume(self, code, action, price):
    # 【V9.2 新增】仓位控制：首次买入使用总资产的33%
    INITIAL_POSITION_RATIO = 0.33  # 33% 初始仓位
    
    # 计算目标买入金额（基于总资产而非可用现金）
    target_order_value = total_asset * INITIAL_POSITION_RATIO
    
    # 限制单笔最大金额
    MAX_SINGLE_ORDER_VALUE = 50000
    order_value = min(target_order_value, MAX_SINGLE_ORDER_VALUE)
    
    # 确保不超过可用现金的80%（保留安全边际）
    order_value = min(order_value, available_cash * 0.8)
```

---

### 5. strategies/rocket_boost.py - 火箭加仓策略

**职责**:
- 监控总浮盈,达到阈值后自动加仓
- 每次加仓使用总资产的33%
- 选择浮盈最高的股票优先加仓

**V9.2改进**:
```python
def _execute_boost(self, stage, profit_details):
    # 【V9.2 新增】每次加仓使用总资产的33%
    BOOST_POSITION_RATIO = 0.33  # 33% 加仓仓位
    target_boost_value = total_asset * BOOST_POSITION_RATIO
    
    # 根据目标金额计算加仓数量
    boost_volume = int(order_value / current_price / 100) * 100
```

---

### 6. risk/stop_loss.py - 动态分级止损

**职责**:
- 监控持仓盈亏比例
- 三级止损机制: 监控(-0.5%) → 一级减半(-1.2%) → 二级清仓(-2.5%)
- 反弹保护和时间窗口限制

**配置参数**:
```python
STOP_LOSS_MONITOR_THRESHOLD = 0.005     # 止损监控触发阈值（-0.5%开始监控）
STOP_LOSS_LEVEL1_THRESHOLD = 0.012      # 一级止损阈值（-1.2%减半仓）
STOP_LOSS_LEVEL2_THRESHOLD = 0.025      # 二级止损阈值（-2.5%清仓）
STOP_LOSS_START_TIME = "1045"           # 硬止损开始执行时间（10:45后）
STOP_LOSS_END_TIME = "1450"             # 硬止损结束执行时间（14:50前）
```

**止损流程**:
```
亏损 0% ──→ -0.5% ──→ -1.2% ──→ -2.5%
         [监控]     [减半]     [清仓]
```

---

## 📊 工作流程

### 完整信号处理流程

```
graph LR
    A[信号生成<br/>listener.py] -->|创建.txt文件| B[Watchdog监听<br/>signal_watcher.py]
    B -->|CREATE事件| C[SignalBus发布<br/>signal_bus.py]
    C -->|分发信号| D{策略选择}
    D -->|BUY信号| E[SignalStrategy<br/>即时策略]
    D -->|SELL信号| F[AuctionStrategy<br/>集合竞价]
    E -->|量比过滤| G[_decide_action<br/>分时段阈值]
    G -->|通过| H[_check_position<br/>33%仓位计算]
    H -->|成功| I[TraderEngine<br/>执行下单]
    
    J[HeartbeatMonitor<br/>心跳线程] -->|每30秒| K[risk/stop_loss.py<br/>止损检查]
    K -->|触发| I
```

### 分时段量比判断流程

```
收到BUY信号
    ↓
获取当前时间
    ↓
判断时段:
  - 09:30-10:30 → 阈值1.2
  - 10:30-11:30 → 阈值2.2
  - 13:00-14:00 → 阈值3.0
  - 14:00-15:00 → 阈值3.8
    ↓
获取大盘涨跌幅
    ↓
if -1.0% ≤ 大盘 < -0.35%:
    阈值 × 1.5  # 弱势市场
    ↓
比较: 量比 ≥ 阈值?
    ↓
是 → 通过,继续仓位计算
否 → 拦截,记录日志
```

---

## ⚙️ 配置说明

### 核心配置项 (config/settings.py)

```python
# ================= 掘金平台配置 =================
GM_TOKEN = os.getenv('GM_TOKEN', '')              # 掘金Token
ACCOUNT_ID = os.getenv('GM_ACCOUNT_ID', 'simulation')  # 账户ID
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')       # 运行模式(live/backtest)

# ================= 资金策略配置 (V9.2优化) =================
INITIAL_POSITION_RATIO = 0.33   # 初始仓位比例（33% 总资产）
BOOST_POSITION_RATIO = 0.33     # 火箭加仓比例（33% 总资产）
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金上限比例（80%）
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限（5万元）
MIN_ORDER_VALUE = 15000         # 最小下单金额

# ================= 火箭加仓阈值 =================
LEVEL_1_THRESHOLD = 30000.0     # 一级火箭触发阈值（总浮盈≥3万）
LEVEL_2_THRESHOLD = 70000.0    # 二级火箭触发阈值（总浮盈≥7万）
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间（9分钟）

# ================= 风控策略配置 =================
STOP_LOSS_MONITOR_THRESHOLD = 0.005     # 止损监控触发阈值（-0.5%）
STOP_LOSS_LEVEL1_THRESHOLD = 0.012      # 一级止损阈值（-1.2%减半仓）
STOP_LOSS_LEVEL2_THRESHOLD = 0.025      # 二级止损阈值（-2.5%清仓）
STOP_LOSS_CHECK_INTERVAL = 30           # 止损检查频率（每30秒）
STOP_LOSS_START_TIME = "1045"           # 硬止损开始时间（10:45后）
STOP_LOSS_END_TIME = "1450"             # 硬止损结束时间（14:50前）
ENABLE_HARD_STOP = True                 # 硬止损开关

# ================= 动态止盈策略配置 (V9.2新增) =================
TAKE_PROFIT_EARLIEST_TIME = "0951"      # 最早执行时间（09:51，避开开盘波动）
TAKE_PROFIT_LEVEL1_GAIN = 0.03          # 第一级涨幅阈值（3%）
TAKE_PROFIT_LEVEL1_DROP = 0.013         # 第一级回落阈值（1.3%）
TAKE_PROFIT_LEVEL1_MAX = 0.085          # 第一级涨幅上限（8.5%）
TAKE_PROFIT_LEVEL2_GAIN = 0.09          # 第二级涨幅阈值（9%，60/00开头）
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 12    # 第二级持有时间（12分钟）
TAKE_PROFIT_LEVEL3_GAIN = 0.18          # 第三级涨幅阈值（18%，68/30开头）
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 12    # 第三级持有时间（12分钟）
```

### .env 文件配置示例

```
# ================= 掘金平台配置 =================
GM_TOKEN=your_token_here
GM_ACCOUNT_ID=simulation
GM_RUN_MODE=live

# ================= 测试安全模式 =================
TEST_SAFE_MODE=0
TEST_FIXED_ORDER_AMOUNT=5000.0
TEST_MIN_ORDER_VALUE=1000
TEST_SINGLE_ORDER_CASH_RATIO=0.1
```

---

## 🚀 启动方式

### 推荐: 一键启动脚本

```bash
start_with_sync.bat
```

会自动:
1. ✅ 激活虚拟环境
2. ✅ 清理Python缓存
3. ✅ 启动信号同步器(独立窗口)
4. ✅ 等待3秒初始化
5. ✅ 启动主策略引擎(独立窗口)

### 手动启动

```bash
# 终端1: 信号同步器
python signal_sync_standalone.py

# 终端2: 主策略引擎
python main.py
```

---

## 📈 预期效果

### 分时段量比阈值效果

| 场景 | V9.1 | V9.2 | 改进 |
|------|------|------|------|
| **早盘09:45,量比1.5** | ❌ 拦截(1.5<2.0) | ✅ 通过(1.5≥1.2) | 捕获更多机会 |
| **上午11:00,量比1.9** | ❌ 拦截(1.9<2.0) | ❌ 拦截(1.9<2.2) | 更严格过滤 |
| **下午13:30,量比3.5** | ✅ 通过(3.5≥3.6? No) | ✅ 通过(3.5≥3.0) | 合理放宽 |
| **尾盘14:30,量比4.2** | ✅ 通过(4.2≥3.6) | ✅ 通过(4.2≥3.8) | 保持严格 |

### 仓位控制效果

假设总资产100万元:

| 阶段 | V9.1 | V9.2 | 优势 |
|------|------|------|------|
| **首次买入** | 80%可用现金≈80万 | 33%总资产=33万 | 降低风险 |
| **一级火箭** | 固定加仓 | +33%总资产(需盈利≥3万) | 盈利验证 |
| **二级火箭** | 固定加仓 | +33%总资产(需盈利≥7万) | 可控扩展 |
| **最大仓位** | 不确定 | 最多99%(3次×33%) | 可预测 |

---

## ⚠️ 注意事项

### 1. Strategy ID 强同步
代码中的 `strategy_id` 必须与掘金终端中创建的策略实例ID**完全一致**,否则报错 `无效的ACCOUNT_ID`。

### 2. 运行依赖
必须启动掘金终端并登录账户,策略才能连接行情和交易服务。

### 3. 时间窗口限制
止损策略仅在 **10:45 - 14:50** 之间执行,避开开盘尾盘噪音。

### 4. 测试建议
- ✅ 先在掘金仿真账户运行至少2周
- ✅ 统计各时段的胜率和盈亏比
- ✅ 确认参数适合您的风险偏好
- ❌ 禁止直接在实盘账户使用新参数

### 5. 异步日志说明
异步日志可能导致日志显示时间滞后于实际交易时间(**正常现象,非卡顿**)。

---

## 📚 相关文档

- **QUICKSTART.md** - 快速入门指南(中英双语)
- **CHANGELOG_V9.2_STRATEGY_OPTIMIZATION.md** - V9.2策略优化详细说明
- **V9.2_QUICK_REFERENCE.md** - V9.2快速参考指南
- **CONFIG_GUIDE_V9.2.md** - 配置项完整说明
- **SIGNAL_SYNC_DELIVERY_SUMMARY.md** - 跨目录信号同步功能说明

---

## 💡 量化专家建议

### 关于分时段量比阈值

> "不同时段的市场微观结构不同。早盘流动性较低但波动大,适合降低量比要求;尾盘流动性高但容易追高,需要更严格的过滤。这种设计符合A股市场的实际特征。"

### 关于仓位控制

> "33%初始仓位是经典的'三分之一法则',既保证有足够exposure获取收益,又保留充足现金应对波动。金字塔式加仓确保只有在盈利时才扩大风险暴露,这是专业基金管理的常用策略。"

### 关于弱势市场动态调整

> "弱势市场×1.5的设计体现了风险自适应理念。不是简单的'弱势就减半仓',而是智能调整入场标准,减少低质量交易,保留优质机会。这是从散户思维到机构思维的跨越。"

---

**版本**: V9.2  
**更新日期**: 2026-04-26  
**作者**: Alphapilot智能体团队  
**联系方式**: 497720537@qq.com | 13392077558