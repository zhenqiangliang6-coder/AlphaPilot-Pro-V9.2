# AlphaPilot Pro V9.2 - 核心架构原则与执行规范

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558  
版本: V9.2  
更新日期: 2026-04-24

---

## 🎯 核心原则：大脑-手脚架构

### ⚠️ **最高优先级声明**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   🧠 AlphaPilot 智能体 = 大脑（决策中枢）                    │
│   👐 掘金/QMT/其他平台 = 手脚（执行终端）                     │
│                                                             │
│   【铁律】大脑发出指令 → 手脚必须严格执行                      │
│   【禁令】严禁因平台接口限制而修改大脑的核心逻辑               │
│                                                             │
│   ⚠️ 重要：各平台接口在运行策略之前必须先测试接口字段          │
│      确保T+1合规、100股取整、成本价映射正确                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 架构分层说明

### 第零层：接口测试层（必须执行）

**职责：**
- ✅ 测试平台SDK返回的持仓字段（`available_now`, `vwap_open`等）
- ✅ 验证T+1合规模块（可卖数量是否正确）
- ✅ 确认100股取整逻辑（卖出数量是否为100的倍数）
- ✅ 检查成本价字段优先级（`vwap_open` > `vwap` > `cost/volume`）

**测试工具：**
```bash
# 掘金量化平台测试
python test_position_fields.py

# QMT平台测试（需适配）
python test_qmt_position_fields.py
```

**测试结果验证：**
- ✅ `available_now` 应该显示当前可卖数量（不含今日买入）
- ❌ `available` 包含今日买入，不能用于卖出决策
- ✅ 所有卖出操作必须是100股的整数倍
- ✅ 成本价优先使用 `vwap_open`

**详细文档：**
- [GM_POSITION_FIELDS_MAPPING_V9.2.md](GM_POSITION_FIELDS_MAPPING_V9.2.md) - 掘金SDK字段完整映射
- [A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md](A_SHARE_TRADING_RULES_COMPLIANCE_AUDIT_V9.2.md) - A股交易规则合规性审计

---

### 第一层：决策层（大脑 - AlphaPilot）

**职责：**
- ✅ 生成交易信号（BUY/SELL）
- ✅ 计算量比指标（volume_ratio）
- ✅ 判断股票类型（immediate/delayed）
- ✅ 设定触发阈值（min_volume_ratio, delay_days等）

**输出格式：**
```json
{
  "ts": "2026-04-15 14:32:59",
  "code": "603353.SH",           // AlphaPilot标准格式
  "name": "和顺电气",
  "action": "BUY",                // 核心决策
  "price": 38.63,                 // 触发价格
  "volume_ratio": 22.50,          // 🔑 核心指标：量比
  "source": "AlphaPilot_Email"
}
```

**存储位置：**
```
D:\main_data\signals\*.txt
```

---

### 第二层：适配层（神经中枢 - 本系统）

**职责：**
- ✅ 接收AlphaPilot信号文件
- ✅ 标准化股票代码格式（兼容多平台）
- ✅ 路由信号到对应策略模块
- ✅ 维护状态文件（观察名单、精英名单等）

**关键代码示例：**

#### 1. 股票代码标准化（支持多平台格式）
```python
# 输入：AlphaPilot格式 "603353.SH" 或 "300444.SZ"
# 输出：掘金格式 "SHSE.603353" 或 "SZSE.300444"

def convert_stock_code(code):
    """将AlphaPilot格式转换为平台标准格式"""
    if not code or '.' not in code:
        return code
    
    parts = code.split('.')
    
    # 已经是平台格式（如 SHSE.603353）
    if parts[0] in ['SHSE', 'SZSE']:
        return code
    
    # AlphaPilot格式（如 603353.SH）
    stock_num = parts[0]
    exchange = parts[1].upper()
    
    if exchange == 'SH':
        return f'SHSE.{stock_num}'  # 掘金标准
    elif exchange == 'SZ':
        return f'SZSE.{stock_num}'  # 掘金标准
    
    return code
```

