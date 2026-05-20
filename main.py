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

💡 跨目录信号同步请使用独立脚本: signal_sync_standalone.py
   或使用一键启动脚本: start_with_sync.bat

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
    策略初始化函数 - 掘金量化SDK入口
    
    Alphapilot智能体团队
    作者: 梁子羿、侯沣睿、梁茹真
    邮箱: 497720537@qq.com | 电话: 13392077558
    
    参数:
        context: 策略上下文对象
    """
    global log, engine, state_mgr, signal_strat, rocket_strat
    global delayed_strat, auction_strat, stop_loss_mon, take_profit_mon
    global signal_bus, heartbeat_monitor, signal_watcher
    
    # ==================== 第一步：初始化日志系统 ====================
    ensure_dirs()
    init_logger(settings.LOG_DIR)
    log = get_logger()
    
    # ==================== 第二步：自动清理Python缓存 ====================
    try:
        import shutil
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # 查找并删除所有 __pycache__ 目录
        cache_dirs = []
        for root, dirs, files in os.walk(project_root):
            # 跳过虚拟环境目录
            if 'quant_env' in root or '.venv' in root or 'venv' in root:
                continue
            
            for dir_name in dirs:
                if dir_name == '__pycache__':
                    cache_path = os.path.join(root, dir_name)
                    cache_dirs.append(cache_path)
        
        # 执行清理
        if cache_dirs:
            for cache_dir in cache_dirs:
                try:
                    shutil.rmtree(cache_dir)
                except Exception as e:
                    pass  # 静默失败，不影响启动
            
            log.log(f"🧹 [系统] 已清理 {len(cache_dirs)} 个缓存目录")
        else:
            log.log("✅ [系统] 无需清理缓存")
    except Exception as e:
        log.log(f"⚠️ [系统] 缓存清理失败（不影响运行）: {e}")
    
    log.log("="*60)
    log.log(f"启动 AlphaPilot Pro V9.1 (工业级事件驱动架构)")
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
    
    # 【关键优化】启动时重建精英名单（仅在尾盘14:40-15:00执行，避免早盘波动误判）
    current_time_str = datetime.datetime.now().strftime("%H%M")
    is_tail_window = "1440" <= current_time_str <= "1800"
    
    if is_tail_window:
        log.log("🔄 [精英名单] 尾盘时段(14:40-15:00)，重新扫描持仓并重建精英名单...")
        try:
            positions = engine.query_positions()
            if positions:
                codes = [p.stock_code for p in positions if p.volume > 0]
                latest_prices = engine.get_latest_prices(codes)
                
                new_elite_list = {}
                count = 0
                for p in positions:
                    if p.volume <= 0: 
                        continue
                    code = p.stock_code
                    cost = getattr(p, 'open_price', 0.0)
                    price = latest_prices.get(code, cost) if latest_prices else cost
                    
                    if price <= 0: 
                        price = cost
                    
                    if cost > 0 and price > 0:
                        profit = (price - cost) / cost
                        if profit > settings.ELITE_PROFIT_THRESHOLD:
                            new_elite_list[code] = {
                                'volume': p.volume,
                                'profit_ratio': round(profit, 4),
                                'close_price': price,
                                'cost_price': cost
                            }
                            count += 1
                
                # 更新内存和文件
                state_mgr.elite_list = new_elite_list
                import json
                with open(settings.STATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump({'positions': state_mgr.elite_list}, f, indent=2, ensure_ascii=False)
                
                log.log(f"✅ [精英名单] 重建完成，{count}只股票入选（浮盈>{settings.ELITE_PROFIT_THRESHOLD*100}%）")
                if new_elite_list:
                    for code, data in new_elite_list.items():
                        log.log(f"   📊 {code} - 持仓:{data['volume']}股 浮盈:{data['profit_ratio']*100:.2f}% 成本:{data['cost_price']:.2f} 现价:{data['close_price']:.2f}")
            else:
                log.log("ℹ️ [精英名单] 当前无持仓，精英名单为空")
        except Exception as e:
            log.log(f"[警告] 重建精英名单失败: {e}")
            import traceback
            log.log(f"[调试] {traceback.format_exc()}")
    else:
        log.log(f"ℹ️ [精英名单] 非尾盘时段({current_time_str})，仅加载历史数据，不重建（避免早盘波动误判）")
        log.log(f"💡 [提示] 精英名单将在交易日14:40-15:00自动重建并写入文件")
    
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
        take_profit_mon=take_profit_mon,
        delayed_strat=delayed_strat  # 【新增】注入延时策略，实现定时检查
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
        # 【新增】启动时检查竞价策略（仅显示日志，不执行卖出）
        if auction_strat and not auction_strat.executed_today:
            log.log("📋 [竞价策略] 启动时检查精英名单（仅观察模式）...")
            # 检查时间窗口，只有在竞价时间才实际执行卖出
            from utils.helpers import is_auction_time
            current_time_str = datetime.datetime.now().strftime("%H%M")
            if is_auction_time(current_time_str):
                log.log("🔔 [竞价时间] 当前在竞价时间窗口，将执行卖出")
                auction_strat.execute()
            else:
                log.log("⏰ [非竞价时间] 当前时间不在09:21-09:25，仅显示精英名单，不执行卖出")
                # 【优化】观察模式下也清理已清仓的股票
                if auction_strat.state_mgr.elite_list:
                    # 获取当前实际持仓
                    positions = auction_strat.engine.query_positions()
                    hold_map = {p.stock_code: p for p in positions if p.volume > 0}
                    
                    # 清理不在持仓中的股票
                    empty_codes = []
                    for code in list(auction_strat.state_mgr.elite_list.keys()):
                        if code not in hold_map:
                            log.log("[观察] {} 已不在持仓中，从精英名单移除".format(code))
                            del auction_strat.state_mgr.elite_list[code]
                            empty_codes.append(code)
                    
                    if empty_codes:
                        # 【修复】观察模式下只更新内存，不调用save_elite_list()重新扫描
                        # save_elite_list()会重新查询实时价格并计算浮盈，非交易时间可能失败
                        # 改为直接保存当前内存中的精英名单到文件
                        try:
                            with open(settings.STATE_FILE, 'w', encoding='utf-8') as f:
                                json.dump({'positions': auction_strat.state_mgr.elite_list}, f, indent=2, ensure_ascii=False)
                            log.log("[观察] 已清理 {} 只已清仓股票，精英名单文件已更新（保留{}只）".format(len(empty_codes), len(auction_strat.state_mgr.elite_list)))
                        except Exception as e:
                            log.log("[警告] 保存精英名单失败: {}".format(e))
                    
                    # 显示剩余的精英名单
                    if auction_strat.state_mgr.elite_list:
                        log.log("[观察] 精英名单数量: {} 只".format(len(auction_strat.state_mgr.elite_list)))
                        for code, data in auction_strat.state_mgr.elite_list.items():
                            pos = hold_map.get(code)
                            if pos:
                                log.log("[观察] {} - 持仓:{}股 浮盈:{}% 成本:{:.2f} 收盘:{:.2f}".format(
                                    code, 
                                    data.get('volume', 0),
                                    round(data.get('profit_ratio', 0) * 100, 2),
                                    data.get('cost_price', 0),
                                    data.get('close_price', 0)
                                ))
                            else:
                                log.log("[观察] {} - 已清仓（待删除）".format(code))
                    else:
                        log.log("[观察] 精英名单为空")
                else:
                    log.log("[观察] 精英名单为空")
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
    run(strategy_id='6901bc32-3d4b-11f1-962d-1ece51d839d6',
        filename='main.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562')
    
# if __name__ == '__main__':
#     """
#     掘金量化策略启动入口
    