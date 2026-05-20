# -*- coding: utf-8 -*-
"""
动态止损模块 - 掘金量化版 (V9.1)

功能说明：
1. 监控阶段：当亏损达到-0.5%时开始跟踪记录
2. 一级止损：亏损达到-1.2%时，执行50%仓位减仓（30/68开头为-1.6%）
3. 二级止损：亏损达到-2.5%时，执行全部清仓（30/68开头为-3.5%）
4. 反弹保护：触发一级止损后，若反弹超过成本价，重置止损状态

【特殊板块策略】：
- 30/68开头股票（创业板/科创板）使用更宽松的止损阈值
- 一级止损：-1.6%减半仓（普通股票-1.2%）
- 二级止损：-3.5%清仓（普通股票-2.5%）

时间控制：
- 仅在 STOP_LOSS_START_TIME 之后执行（默认 10:45）
- 在 STOP_LOSS_END_TIME 之前结束（默认 14:50）
"""
from config import settings
from utils.logger import get_logger
import time
import threading
import datetime


class StopLossMonitor:
    def __init__(self, engine):
        self.engine = engine
        
        # 动态止损追踪器
        # 格式: {code: {
        #     'monitoring': False,           # 是否进入监控状态（-0.5%触发）
        #     'level1_triggered': False,     # 是否已触发一级止损
        #     'level1_sell_volume': 0,       # 一级止损已卖出数量
        #     'original_volume': 0,          # 原始持仓数量
        #     'open_price': 0.0,             # 开仓成本
        #     'monitor_start_time': 0,       # 开始监控的时间戳
        #     'lowest_profit': 0.0,          # 监控期间最低盈亏比例
        # }}
        self.stop_loss_tracker = {}
        self.lock = threading.Lock()

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

    def _is_special_stock(self, code):
        """
        判断是否为特殊板块股票（30/68开头）
        
        返回：True=30/68开头，False=其他
        """
        numeric_code = self._extract_numeric_code(code)
        prefix = numeric_code[:2]
        return prefix in ['30', '68']

    def _get_stop_loss_thresholds(self, code):
        """
        获取指定股票的止损阈值
        
        返回：(level1_threshold, level2_threshold)
        """
        if self._is_special_stock(code):
            # 30/68开头使用宽松阈值
            level1 = getattr(settings, 'STOP_LOSS_LEVEL1_THRESHOLD_3068', 0.016)
            level2 = getattr(settings, 'STOP_LOSS_LEVEL2_THRESHOLD_3068', 0.035)
        else:
            # 普通股票使用标准阈值
            level1 = getattr(settings, 'STOP_LOSS_LEVEL1_THRESHOLD', 0.012)
            level2 = getattr(settings, 'STOP_LOSS_LEVEL2_THRESHOLD', 0.025)
        
        return level1, level2

    def _execute_stop_loss(self, code, volume, price, reason):
        """
        执行止损卖出操作
        
        参数:
            code: 股票代码，如 'SZSE.300259'
            volume: 卖出数量（股）
            price: 卖出价格（None表示市价单）
            reason: 止损原因描述
        
        返回:
            bool: 是否成功执行
        """
        try:
            # 调用交易引擎的下单接口
            order_id = self.engine.order_stock(
                symbol=code,
                side="SELL",
                volume=volume,
                price=price,
                reason=reason
            )
            
            if order_id:
                return True
            else:
                return False
                
        except Exception as e:
            log = get_logger()
            log.log("[止损失败] {} 执行异常: {}".format(code, str(e)))
            import traceback
            traceback.print_exc()
            return False

    def check(self):
        """定期检查持仓，执行动态止损
        
        【重要】时间控制：
        - 仅在 STOP_LOSS_START_TIME 之后执行（默认 10:45）
        - 在 STOP_LOSS_END_TIME 之前结束（默认 14:50）
        - 避免开盘剧烈波动导致误触发止损
        - 避开尾盘集合竞价阶段（14:50-15:00）流动性差的问题
        - 如需调整时间，请修改 config/settings.py 中的相关配置
        """
        log = get_logger()  # 动态获取
        
        # 【强制日志】每次调用都输出，方便调试
        now = datetime.datetime.now()
        now_time = now.strftime("%H%M")
        
        log.log("[止损检查] 开始执行 (当前时间:{}, 窗口:{}-{})".format(
            now.strftime("%H:%M:%S"),
            settings.STOP_LOSS_START_TIME[:2] + ":" + settings.STOP_LOSS_START_TIME[2:],
            settings.STOP_LOSS_END_TIME[:2] + ":" + settings.STOP_LOSS_END_TIME[2:]
        ))
        
        # 【时间检查】判断是否在允许的时间窗口内
        # 未到开始时间，跳过
        if now_time < settings.STOP_LOSS_START_TIME:
            log.log("[止损跳过] 当前时间 {} 早于最早执行时间 {}，暂不执行".format(
                now.strftime("%H:%M"), 
                settings.STOP_LOSS_START_TIME[:2] + ":" + settings.STOP_LOSS_START_TIME[2:]
            ))
            return
        
        # 已超过结束时间，跳过
        if now_time >= settings.STOP_LOSS_END_TIME:
            log.log("[止损跳过] 当前时间 {} 已超过最晚执行时间 {}，今日止损检查结束".format(
                now.strftime("%H:%M"), 
                settings.STOP_LOSS_END_TIME[:2] + ":" + settings.STOP_LOSS_END_TIME[2:]
            ))
            return
        
        # 查询持仓
        positions = self.engine.query_positions()
        if not positions:
            log.log("[止损检查] 当前无持仓，跳过")
            return
        
        log.log("[止损检查] 发现 {} 只持仓股票，开始检查...".format(len(positions)))
        
        stop_loss_count = 0
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            current_volume = pos.volume
            
            # 【关键修复】兼容多种成本价字段名
            # 掘金API可能返回: open_price, cost_price, avg_price
            open_price = getattr(pos, 'open_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
            
            if open_price <= 0:
                log.log("[止损跳过] {} 成本价为0，跳过".format(code))
                continue
            
            # 【修复】使用真正的实时行情API获取最新价格
            latest_prices = self.engine.get_latest_prices([code])
            current_price = latest_prices.get(code)
            
            if current_price is None or current_price <= 0:
                current_price = open_price
            
            # 计算当前盈亏比例
            profit_ratio = (current_price - open_price) / open_price
            loss_ratio = -profit_ratio  # 转为正数表示亏损
            
            # 强制输出每只股票的盈亏情况（方便调试）
            log.log("[止损分析] {} 成本:{:.2f} 现价:{:.2f} 盈亏:{:.2f}% 亏损:{:.2f}%".format(
                code, open_price, current_price, profit_ratio*100, loss_ratio*100
            ))
            
            # 更新或初始化追踪器
            with self.lock:
                if code not in self.stop_loss_tracker:
                    self.stop_loss_tracker[code] = {
                        'monitoring': False,
                        'level1_triggered': False,
                        'level1_sell_volume': 0,
                        'original_volume': current_volume,
                        'open_price': open_price,
                        'monitor_start_time': 0,
                        'lowest_profit': profit_ratio
                    }
                    log.log("[止损初始化] {} 加入追踪器".format(code))
                
                tracker = self.stop_loss_tracker[code]
                
                # 更新最低盈亏比例（用于追踪最大回撤）
                if profit_ratio < tracker['lowest_profit']:
                    tracker['lowest_profit'] = profit_ratio
                
                # 更新原始持仓（如果变化）
                if tracker['original_volume'] == 0:
                    tracker['original_volume'] = current_volume
            
            # 【阶段1】监控触发：亏损达到-0.5%
            if not tracker['monitoring'] and loss_ratio >= 0.005:
                with self.lock:
                    tracker['monitoring'] = True
                    tracker['monitor_start_time'] = time.time()
                log.log("[止损-监控] {} 进入监控状态 (成本:{:.2f} 现价:{:.2f} 亏损:{:.2f}%)".format(
                    code, open_price, current_price, loss_ratio*100))
            
            if not tracker['monitoring']:
                log.log("[止损跳过] {} 亏损{:.2f}% < 监控阈值0.5%，未进入监控".format(code, loss_ratio*100))
                continue
            
            # 【反弹保护】
            if tracker['level1_triggered'] and profit_ratio > 0:
                with self.lock:
                    tracker['level1_triggered'] = False
                    tracker['level1_sell_volume'] = 0
                    tracker['monitoring'] = False
                    tracker['lowest_profit'] = profit_ratio
                log.log("[止损-重置] {} 股价反弹超过成本价，止损状态重置 (当前盈利:{:.2f}%)".format(
                    code, profit_ratio*100))
                continue
            
            # 【阶段2】一级止损：根据股票类型使用不同阈值
            level1_threshold, _ = self._get_stop_loss_thresholds(code)
            
            if not tracker['level1_triggered'] and loss_ratio >= level1_threshold:
                # 【A股T+1修复】必须先检查可卖数量
                remaining_positions = self.engine.query_positions()
                can_sell = 0
                for p in remaining_positions:
                    if p.stock_code == code and p.volume > 0:
                        can_sell = p.can_use_volume
                        break
                
                # 无可卖数量，跳过
                if can_sell <= 0:
                    log.log("[止损跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行一级止损".format(code, current_volume))
                    continue
                
                # 计算理论卖出数量（50%仓位）
                sell_volume = current_volume // 2
                
                # 【A股合规】向下取整为100的整数倍
                actual_sell_volume = (sell_volume // 100) * 100
                
                # 如果取整后为0但可卖数量>0，至少卖出100股（如果可卖>=100）
                if actual_sell_volume == 0 and can_sell >= 100:
                    actual_sell_volume = 100
                
                # 实际卖出数量不能超过可卖数量
                actual_sell_volume = min(actual_sell_volume, can_sell)
                
                # 最终再次确认可卖数量>0
                if actual_sell_volume > 0:
                    # 判断是否为特殊板块
                    is_special = self._is_special_stock(code)
                    stock_type = "30/68特殊板块" if is_special else "普通股票"
                    
                    log.log("[止损-一级] {} ({}) 触发一级止损 (成本:{:.2f} 现价:{:.2f} 亏损:{:.2f}% 阈值:{:.2f}% 总持仓:{} 可卖:{} 实际卖出:{})".format(
                        code, stock_type, open_price, current_price, loss_ratio*100, level1_threshold*100, current_volume, can_sell, actual_sell_volume))
                    
                    if self._execute_stop_loss(code, actual_sell_volume, current_price, "一级止损(-{:.1f}%减半)".format(level1_threshold*100)):
                        with self.lock:
                            tracker['level1_triggered'] = True
                            tracker['level1_sell_volume'] = actual_sell_volume
                        stop_loss_count += 1
                        log.log("[止损] {} 一级止损完成，已卖出 {} 股（可卖{}股）".format(code, actual_sell_volume, can_sell))
                    else:
                        log.log("[止损失败] {} 一级止损执行失败".format(code))
                else:
                    log.log("[止损跳过] {} 可卖数量不足100股（可卖:{}），无法执行一级止损".format(code, can_sell))
            
            # 【阶段3】二级止损：根据股票类型使用不同阈值
            _, level2_threshold = self._get_stop_loss_thresholds(code)
            
            if loss_ratio >= level2_threshold:
                # 【A股T+1修复】必须先检查可卖数量
                remaining_positions = self.engine.query_positions()
                can_sell = 0
                for p in remaining_positions:
                    if p.stock_code == code and p.volume > 0:
                        can_sell = p.can_use_volume
                        break
                
                # 无可卖数量，跳过
                if can_sell <= 0:
                    log.log("[止损跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行二级止损".format(code, current_volume))
                    continue
                
                # 【A股合规】清仓时直接使用可卖数量，不强制取整（可能包含零股）
                actual_sell_volume = can_sell
                
                # 判断是否为特殊板块
                is_special = self._is_special_stock(code)
                stock_type = "30/68特殊板块" if is_special else "普通股票"
                
                log.log("[止损-二级] {} ({}) 触发二级止损 (成本:{:.2f} 现价:{:.2f} 亏损:{:.2f}% 阈值:{:.2f}% 总持仓:{} 可卖:{} 实际卖出:{})".format(
                    code, stock_type, open_price, current_price, loss_ratio*100, level2_threshold*100, current_volume, can_sell, actual_sell_volume))
                
                if self._execute_stop_loss(code, actual_sell_volume, current_price, "二级止损(-{:.1f}%清仓)".format(level2_threshold*100)):
                    with self.lock:
                        # 清仓后移除追踪
                        del self.stop_loss_tracker[code]
                    stop_loss_count += 1
                    log.log("[止损] {} 二级止损完成，已清仓 {} 股（可卖{}股）".format(code, can_sell, can_sell))
                else:
                    log.log("[止损失败] {} 二级止损执行失败".format(code))
