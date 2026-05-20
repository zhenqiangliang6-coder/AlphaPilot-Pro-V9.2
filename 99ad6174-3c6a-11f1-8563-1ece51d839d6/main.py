# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 主策略入口 (V9.1)

Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

策略ID: a62d366d-3c78-11f1-8563-1ece51d839d6
说明: 必须在掘金终端中创建同名策略实例才能运行
"""

from __future__ import print_function, absolute_import
from gm.api import *
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 80)
print("🚀 AlphaPilot Pro - 量化交易策略启动")
print("=" * 80)
print(f"策略ID: a62d366d-3c78-11f1-8563-1ece51d839d6")
print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

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
last_stop_loss_check = 0
last_take_profit_check = 0
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
    打印账户资金和持仓信息
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
            log.log(f"   可用资金: ¥{cash:,.2f}")
            log.log(f"   总资产:   ¥{total_asset:,.2f}")
            log.log(f"   持仓市值: ¥{market_value:,.2f}")
            log.log("=" * 60)
        
        # 【修复】直接使用掘金API查询持仓，避免格式转换问题
        from gm.api import get_position
        positions_raw = get_position(account_id=settings.ACCOUNT_ID)
        
        if positions_raw:
            log.log("📊 [当前持仓]")
            for pos in positions_raw:
                # pos 是掘金返回的原始字典
                stock_code = pos.get('symbol', 'N/A')
                volume = pos.get('volume', 0)
                can_use = pos.get('available', pos.get('available_today', 0))
                # 【关键修复】掘金返回的成本价字段是 vwap (成交均价)
                cost_price = pos.get('vwap', 0)
                
                log.log(f"   {stock_code}:")
                log.log(f"     持仓数量: {volume} 股")
                log.log(f"     可卖数量: {can_use} 股")
                log.log(f"     成本价:   ¥{cost_price:.2f}")
            log.log("=" * 60)
        else:
            log.log("📊 [当前持仓] 无持仓")
            log.log("=" * 60)
            
    except Exception as e:
        log.log(f"[错误] 查询账户信息失败: {e}")
        import traceback
        log.log(f"[调试] {traceback.format_exc()}")


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
    
    # ==================== 第七步：初始化心跳监控器====================
    heartbeat_monitor = HeartbeatMonitor(log.log, print_account_info)
    heartbeat_monitor.start()
    
    # ==================== 第八步：订阅行情数据====================
    subscribe(symbols=settings.SUBSCRIBE_SYMBOLS, frequency='60s', count=100)
    
    log.log("[成功] 策略初始化完成")
    log.log(f"[订阅] 已订阅 {len(settings.SUBSCRIBE_SYMBOLS)} 只股票")
    log.log(f"[订阅] 数据频率: 1分钟K线 (60s)")
    
    # 打印初始账户信息
    print_account_info()
    
    # ==================== 第九步：启动时立即扫描一次信号文件====================
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
    - 止损/止盈检查
    - 集合竞价策略执行
    - 延时策略和火箭加仓的时间触发检查
    """
    global last_stop_loss_check, last_take_profit_check
    global context_global
    
    if not bars:
        return
    
    current_time = context.now
    time_str = current_time.strftime("%H%M")
    today_str = current_time.strftime("%Y%m%d")
    current_ts = time.time()
    
    # 获取最新bar
    latest_bar = bars[-1]
    symbol = latest_bar['symbol']
    
    # 1. 止损检查 (每5秒)
    if current_ts - last_stop_loss_check >= settings.STOP_LOSS_CHECK_INTERVAL:
        log.log(f"🔍 [风控] 执行止损检查...")
        stop_loss_mon.check()
        last_stop_loss_check = current_ts
    
    # 2. 动态止盈检查 (仅在 09:50 后)
    if current_ts - last_take_profit_check >= 10 and _is_after_take_profit_start(time_str):
        log.log(f"📈 [止盈] 执行止盈检查...")
        take_profit_mon.check()
        last_take_profit_check = current_ts
    
    # 3. 集合竞价卖出策略（09:21-09:25）
    if is_auction_time(time_str):
        try:
            if auction_strat and not auction_strat.executed_today:
                log.log(f"🔔 [集合竞价] 开始执行精英名单卖出...")
                auction_strat.execute()
        except Exception as e:
            log.log(f"[错误] 集合竞价策略执行失败: {e}")
            import traceback
            log.log(f"[调试] {traceback.format_exc()}")
    
    # 4. 策略执行（仅在交易时间）
    if is_trading_time(time_str):
        # 检查延时策略（时间触发）
        delayed_strat.check_and_execute()
        
        # 火箭加仓检查（时间触发）
        rocket_strat.check_and_fire()


