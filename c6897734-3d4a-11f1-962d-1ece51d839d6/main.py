# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 掘金量化版主程序入口（工业级事件驱动架构）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.1 - 工业级事件驱动架构
核心改进:
- watchdog 事件触发信号处理（零扫描开销）
- 异步日志队列（非阻塞 I/O）
- 心跳线程瘦身（仅负责心跳+账户信息）
- 信号总线模式（生产者-消费者解耦）

⚠️ 重要提示：
- Strategy ID 必须与掘金终端中创建的策略实例 ID 完全一致
- 详见文档: VSCODE_INDEPENDENT_RUN_MANDATORY.md
"""

from gm.api import *
import os
import sys
import time
import datetime
import json
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.logger import init_logger, get_logger
from utils.helpers import ensure_dirs, is_auction_time, is_silent_time, is_trading_time
from utils.heartbeat import HeartbeatMonitor
from utils.signal_watcher import SignalWatcher
from core.trader_engine import TraderEngine
from core.state_manager import StateManager
from core.signal_bus import SignalBus
from strategies.signal_strategy import SignalStrategy
from strategies.rocket_boost import RocketBoost
from strategies.delayed_strategy import DelayedStrategy
from strategies.auction_strategy import AuctionStrategy
from risk.stop_loss import StopLossMonitor
from risk.dynamic_take_profit import DynamicTakeProfit

# 全局变量
log = None
engine = None
state_mgr = None
signal_strat = None
rocket_strat = None
delayed_strat = None
auction_strat = None
stop_loss_mon = None
take_profit_mon = None
context_global = None  # 【新增】保存全局context

# 工业级组件
signal_bus = None
heartbeat_monitor = None
signal_watcher = None


def on_error(context, error_code, info):
    """
    自定义交易服务错误处理
    
    Alphapilot智能体团队
    作者: 梁子羿、侯沣睿、梁茹真
    邮箱: 497720537@qq.com | 电话: 13392077558
    
    参数:
        context: 策略上下文
        error_code: 错误代码
        info: 错误信息
    """
    log = get_logger()
    if not log:
        return
    
    # 交易消息服务相关错误（1100/1101）通常会自动恢复，降低日志级别
    if error_code in [1100, 1101]:
        # 只在首次出现时记录，避免刷屏
        if not hasattr(on_error, '_last_warning_time'):
            on_error._last_warning_time = 0
        
        current_time = time.time()
        # 每60秒最多记录一次
        if current_time - on_error._last_warning_time > 60:
            on_error._last_warning_time = current_time
            log.log(f'[交易服务] 连接状态变化: code={error_code}, {info} (将自动重连)')
    else:
        # 其他错误正常记录
        log.log(f'[交易服务错误] code={error_code}, info={info}')


def print_account_info():
    """
    打印账户资金和持仓信息（精简版）
    """
    global log, engine
    
    if not log or not engine:
        return
    
    try:
        # 查询资产
        asset = engine.query_asset()
        if asset:
            cash = asset.get('cash', 0) if isinstance(asset, dict) else getattr(asset, 'cash', 0)
            total_asset = asset.get('total_asset', 0) if isinstance(asset, dict) else getattr(asset, 'total_asset', 0)
            market_value = asset.get('market_value', 0) if isinstance(asset, dict) else getattr(asset, 'market_value', 0)
            
            log.log("=" * 60)
            log.log("💰 [账户资金]")
            log.log("   可用资金: ¥{:,.2f}".format(cash))
            log.log("   总资产:   ¥{:,.2f}".format(total_asset))
            log.log("   持仓市值: ¥{:,.2f}".format(market_value))
            log.log("=" * 60)
        
        # 【修复】直接使用掘金API查询持仓，避免格式转换问题
        from gm.api import get_position
        positions_raw = get_position(account_id=settings.ACCOUNT_ID)
        
        if positions_raw:
            # 【精简】只汇总显示持仓数量和盈亏概况，不逐个打印详情
            total_stocks = len(positions_raw)
            total_volume = sum(pos.get('volume', 0) for pos in positions_raw)
            
            log.log("📊 [当前持仓] 共 {} 只股票，总计 {} 股".format(total_stocks, total_volume))
            # 【可选】如需查看个股详情，可临时取消注释以下代码
            # for pos in positions_raw:
            #     stock_code = pos.get('symbol', 'N/A')
            #     volume = pos.get('volume', 0)
            #     log.log("   {}: {} 股".format(stock_code, volume))
            log.log("=" * 60)
        else:
            log.log("📊 [当前持仓] 无持仓")
            log.log("=" * 60)
            
    except Exception as e:
        log.log("[错误] 查询账户信息失败: {}".format(e))
        import traceback
        log.log("[调试] {}".format(traceback.format_exc()))


def init(context):
    """
    初始化函数 - 掘金平台入口点
    """
    global log, engine, state_mgr, signal_strat, rocket_strat, delayed_strat
    global auction_strat, stop_loss_mon, take_profit_mon
    global context_global
    global signal_bus, heartbeat_monitor, signal_watcher
    
    # 保存全局context
    context_global = context
    
    # ==================== 第一步：初始化日志系统（异步）====================
    init_logger(settings.LOG_DIR)
    log = get_logger()
    ensure_dirs()
    
    log.log("="*60)
    log.log("启动 AlphaPilot Pro V9.1 (工业级事件驱动架构)")
    log.log("="*60)
    log.log(f"[配置] 运行模式: {settings.RUN_MODE}")
    log.log(f"[配置] 账户ID: {settings.ACCOUNT_ID}")
    log.log(f"[配置] 订阅股票: {', '.join(settings.SUBSCRIBE_SYMBOLS)}")
    log.log("="*60)
    
    # ==================== 第二步：初始化交易引擎====================
    engine = TraderEngine(context)
    
    # ==================== 第三步：初始化状态管理器====================
    state_mgr = StateManager(engine)
    state_mgr.load_elite_list()
    
    # ==================== 第四步：初始化策略模块====================
    signal_strat = SignalStrategy(engine)
    rocket_strat = RocketBoost(engine)
    delayed_strat = DelayedStrategy(engine)
    auction_strat = AuctionStrategy(engine, state_mgr)
    stop_loss_mon = StopLossMonitor(engine)
    take_profit_mon = DynamicTakeProfit(engine)
    
    # 建立策略关联
    signal_strat.set_delayed_strategy(delayed_strat)
    
    # ==================== 第五步：初始化信号总线====================
    signal_bus = SignalBus(max_size=1000)
    
    # 注册信号消费者（从总线消费信号）
    signal_bus.register_consumer(signal_strat.process_single_signal)
    
    # 启动信号分发线程（传入 log.log 方法而不是 log 对象）
    signal_bus.start_dispatcher(log.log)
    
    # ==================== 第六步：初始化 watchdog 监听器====================
    signal_watcher = SignalWatcher(settings.SIGNAL_DIR_INPUT, signal_bus, log.log)
    signal_watcher.start()
    
    # ==================== 第七步：初始化心跳监控器（含风控检查）====================
    heartbeat_monitor = HeartbeatMonitor(
        log.log, 
        print_account_info,
        stop_loss_mon=stop_loss_mon,
        take_profit_mon=take_profit_mon
    )
    heartbeat_monitor.start()
    
    # ==================== 第八步：订阅行情数据====================
    subscribe(symbols=settings.SUBSCRIBE_SYMBOLS, frequency='60s', count=100)
    
    log.log("[成功] 策略初始化完成")
    log.log(f"[订阅] 已订阅 {len(settings.SUBSCRIBE_SYMBOLS)} 只股票")
    log.log(f"[订阅] 数据频率: 1分钟K线 (60s)")
    
    # 打印初始账户信息
    print_account_info()
    
    # ==================== 第九步：启动时立即扫描一次信号====================
    try:
        log.log("🚀 [启动扫描] 立即检查待处理信号...")
        signal_strat.process_files()
        delayed_strat.check_and_execute()
        rocket_strat.check_and_fire()
        log.log("✅ [启动扫描] 完成")
    except Exception as e:
        log.log(f"[警告] 启动扫描失败: {e}")
    
    # 启动提示
    log.log("=" * 60)
    log.log("💡 [提示] 工业级事件驱动架构已启动")
    log.log("💡 [watchdog] 新信号文件将立即触发处理（零扫描开销）")
    log.log("💡 [异步日志] 日志写入不阻塞主线程")
    log.log("💡 [心跳监控] 每5秒输出心跳，每60秒更新账户信息")
    log.log("💡 [交易时间] 09:30-11:30, 13:00-15:00")
    log.log("💡 [集合竞价卖出] 09:21-09:25")
    log.log("=" * 60)


def on_bar(context, bars):
    """
    K线数据更新回调
    
    职责：
    - 集合竞价策略执行
    - 延时策略和火箭加仓的时间触发检查
    - 【注意】止损/止盈已移至心跳线程独立执行，不再依赖bar数据
    """
    global context_global
    
    if not bars:
        return
    
    current_time = context.now
    time_str = current_time.strftime("%H%M")
    
    # 获取最新bar
    latest_bar = bars[-1]
    symbol = latest_bar['symbol']
    
    # 1. 集合竞价卖出策略（09:21-09:25）
    if is_auction_time(time_str):
        try:
            if auction_strat and not auction_strat.executed_today:
                log.log(f"🔔 [集合竞价] 开始执行精英名单卖出...")
                auction_strat.execute()
        except Exception as e:
            log.log(f"[错误] 集合竞价策略执行失败: {e}")
            import traceback
            log.log(f"[调试] {traceback.format_exc()}")
    
    # 2. 策略执行（仅在交易时间）
    if is_trading_time(time_str):
        # 检查延时策略（时间触发）
        delayed_strat.check_and_execute()
        
        # 火箭加仓检查（时间触发）
        rocket_strat.check_and_fire()


if __name__ == '__main__':
    """
    掘金量化策略启动入口
    
    参数说明:
        strategy_id: 策略ID，必须与掘金终端中创建的策略实例ID一致
        filename: 文件名，使用相对路径（与本文件名保持一致）
        mode: 运行模式 - MODE_LIVE(实时) / MODE_BACKTEST(回测)
        token: 绑定计算机的ID，可在系统设置-密钥管理中生成
        backtest_start_time: 回测开始时间
        backtest_end_time: 回测结束时间
        backtest_adjust: 股票复权方式 - ADJUST_NONE(不复权) / ADJUST_PREV(前复权) / ADJUST_POST(后复权)
        backtest_initial_cash: 回测初始资金
        backtest_commission_ratio: 回测佣金比例
        backtest_slippage_ratio: 回测滑点比例
        backtest_match_mode: 市价撮合模式 - 0(以下一tick/bar开盘价撮合) / 1(以当前tick/bar收盘价撮合)
    """
    run(strategy_id='a62d366d-3c78-11f1-8563-1ece51d839d6',
        filename='main.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562')
