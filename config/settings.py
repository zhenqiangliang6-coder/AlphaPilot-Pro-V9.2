# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 智能量化交易策略引擎 (掘金量化版)
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.0 - 掘金量化平台专用版
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ================= 基础路径配置 =================

# 1. 项目代码根目录 (自动获取)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR_CODE = CURRENT_DIR

# 【修复】项目根目录（用于访问根目录下的 signals 文件夹）
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ================= [路径架构] =================

# --- A. 信号输入区 ---
# 【修复】指向项目根目录的 signals 文件夹
SIGNAL_DIR_INPUT = os.path.join(PROJECT_ROOT, "signals")
SIGNAL_DIR_PROCESSED = os.path.join(SIGNAL_DIR_INPUT, "processed")

# --- B. 核心安全区 ---
BASE_DIR_SAFE = BASE_DIR_CODE
# 【修复】精英名单文件应该在 signals 目录下
STATE_FILE = os.path.join(SIGNAL_DIR_INPUT, "yesterday_holdings.json")
LOG_DIR = os.path.join(BASE_DIR_SAFE, "logs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")  # 【修复】指向项目根目录的 data 文件夹

# ================= 掘金平台配置 =================

# 掘金 Token (从环境变量读取，建议在 .env 文件中设置)
GM_TOKEN = os.getenv('GM_TOKEN', '')

if not GM_TOKEN:
    print("⚠️  警告: 未设置 GM_TOKEN，请在 .env 文件中配置")
    print("   格式: GM_TOKEN=your_token_here")

# 账户ID (掘金模拟账户或实盘账户)
ACCOUNT_ID = os.getenv('GM_ACCOUNT_ID', 'simulation')  # 默认使用模拟账户

# 运行模式 (live: 实盘/仿真, backtest: 回测)
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')  # 默认使用实盘/仿真模式

# ================ 测试安全模式（便于本地联调） ================
# 在虚拟环境或运行命令前设置环境变量 TEST_SAFE_MODE=1 可启用
TEST_SAFE_MODE = os.getenv('TEST_SAFE_MODE', '0') in ('1', 'true', 'True')
if TEST_SAFE_MODE:
    # 为联调降低下单金额与仓位，防止误下大单
    FIXED_ORDER_AMOUNT = float(os.getenv('TEST_FIXED_ORDER_AMOUNT', '5000.0'))
    MIN_ORDER_VALUE = int(os.getenv('TEST_MIN_ORDER_VALUE', '1000'))
    SINGLE_ORDER_CASH_RATIO = float(os.getenv('TEST_SINGLE_ORDER_CASH_RATIO', '0.1'))


# ================= 策略参数配置 (V9.2 优化版) =================

# --- [精英名单策略] ---
ELITE_PROFIT_THRESHOLD = 0.08 # 精英筛选阈值（浮盈 >8%）
AUCTION_SELL_RATIO = 0.95      # 竞价卖出报价系数（现价 95%）

# --- [无限加仓策略] ---
LEVEL_1_THRESHOLD = 30000.0     # 一级火箭触发阈值（总浮盈 >= 3万）
LEVEL_2_THRESHOLD = 70000.0    # 二级火箭触发阈值（总浮盈 >= 7万）
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间（9 分钟）
MIN_ORDER_VALUE = 10000        # 最小下单金额

# --- [资金策略 - V9.2 优化] ---
INITIAL_POSITION_RATIO = 0.33   # 【新增】初始仓位比例（33% 总资产）
BOOST_POSITION_RATIO = 0.33     # 【新增】火箭加仓比例（33% 总资产）
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金上限比例（80%，安全边际）
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限（5 万元）

# --- [分时段量比阈值 - V9.2 新增] ---
# 早盘(09:30-10:30): 量比 ≥ 1.2
# 上午(10:30-11:30): 量比 ≥ 2.2
# 下午(13:00-14:00): 量比 ≥ 3.0
# 尾盘(14:00-15:00): 量比 ≥ 3.8
# 弱势市场（大盘-1.0%至-0.35%）：上述阈值 * 1.5

# --- [仓位管理] ---
MAX_STOCK_COUNT = 20            # 最大持仓股票数量

# --- [风控策略 - V9.1] ---
STOP_LOSS_MONITOR_THRESHOLD = 0.005     # 止损监控触发阈值（-0.5%开始监控）
STOP_LOSS_LEVEL1_THRESHOLD = 0.012      # 一级止损阈值（-1.2%减半仓）⭐ 用户自定义
STOP_LOSS_LEVEL2_THRESHOLD = 0.025      # 二级止损阈值（-2.5%清仓）⭐ 用户自定义

# --- [特殊板块止损策略 - 30/68开头科创板/创业板] ---
STOP_LOSS_LEVEL1_THRESHOLD_3068 = 0.016     # 30/68开头一级止损阈值（-1.6%减半仓）
STOP_LOSS_LEVEL2_THRESHOLD_3068 = 0.035     # 30/68开头二级止损阈值（-3.5%清仓）

STOP_LOSS_CHECK_INTERVAL = 30           # 止损检查频率（每 30 秒）
STOP_LOSS_START_TIME = "1045"           # 硬止损开始执行时间（10:45 后）
STOP_LOSS_END_TIME = "1450"             # 硬止损结束执行时间（14:50 前）
ENABLE_HARD_STOP = True                 # 硬止损开关

# --- [动态止盈策略 - V9.2] ---
TAKE_PROFIT_EARLIEST_TIME = "0951"      # 动态止盈最早执行时间（09:51，避开开盘波动）

# 第一级止盈参数（通用）
TAKE_PROFIT_LEVEL1_GAIN = 0.03          # 第一级止盈涨幅阈值（3%）
TAKE_PROFIT_LEVEL1_DROP = 0.013         # 第一级止盈回落阈值（1.3%）
TAKE_PROFIT_LEVEL1_MAX = 0.085          # 第一级止盈涨幅上限（8.5%，超过则交由第二/三级）

# 【特殊板块止盈参数 - 30/68开头科创板/创业板】
TAKE_PROFIT_LEVEL1_DROP_3068 = 0.015    # 30/68开头第一级止盈回落阈值（1.5%）
TAKE_PROFIT_LEVEL1_MAX_3068 = 0.17      # 30/68开头第一级止盈涨幅上限（17%）

TAKE_PROFIT_LEVEL2_GAIN = 0.09          # 第二级止盈涨幅阈值（9%，适用于60/00开头）
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 12    # 第二级止盈持有时间（12分钟）
TAKE_PROFIT_LEVEL3_GAIN = 0.18          # 第三级止盈涨幅阈值（18%，适用于68/30开头）
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 12    # 第三级止盈持有时间（12分钟）

# --- [基础参数] ---
HEARTBEAT_INTERVAL = 3          # 主循环心跳间隔（秒）

# --- [延时策略参数] ---
DELAYED_STRATEGY_CHECK_INTERVAL = 3

# ================= 掘金订阅配置 =================

# 订阅的股票列表 (根据实际持仓动态调整)
# 初始为空列表,系统会根据信号自动订阅
SUBSCRIBE_SYMBOLS = []