#### 2. 量比数据读取（严格从信号文件获取）
```python
def _get_latest_volume_ratio(self, code):
    """
    ⚠️ 铁律：量比必须从AlphaPilot信号文件获取
    ❌ 严禁使用掘金SDK的current()获取量比（不支持）
    ❌ 严禁自行计算公式替代
    """
    # 从 signals 目录读取最新信号文件
    signal_files = glob.glob(os.path.join(settings.SIGNAL_DIR_INPUT, "*.txt"))
    
    for sig_file in signal_files:
        with open(sig_file, 'r', encoding='utf-8') as f:
            lines = f.read().strip().split('\n')
        
        for line in lines:
            sig_data = json.loads(line)
            
            # 匹配股票代码（支持多种格式）
            sig_code = sig_data.get('code', '')
            sig_pure = self._normalize_code(sig_code)  # 提取纯数字
            
            if sig_pure == pure_code:
                # ✅ 直接读取AlphaPilot计算的量比
                return float(sig_data.get('volume_ratio', 0))
    
    return None
```

---

### 第三层：执行层（手脚 - 掘金/QMT等平台）

**职责：**
- ✅ 执行下单操作（order_stock）
- ✅ 查询持仓信息（query_positions）
- ✅ 查询资产状况（query_asset）
- ✅ 获取实时价格（get_latest_prices）

**限制：**
- ❌ **不能**修改AlphaPilot的量比逻辑
- ❌ **不能**改变信号分流规则（即时vs延时）
- ❌ **不能**调整止损止盈阈值（由config/settings.py统一配置）

---

## 🔑 核心不可变原则

### 原则1：量比数据来源唯一性

```
✅ 正确做法：
   volume_ratio = 从 signals/*.txt 文件读取

❌ 错误做法：
   volume_ratio = 掘金SDK.current()  # SDK不支持
   volume_ratio = 自行公式计算        # 违背大脑决策
```

**原因：**
- AlphaPilot使用专有算法计算量比（考虑早盘/午盘差异）
- 掘金SDK的`current()` API不支持量比字段
- 自行计算会导致策略逻辑偏离大脑意图

---

### 原则2：T+1合规是平台责任，不是大脑责任

```
✅ 正确做法：
   can_sell = pos.can_use_volume  # 掘金提供的可卖数量
   if can_sell <= 0:
       log("今日买入不可卖，跳过")

❌ 错误做法：
   修改AlphaPilot信号为"T+0可卖"  # 违背A股规则
   忽略can_use_volume检查         # 违反合规
```

**原因：**
- A股T+1制度是监管要求，所有平台必须遵守
- `can_use_volume`是掘金SDK提供的合规字段
- 大脑只负责决策"是否卖出"，手脚负责"能否卖出"

---

### 原则3：信号分流逻辑由大脑决定

```
AlphaPilot信号 → 本系统判断 → 路由到对应策略
                        ↓
            ┌───────────┴───────────┐
            ↓                       ↓
    即时策略(Signal)          延时策略(Delayed)
    - 量比≥阈值立即买          - 加入观察名单
    - 大盘联动风控              - T+N日检查量比
                               - 14:39保底买入
```

**禁止行为：**
- ❌ 将所有BUY信号都改为即时买入
- ❌ 取消延时策略的观察期
- ❌ 修改量比阈值的判断逻辑

---

## 🛡️ 平台适配指南

### 场景1：切换到QMT平台

**需要修改的部分：**
```python
# trader_engine.py 中的平台接口调用

# 掘金SDK
from gm.api import current, order_target_value

# 改为 QMT SDK
from xtquant.xttrader import XtTrader
from xtquant.xtdata import get_full_tick
```

**不需要修改的部分：**
```python
# ✅ 信号解析逻辑（保持不变）
sig_data = json.loads(signal_line)
volume_ratio = sig_data['volume_ratio']  # 仍从文件读取

# ✅ 策略分流逻辑（保持不变）
if delayed_strategy.is_delayed_stock(code):
    delayed_strategy.process_signal(...)
else:
    signal_strategy.execute(...)

# ✅ 量比对比逻辑（保持不变）
if current_vr >= trigger_vr:
    execute_buy()
```

---

### 场景2：切换到其它量化平台

**适配清单：**

