# AlphaPilot Pro V9.2 - 配置项完整说明

## 📋 新增配置项 (V9.2)

### 1. RUN_MODE - 运行模式

**位置**: `config/settings.py`  
**类型**: 字符串  
**默认值**: `'live'`  
**可选值**: 
- `'live'` - 实盘/仿真模式(默认)
- `'backtest'` - 回测模式

**说明**:
```python
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')
```

**使用方式**:
```bash
# 方式1: 在.env文件中设置
GM_RUN_MODE=live

# 方式2: 环境变量
$env:GM_RUN_MODE="live"  # PowerShell
set GM_RUN_MODE=live     # CMD
```

---

### 2. SUBSCRIBE_SYMBOLS - 订阅股票列表

**位置**: `config/settings.py`  
**类型**: 列表  
**默认值**: `[]` (空列表)

**说明**:
```python
SUBSCRIBE_SYMBOLS = []
```

**工作原理**:
- 初始为空列表
- 系统会根据接收到的信号文件自动订阅相关股票
- 无需手动配置,动态管理更高效

**示例**:
```python
# 如果需要固定订阅某些股票(高级用法)
SUBSCRIBE_SYMBOLS = ['SHSE.600000', 'SZSE.000001']
```

---

## 🔧 其他核心配置项

### 掘金平台配置

```python
# 掘金 Token (从环境变量读取)
GM_TOKEN = os.getenv('GM_TOKEN', '')

# 账户ID (默认使用模拟账户)
ACCOUNT_ID = os.getenv('GM_ACCOUNT_ID', 'simulation')

# 运行模式
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')
```

### 资金策略配置 (V9.2优化)

```python
INITIAL_POSITION_RATIO = 0.33   # 初始仓位比例（33% 总资产）
BOOST_POSITION_RATIO = 0.33     # 火箭加仓比例（33% 总资产）
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金上限比例（80%）
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限（5万元）
MIN_ORDER_VALUE = 15000         # 最小下单金额
```

### 火箭加仓阈值

```python
LEVEL_1_THRESHOLD = 30000.0     # 一级火箭触发阈值（总浮盈≥3万）
LEVEL_2_THRESHOLD = 70000.0    # 二级火箭触发阈值（总浮盈≥7万）
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间（9分钟）
```

### 风控策略配置

```python
STOP_LOSS_MONITOR_THRESHOLD = 0.005     # 止损监控触发阈值（-0.5%）
STOP_LOSS_LEVEL1_THRESHOLD = 0.012      # 一级止损阈值（-1.2%减半仓）
STOP_LOSS_LEVEL2_THRESHOLD = 0.025      # 二级止损阈值（-2.5%清仓）
STOP_LOSS_CHECK_INTERVAL = 30           # 止损检查频率（每30秒）
STOP_LOSS_START_TIME = "1045"           # 硬止损开始时间（10:45后）
STOP_LOSS_END_TIME = "1450"             # 硬止损结束时间（14:50前）
ENABLE_HARD_STOP = True                 # 硬止损开关
```

---

## ⚙️ .env 文件配置示例

在项目根目录创建 `.env` 文件:

```bash
# ================= 掘金平台配置 =================
GM_TOKEN=your_token_here
GM_ACCOUNT_ID=simulation
GM_RUN_MODE=live

# ================= 测试安全模式 =================
TEST_SAFE_MODE=0
TEST_FIXED_ORDER_AMOUNT=5000.0
TEST_MIN_ORDER_VALUE=1000
TEST_SINGLE_ORDER_CASH_RATIO=0.1

# ================= 回放测试模式 =================
REPLAY_MODE=0
```

---

## 🐛 常见问题

### Q1: AttributeError: module 'config.settings' has no attribute 'RUN_MODE'

**原因**: `settings.py` 中缺少 `RUN_MODE` 配置项

**解决**: 
已在 V9.2 版本中添加,确保您的 `settings.py` 包含:
```python
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')
```

### Q2: AttributeError: module 'config.settings' has no attribute 'SUBSCRIBE_SYMBOLS'

**原因**: `settings.py` 中缺少 `SUBSCRIBE_SYMBOLS` 配置项

**解决**:
已在 V9.2 版本中添加,确保您的 `settings.py` 包含:
```python
SUBSCRIBE_SYMBOLS = []
```

### Q3: 如何切换仿真/实盘模式?

**方法1**: 修改 `.env` 文件
```bash
GM_ACCOUNT_ID=simulation  # 仿真账户
# 或
GM_ACCOUNT_ID=your_real_account_id  # 实盘账户
```

**方法2**: 修改 `settings.py`
```python
ACCOUNT_ID = os.getenv('GM_ACCOUNT_ID', 'simulation')  # 改这里
```

---

## 📝 配置优先级

配置加载优先级(从高到低):

1. **环境变量** (`os.getenv()`)
2. **.env 文件** (通过 `load_dotenv()` 加载)
3. **settings.py 默认值**

**示例**:
```python
# settings.py 中的代码
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')

# 优先级:
# 1. 如果设置了环境变量 GM_RUN_MODE,使用该值
# 2. 如果 .env 文件中有 GM_RUN_MODE,使用该值
# 3. 否则使用默认值 'live'
```

---

## ✅ 验证配置

启动系统后,查看日志确认配置是否正确加载:

```
[配置] 运行模式: live
[配置] 账户ID: 1103758f-395a-11f1-aecc-00163e022aa6
[配置] 订阅股票: 
```

如果看到这些信息,说明配置加载成功! 🎉

---

**版本**: V9.2  
**更新**: 2026-04-26  
**作者**: Alphapilot智能体团队