def on_tick(context, ticks):
    """
    Tick数据更新回调 (高频策略使用)
    """
    pass


def on_order_status(context, order):
    """
    订单状态更新回调
    """
    if log:
        log.log("=" * 60)
        log.log(f"📋 [订单状态更新]")
        log.log(f"   股票代码: {order['symbol']}")
        log.log(f"   订单状态: {order['status']}")
        log.log(f"   委托数量: {order.get('volume', 0)}")
        log.log(f"   委托价格: {order.get('price', 0)}")
        log.log(f"   订单类型: {'买入' if order.get('side') == 1 else '卖出'}")
        log.log("=" * 60)


def on_execution_report(context, exec_rpt):
    """
    成交回报回调
    """
    if log:
        log.log("=" * 60)
        log.log(f"✅ [成交确认]")
        log.log(f"   股票代码: {exec_rpt['symbol']}")
        log.log(f"   成交方向: {'买入' if exec_rpt['side'] == 1 else '卖出'}")
        log.log(f"   成交数量: {exec_rpt.get('volume', 0)} 股")
        log.log(f"   成交价格: ¥{exec_rpt.get('price', 0):.2f}")
        log.log(f"   成交金额: ¥{exec_rpt.get('volume', 0) * exec_rpt.get('price', 0):.2f}")
        log.log("=" * 60)


def on_backtest_finished(context, indicator):
    """
    回测结束回调
    """
    if log:
        log.log("="*60)
        log.log("回测完成")
        log.log(f"[收益] 总收益率: {indicator.get('pnl_ratio', 0):.2%}")
        log.log(f"[年化] 年化收益率: {indicator.get('annual_return', 0):.2%}")
        log.log(f"[最大回撤] {indicator.get('max_drawdown', 0):.2%}")
        log.log(f"[夏普比率] {indicator.get('sharpe_ratio', 0):.2f}")
        log.log("="*60)


def _is_after_take_profit_start(time_str):
    """判断是否在止盈开始时间之后"""
    return int(time_str) >= settings.EARLIEST_EXECUTION_TIME


if __name__ == '__main__':
    """
    主程序入口
    
    支持两种运行模式:
    1. 回测模式: python main.py --mode backtest
    2. 实盘/模拟模式: python main.py --mode live
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='AlphaPilot Pro - 掘金量化版')
    parser.add_argument('--mode', type=str, default='live', 
                       choices=['backtest', 'live'],
                       help='运行模式: backtest(回测) 或 live(实盘/模拟)')
    args = parser.parse_args()
    
    # 设置Token
    set_token(settings.GM_TOKEN)
    
    print(f"✅ Token 设置成功")
    print(f"💡 策略模式下，账户由掘金终端自动管理")
    print(f"   请确保在掘金终端中已连接账户: {settings.ACCOUNT_ID}")
    
    if args.mode == 'backtest':
        # 回测模式
        run(
            strategy_id='alphapilot_pro_v9',
            filename=__file__,
            mode=MODE_BACKTEST,
            token=settings.GM_TOKEN,
            backtest_start_time=settings.BACKTEST_START_DATE,
            backtest_end_time=settings.BACKTEST_END_DATE,
            backtest_initial_cash=settings.BACKTEST_INITIAL_CASH
        )
    else:
        # 实盘/模拟模式
        run(
            strategy_id='alphapilot_pro_v9_1',
            filename=os.path.basename(__file__),
            mode=MODE_LIVE,
            token=settings.GM_TOKEN
            # 【移除】不需要 accounts 参数
        )