| 模块 | 是否需要修改 | 说明 |
|------|------------|------|
| `core/trader_engine.py` | ✅ 需要 | 替换下单/查询API |
| `utils/logger.py` | ❌ 不需要 | 通用异步日志 |
| `strategies/signal_strategy.py` | ❌ 不需要 | 策略逻辑不变 |
| `strategies/delayed_strategy.py` | ❌ 不需要 | 量比从文件读取 |
| `risk/stop_loss.py` | ❌ 不需要 | 风控逻辑不变 |
| `config/settings.py` | ⚠️ 可能需要 | 调整阈值参数 |

---

## 🚫 常见错误案例与纠正

### 错误案例1：误用平台API替代量比

**错误代码：**
```python
# ❌ 错误：试图从掘金获取量比
tick_data = current([code], fields=['volume_ratio'])  # 不支持！
```

**正确代码：**
```python
# ✅ 正确：从AlphaPilot信号文件读取
volume_ratio = self._get_latest_volume_ratio(code)
```

---

### 错误案例2：忽略T+1合规检查

**错误代码：**
```python
# ❌ 错误：直接使用总持仓卖出
sell_volume = pos.volume  # 可能包含今日买入的股票
```

**正确代码：**
```python
# ✅ 正确：检查可卖数量
can_sell = pos.can_use_volume
if can_sell <= 0:
    log("今日买入不可卖，跳过")
    return
```

---

### 错误案例3：修改大脑的决策逻辑

**错误代码：**
```python
# ❌ 错误：因为掘金无法获取量比，改用价格对比
if current_price >= trigger_price * 1.02:  # 违背大脑意图
    execute_buy()
```

**正确代码：**
```python
# ✅ 正确：坚持使用量比（从文件读取）
current_vr = self._get_latest_volume_ratio(code)
if current_vr >= trigger_vr:  # 严格执行大脑决策
    execute_buy()
```

---

## 📊 架构优势总结

### 为什么采用"大脑-手脚"架构？

| 维度 | 传统架构 | 大脑-手脚架构 |
|------|---------|--------------|
| **决策来源** | 硬编码在策略中 | AlphaPilot智能体动态生成 |
| **平台依赖** | 强耦合，难以切换 | 解耦，快速适配 |
| **策略迭代** | 需修改代码重新部署 | 只需更新信号生成逻辑 |
| **多平台支持** | 每个平台独立开发 | 共用同一套策略引擎 |
| **风险控制** | 分散在各处 | 集中在大脑统一决策 |

---

## 🔧 开发规范

### 新增功能时的检查清单

- [ ] 是否修改了AlphaPilot的核心决策逻辑？（应为❌）
- [ ] 量比数据是否仍从信号文件读取？（应为✅）
- [ ] T+1合规检查是否完整？（应为✅）
- [ ] 股票代码标准化是否支持多格式？（应为✅）
- [ ] 日志是否记录了关键决策点？（应为✅）

### 代码审查要点

```python
# 审查者需确认：

# 1. 量比来源
assert volume_ratio comes from signals/*.txt  # ✅
assert volume_ratio NOT from platform API     # ✅

# 2. 合规检查
assert can_use_volume checked before SELL     # ✅
assert volume rounded to 100 shares           # ✅

# 3. 信号路由
assert BUY signals routed correctly           # ✅
assert delayed stocks added to watchlist      # ✅
```

---

## 📞 技术支持与反馈

如在平台适配过程中遇到疑问，请遵循以下流程：

1. **第一步**：查阅本文档，确认是否属于"大脑逻辑"还是"手脚适配"
2. **第二步**：检查是否有类似案例（见"常见错误案例"章节）
3. **第三步**：联系Alphapilot智能体团队
   - 邮箱: 497720537@qq.com
   - 电话: 13392077558

---

## 📝 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| V1.0 | 2026-04-24 | 首次发布，明确大脑-手脚架构原则 |

---

## ⚖️ 法律声明

**本系统的核心知识产权属于Alphapilot智能体团队。**

任何基于本系统的二次开发必须遵守：
1. 不得修改AlphaPilot的决策逻辑
2. 不得绕过T+1合规检查
3. 不得篡改量比数据来源
4. 必须在显著位置标注原作者信息

**违者将追究法律责任。**

---

**记住：大脑思考，手脚执行。各司其职，方能高效！** 🧠👐
