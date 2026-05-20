# -*- coding: utf-8 -*-
"""
动态止盈模块 - 完全独立的三级止盈策略（修复版）

功能说明：
1. 第一级（快速止盈）：所有股票上涨 3% 后回落 1.3% 立即卖出
2. 第二级（波段止盈）：60/00 开头股票上涨 9% 后 12 分钟卖出
3. 第三级（强势股止盈）：68/30 开头股票上涨 18% 后 12 分钟卖出

设计原则：
- 完全独立于买入策略和其他卖出策略
- 通过独立定时器在后台运行
- 止盈卖出不影响其他策略的买入逻辑

【重要】时间控制：
- 为避免开盘剧烈波动导致误触发，动态止盈仅在 09:35 之后执行
- 如需调整此时间，请修改 check() 方法中的 EARLIEST_EXECUTION_TIME 常量

【V9.2.1 修复】股票代码前缀判断BUG：
- 掘金SDK返回格式：SZSE.300444、SHSE.688295（带交易所前缀）
- 原代码使用 code[:2] 提取前缀，得到的是 "SZ"、"SH" 而非数字部分
- 修复：先提取纯数字代码，再判断前缀（60/00/68/30）
"""
import time
import datetime
import threading
from config import settings
from utils.logger import get_logger

class DynamicTakeProfit:
    def __init__(self, engine):
        self.engine = engine
        
        # 记录每只股票的止盈状态
        # 格式: {code: {
        #     'highest_profit': 0.0,      # 最高涨幅
        #     'peak_time': 0,             # 首次达到峰值的时间戳
        #     'triggered_level1': False,  # 是否已触发第一级
        #     'triggered_level2': False,  # 是否已触发第二级
        #     'triggered_level3': False   # 是否已触发第三级
        # }}
        self.profit_tracker = {}
        self.lock = threading.Lock()
        
        # 【V9.2 优化】从配置文件读取止盈参数（支持灵活调整）
        # 第一级：所有股票
        self.level1_gain_threshold = getattr(settings, 'TAKE_PROFIT_LEVEL1_GAIN', 0.03)    # 上涨阈值
        self.level1_gain_max = getattr(settings, 'TAKE_PROFIT_LEVEL1_MAX', 0.085)          # 涨幅上限
        self.level1_drop_threshold = getattr(settings, 'TAKE_PROFIT_LEVEL1_DROP', 0.013)   # 回落阈值
        
        # 【特殊板块止盈参数 - 30/68开头科创板/创业板】
        self.level1_drop_threshold_3068 = getattr(settings, 'TAKE_PROFIT_LEVEL1_DROP_3068', 0.015)   # 30/68回落阈值
        self.level1_gain_max_3068 = getattr(settings, 'TAKE_PROFIT_LEVEL1_MAX_3068', 0.17)           # 30/68涨幅上限
        
        # 第二级：60/00 开头股票
        self.level2_gain_threshold = getattr(settings, 'TAKE_PROFIT_LEVEL2_GAIN', 0.09)    # 上涨阈值
        self.level2_hold_minutes = getattr(settings, 'TAKE_PROFIT_LEVEL2_HOLD_MINUTES', 12) # 持有时间
        
        # 第三级：68/30 开头股票
        self.level3_gain_threshold = getattr(settings, 'TAKE_PROFIT_LEVEL3_GAIN', 0.18)    # 上涨阈值
        self.level3_hold_minutes = getattr(settings, 'TAKE_PROFIT_LEVEL3_HOLD_MINUTES', 12) # 持有时间
        
        # 【可配置】动态止盈最早执行时间（HHMM格式）
        # 默认 09:51，避开开盘前剧烈波动
        # 如需调整此时间，请修改 check() 方法中的 EARLIEST_EXECUTION_TIME 常量
        self.EARLIEST_EXECUTION_TIME = getattr(settings, 'TAKE_PROFIT_EARLIEST_TIME', "0951")

    def _extract_numeric_code(self, code):
        """
        【V9.2.1 新增】从掘金格式代码中提取纯数字部分
        
        参数：
            code: 股票代码，可能是以下格式：
                - SZSE.300444 (掘金标准格式)
                - SHSE.688295 (掘金标准格式)
                - 300444.SZ (外部信号格式)
                - 300444 (纯数字)
        
        返回：
            str: 纯数字股票代码，如 "300444"
        """
        if not code:
            return ""
        
        # 如果包含点号，分割处理
        if '.' in code:
            parts = code.split('.')
            # 尝试找到纯数字部分
            for part in parts:
                if part.isdigit():
                    return part
            # 如果没有纯数字部分，返回第一部分
            return parts[0]
        
        # 纯数字代码，直接返回
        if code.isdigit():
            return code
        
        # 无法识别，返回原样
        return code

    def _can_execute_now(self):
        """
        检查当前时间是否允许执行动态止盈
        
        返回：True=可以执行，False=未到执行时间
        
        【实盘修改指南】：
        - 如果想让动态止盈在 9:30 开盘后立即生效，将 EARLIEST_EXECUTION_TIME 改为 "0930"
        - 如果想延迟到 10:00 再执行，将 EARLIEST_EXECUTION_TIME 改为 "1000"
        - 如果想去掉时间限制（全天执行），直接返回 True
        """
        now = datetime.datetime.now()
        current_time = now.strftime("%H%M")
        
        # 判断当前时间是否早于最早执行时间
        if current_time < self.EARLIEST_EXECUTION_TIME:
            return False
        
        return True

    def check(self):
        """
        定期检查持仓，执行动态止盈
        
        调用时机：在主循环中定期调用（建议每 10-15 秒一次）
        
        【重要】时间过滤：
        - 仅在 EARLIEST_EXECUTION_TIME 之后执行（默认 09:35）
        - 避免开盘前5分钟剧烈波动导致误触发
        """
        log = get_logger()
        
        # 【时间检查】未到执行时间，直接跳过
        if not self._can_execute_now():
            # 可选：每分钟输出一次提示日志（避免刷屏）
            now = datetime.datetime.now()
            if now.second < 5:  # 每分钟的前5秒内输出
                log.log("[止盈] 当前时间 {} 早于最早执行时间 {}，暂不执行".format(
                    now.strftime("%H:%M"), 
                    self.EARLIEST_EXECUTION_TIME[:2] + ":" + self.EARLIEST_EXECUTION_TIME[2:]
                ))
            return
        
        positions = self.engine.query_positions()
        
        if not positions:
            return
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            volume = pos.volume
            
            # 【关键修复】兼容多种成本价字段名（与止损模块保持一致）
            # 掘金API可能返回: open_price, cost_price, avg_price
            open_price = getattr(pos, 'open_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
            
            if open_price <= 0:
                continue
            
            # 获取最新价格
            try:
                latest_prices = self.engine.get_latest_prices([code])
                current_price = latest_prices.get(code)
                
                if current_price is None or current_price <= 0:
                    current_price = open_price
            except Exception as e:
                log.log("[止盈] 获取 {} 行情失败: {}".format(code, e))
                continue
            
            # 计算当前盈亏比例
            profit_ratio = (current_price - open_price) / open_price
            
            # 更新止盈追踪状态
            self._update_tracker(code, profit_ratio)
            
            # 检查各级止盈条件
            self._check_level1(code, current_price, open_price, volume, profit_ratio)
            self._check_level2(code, current_price, open_price, volume, profit_ratio)
            self._check_level3(code, current_price, open_price, volume, profit_ratio)

    def _update_tracker(self, code, current_profit):
        """更新股票的最高涨幅记录"""
        # 【专家级修复】如果当前时间还没到最早执行时间，不记录峰值时间
        # 防止开盘前的剧烈波动导致计时器提前启动
        if not self._can_execute_now():
            return

        with self.lock:
            if code not in self.profit_tracker:
                self.profit_tracker[code] = {
                    'highest_profit': current_profit,
                    'peak_time': time.time(),
                    'triggered_level1': False,
                    'triggered_level2': False,
                    'triggered_level3': False
                }
            else:
                # 如果当前涨幅创新高，更新时间戳
                if current_profit > self.profit_tracker[code]['highest_profit']:
                    self.profit_tracker[code]['highest_profit'] = current_profit
                    self.profit_tracker[code]['peak_time'] = time.time()

    def _get_take_profit_params(self, code):
        """
        获取指定股票的止盈参数
        
        返回：(drop_threshold, gain_max)
        """
        numeric_code = self._extract_numeric_code(code)
        prefix = numeric_code[:2]
        
        if prefix in ['30', '68']:
            # 30/68开头使用专属参数
            return self.level1_drop_threshold_3068, self.level1_gain_max_3068
        else:
            # 普通股票使用标准参数
            return self.level1_drop_threshold, self.level1_gain_max

    def _check_level1(self, code, current_price, open_price, volume, profit_ratio):
        """
        第一级止盈：所有股票上涨 3% 后回落立即卖出
        
        【差异化策略】：
        - 普通股票：回落 1.3%，上限 8.5%
        - 30/68开头：回落 1.5%，上限 17%
        
        逻辑：
        1. 最高涨幅在 3% ~ 上限之间（超过上限交由第二/三级处理）
        2. 当前涨幅 <= 最高涨幅 - 回落阈值
        3. 尚未触发过第一级止盈
        4. 【A股T+1修复】必须检查可卖数量 > 0
        """
        log = get_logger()
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            highest = tracker['highest_profit']
            
            # 检查是否已触发
            if tracker['triggered_level1']:
                return
            
            # 【差异化】获取该股票的止盈参数
            drop_threshold, gain_max = self._get_take_profit_params(code)
            
            # 【新增】检查涨幅是否在有效范围内（3% ~ 上限）
            if highest > gain_max:
                # 涨幅超过上限，不执行第一级止盈，交由第二/三级处理
                return
            
            # 判断条件：最高涨过 3%，且当前回落了指定阈值
            if highest >= self.level1_gain_threshold:
                drop_from_peak = highest - profit_ratio
                if drop_from_peak >= drop_threshold:
                    # 【A股T+1修复】查询实际可卖数量
                    positions = self.engine.query_positions()
                    can_sell = 0
                    total_volume = 0
                    for pos in positions:
                        if pos.stock_code == code and pos.volume > 0:
                            can_sell = pos.can_use_volume
                            total_volume = pos.volume
                            break
                    
                    if can_sell <= 0:
                        log.log("[止盈跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行快速止盈".format(code, total_volume))
                        return
                    
                    # 判断是否为特殊板块
                    numeric_code = self._extract_numeric_code(code)
                    is_special = numeric_code[:2] in ['30', '68']
                    stock_type = "30/68特殊板块" if is_special else "普通股票"
                    
                    log.log("[止盈-快速] {} ({}) 触发第一级止盈 (最高涨幅: {:.2f}%, 当前涨幅: {:.2f}%, 回落: {:.2f}%, 上限:{:.2f}%, 可卖:{})".format(
                        code, stock_type, highest * 100, profit_ratio * 100, drop_from_peak * 100, gain_max*100, can_sell))
                    
                    # 执行卖出（使用可卖数量）
                    if self._execute_sell(code, can_sell, current_price, "止盈-快速(3%回落{:.1f}%)".format(drop_threshold*100)):
                        tracker['triggered_level1'] = True
                        log.log("[止盈] {} 第一级止盈完成，从追踪列表移除".format(code))

    def _check_level2(self, code, current_price, open_price, volume, profit_ratio):
        """
        第二级止盈：60/00 开头股票上涨 9% 后 12 分钟卖出
        
        逻辑：
        1. 股票代码以 60 或 00 开头
        2. 当前涨幅 >= 9%
        3. 距离首次达到 9% 已过 12 分钟
        4. 【A股T+1修复】必须检查可卖数量 > 0
        
        【V9.2.1 修复】先提取纯数字代码再判断前缀
        """
        log = get_logger()
        
        # 【V9.2.1 修复】提取纯数字代码进行前缀判断
        numeric_code = self._extract_numeric_code(code)
        code_prefix = numeric_code[:2]
        
        if code_prefix not in ['60', '00']:
            return
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            
            # 检查是否已触发
            if tracker['triggered_level2']:
                return
            
            # 判断是否达到涨幅阈值
            if profit_ratio >= self.level2_gain_threshold:
                # 首次达到，记录时间
                if tracker['peak_time'] == 0 or tracker['highest_profit'] < self.level2_gain_threshold:
                    tracker['peak_time'] = time.time()
                    tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                    log.log("[止盈-波段] {} (数字码:{}) 首次达到第二级阈值 (涨幅: {:.2f}%)，开始计时 12 分钟".format(
                        code, numeric_code, profit_ratio * 100))
                    return
                
                # 计算持有时间
                hold_seconds = time.time() - tracker['peak_time']
                hold_minutes = hold_seconds / 60.0
                
                if hold_minutes >= self.level2_hold_minutes:
                    # 【A股T+1修复】查询实际可卖数量
                    positions = self.engine.query_positions()
                    can_sell = 0
                    total_volume = 0
                    for pos in positions:
                        if pos.stock_code == code and pos.volume > 0:
                            can_sell = pos.can_use_volume
                            total_volume = pos.volume
                            break
                    
                    if can_sell <= 0:
                        log.log("[止盈跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行波段止盈".format(code, total_volume))
                        return
                    
                    log.log("[止盈-波段] {} (数字码:{}) 触发第二级止盈 (涨幅: {:.2f}%, 持有时间: {:.1f} 分钟, 可卖:{})".format(
                        code, numeric_code, profit_ratio * 100, hold_minutes, can_sell))
                    
                    # 执行卖出（使用可卖数量）
                    if self._execute_sell(code, can_sell, current_price, "止盈-波段(9%持有12分钟)"):
                        tracker['triggered_level2'] = True
                        log.log("[止盈] {} 第二级止盈完成，从追踪列表移除".format(code))

    def _check_level3(self, code, current_price, open_price, volume, profit_ratio):
        """
        第三级止盈：68/30 开头股票上涨 18% 后 12 分钟卖出
        
        逻辑：
        1. 股票代码以 68 或 30 开头（科创板/创业板）
        2. 当前涨幅 >= 18%
        3. 距离首次达到 18% 已过 12 分钟
        4. 【A股T+1修复】必须检查可卖数量 > 0
        
        【V9.2.1 修复】先提取纯数字代码再判断前缀
        """
        log = get_logger()
        
        # 【V9.2.1 修复】提取纯数字代码进行前缀判断
        numeric_code = self._extract_numeric_code(code)
        code_prefix = numeric_code[:2]
        
        if code_prefix not in ['68', '30']:
            return
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            
            # 检查是否已触发
            if tracker['triggered_level3']:
                return
            
            # 判断是否达到涨幅阈值
            if profit_ratio >= self.level3_gain_threshold:
                # 首次达到，记录时间
                if tracker['peak_time'] == 0 or tracker['highest_profit'] < self.level3_gain_threshold:
                    tracker['peak_time'] = time.time()
                    tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                    log.log("[止盈-强势] {} (数字码:{}) 首次达到第三级阈值 (涨幅: {:.2f}%)，开始计时 12 分钟".format(
                        code, numeric_code, profit_ratio * 100))
                    return
                
                # 计算持有时间
                hold_seconds = time.time() - tracker['peak_time']
                hold_minutes = hold_seconds / 60.0
                
                if hold_minutes >= self.level3_hold_minutes:
                    # 【A股T+1修复】查询实际可卖数量
                    positions = self.engine.query_positions()
                    can_sell = 0
                    total_volume = 0
                    for pos in positions:
                        if pos.stock_code == code and pos.volume > 0:
                            can_sell = pos.can_use_volume
                            total_volume = pos.volume
                            break
                    
                    if can_sell <= 0:
                        log.log("[止盈跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行强势止盈".format(code, total_volume))
                        return
                    
                    log.log("[止盈-强势] {} (数字码:{}) 触发第三级止盈 (涨幅: {:.2f}%, 持有时间: {:.1f} 分钟, 可卖:{})".format(
                        code, numeric_code, profit_ratio * 100, hold_minutes, can_sell))
                    
                    # 执行卖出（使用可卖数量）
                    if self._execute_sell(code, can_sell, current_price, "止盈-强势(18%持有12分钟)"):
                        tracker['triggered_level3'] = True
                        log.log("[止盈] {} 第三级止盈完成，从追踪列表移除".format(code))

    def _execute_sell(self, code, volume, current_price, reason):
        """
        执行卖出操作
        
        参数：
        - code: 股票代码
        - volume: 卖出数量
        - current_price: 当前价格
        - reason: 止盈原因（用于日志记录）
        
        返回：True 成功，False 失败
        """
        log = get_logger()
        
        # A股规则：卖出数量必须是100的整数倍
        actual_volume = (volume // 100) * 100
        
        if actual_volume <= 0:
            log.log("[止盈跳过] {} 数量不足100股，无法卖出".format(code))
            return False
        
        # 卖出价格：当前价格 * 0.99（略微让利，提高成交率）
        sell_price = round(current_price * 0.99, 2)
        
        log.log("[止盈执行] {} 卖出 {} 股 @ {} ({})".format(code, actual_volume, sell_price, reason))
        
        try:
            success = self.engine.order_stock(code, "SELL", actual_volume, sell_price, reason)
            
            if success:
                log.log("[止盈成功] {} 已卖出，原因: {}".format(code, reason))
                return True
            else:
                log.log("[止盈失败] {} 下单失败".format(code))
                return False
        except Exception as e:
            log.log("[止盈错误] {} 卖出异常: {}".format(code, e))
            return False

    def reset_tracker(self, code):
        """
        重置某只股票的止盈追踪（可选）
        
        使用场景：股票卖出后重新买入，需要重新追踪止盈
        """
        with self.lock:
            if code in self.profit_tracker:
                del self.profit_tracker[code]
