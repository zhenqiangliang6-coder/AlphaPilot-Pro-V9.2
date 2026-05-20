# -*- coding: utf-8 -*-
"""
信号驱动策略 - 掘金量化版（工业级事件驱动）
"""

import os
import json
import shutil
import time
import threading
import datetime
from config import settings
from utils.logger import get_logger
from gm.api import current


def convert_stock_code(code):
    """股票代码转换为掘金标准格式"""
    if not code or '.' not in code:
        return code
    
    parts = code.split('.')
    if parts[0] in ['SHSE', 'SZSE']:
        return code
    
    stock_num = parts[0]
    exchange = parts[1].upper()
    
    if exchange == 'SH':
        return f'SHSE.{stock_num}'
    elif exchange == 'SZ':
        return f'SZSE.{stock_num}'
    
    return code


class SignalStrategy:
    def __init__(self, engine):
        self.engine = engine
        self.order_history = {}
        self.history_lock = threading.Lock()
        self.delayed_strategy = None

    def set_delayed_strategy(self, delayed_strat):
        """注入延时策略实例"""
        self.delayed_strategy = delayed_strat

    def _get_index_change(self):
        """
        获取上证指数(SHSE.000001)相对于今日开盘价的涨跌幅
        """
        try:
            # 获取上证指数实时行情
            ticks = current(['SHSE.000001'], fields=['price', 'open'])
            if ticks and len(ticks) > 0:
                tick = ticks[0]
                price = tick.get('price', 0)
                open_price = tick.get('open', 0)
                if open_price > 0:
                    change_pct = (price - open_price) / open_price * 100
                    return round(change_pct, 2)
        except Exception:
            # 异常静默处理，由调用方统一输出警告
            pass
        return None

    # ============================================================
    # ⭐ 事件驱动入口（watchdog 调用）
    # ============================================================
    def process_single_signal(self, signal_file_path):
        log = get_logger()
        
        if not os.path.exists(signal_file_path):
            log.log(f"[警告] 信号文件不存在: {signal_file_path}")
            return
        
        filename = os.path.basename(signal_file_path)
        has_valid_action = False
        
        try:
            with open(signal_file_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                
                try:
                    sig = json.loads(line)
                    code = convert_stock_code(sig.get('code'))
                    action = sig.get('action')
                    price = float(sig.get('price', 0))
                    vr = float(sig.get('volume_ratio', 0))
                    
                    if not code or not action:
                        continue
                    
                    has_valid_action = True
                    
                    # ============================
                    # SELL 信号直接执行
                    # ============================
                    if action == "SELL":
                        self._execute_signal(code, action, price, vr)
                        continue
                    
                    # ============================
                    # BUY 信号：延时策略优先处理
                    # ============================
                    if self.delayed_strategy:
                        
                        # ⭐ 核心逻辑：所有BUY信号先交给延时策略判断
                        added = self.delayed_strategy.process_signal(code, action, price, vr)
                        
                        if added:
                            # 成功加入观察名单 → 跳过立即策略
                            log.log(f"[信号分流] {code} 已加入延时观察名单")
                            continue
                        else:
                            # 未加入观察名单,需要进一步判断原因
                            if self.delayed_strategy.is_delayed_stock(code):
                                # 是延时股票但未加入(可能量比不足或在等待期)
                                log.log(f"[立即策略-阻断] {code} 属于延时股票，禁止立即买入")
                                continue
                            
                            # 不是延时股票 → 执行立即策略
                            # (继续向下执行到 _execute_signal)
                    
                    # ============================
                    # 非延时股票 → 执行立即策略
                    # ============================
                    self._execute_signal(code, action, price, vr)
                
                except Exception as e:
                    log.log(f"[解析] JSON 错误 {filename}: {e}")
            
            # 归档文件
            dest = os.path.join(settings.SIGNAL_DIR_PROCESSED, filename)
            if os.path.exists(dest):
                dest = os.path.join(settings.SIGNAL_DIR_PROCESSED, f"{int(time.time())}_{filename}")
            shutil.move(signal_file_path, dest)
            
            # 【修复】增加明确的归档日志，即使没有符合条件的个股也能看到文件被处理了
            if has_valid_action:
                log.log(f"[归档] {filename} -> processed (包含有效信号)")
            else:
                log.log(f"[归档] {filename} -> processed (无有效信号内容)")
        
        except Exception as e:
            log.log(f"[错误] 处理文件 {filename} 失败: {e}")

    # ============================================================
    # ⭐ 传统扫描模式（兼容）
    # ============================================================
    def process_files(self):
        log = get_logger()
        
        if not os.path.exists(settings.SIGNAL_DIR_INPUT):
            return
        
        try:
            files = [f for f in os.listdir(settings.SIGNAL_DIR_INPUT) if f.endswith(".txt")]
        except Exception as e:
            log.log(f"[错误] 读取信号目录失败: {e}")
            return
        
        for filename in sorted(files):
            self.process_single_signal(os.path.join(settings.SIGNAL_DIR_INPUT, filename))

    # ============================================================
    # ⭐ 执行立即策略（BUY/SELL）
    # ============================================================
    def _execute_signal(self, code, action, price, vr):
        log = get_logger()
        
        # 【探照灯】明确记录开始处理该信号
        log.log(f"[立即策略-启动] {code} {action} | 价格:{price} | 量比:{vr}")
        
        # ⭐ 核心修复：SELL信号跳过重复保护，但保留大盘和量比检查（防止卖飞）
        if action == "SELL":
            log.log(f"[卖出优先] {code} 卖出信号，跳过重复保护，执行大盘/量比检查")
            
            # 1. 检查大盘和量比（防止卖飞）
            if not self._decide_action(action, vr):
                log.log(f"[卖出拦截] {code} 未通过大盘/量比过滤，暂不卖出（防止卖飞）")
                return False
            
            # 2. 检查持仓（不检查重复保护）
            positions = self.engine.query_positions()
            hold_map = {p.stock_code: p for p in positions if p.volume > 0}
            
            if code not in hold_map:
                log.log(f"[卖出失败] {code} 无持仓，跳过")
                return False
            
            pos = hold_map[code]
            if pos.can_use_volume <= 0:
                log.log(f"[卖出失败] {code} 无可用持仓，跳过")
                return False
            
            # 3. 卖出价格：当前价打1%折扣
            order_price = round(price * 0.99, 2)
            
            # 4. 【A股合规】可卖数量向下取整为100的整数倍
            can_sell = pos.can_use_volume
            actual_sell_volume = (can_sell // 100) * 100
            
            # 如果取整后为0但可卖数量>=100，至少卖出100股
            if actual_sell_volume == 0 and can_sell >= 100:
                actual_sell_volume = 100
            
            # 如果取整后仍为0，跳过
            if actual_sell_volume <= 0:
                log.log(f"[卖出失败] {code} 可卖数量不足100股（可卖:{can_sell}），跳过")
                return False
            
            # 5. 执行卖出（使用取整后的数量）
            result = self.engine.order_stock(code, "SELL", actual_sell_volume, order_price, "SIGNAL_V9")
            if result:
                log.log(f"[卖出成功] {code} 卖出 {actual_sell_volume} 股 @ {order_price} (总持仓:{pos.volume} 可卖:{can_sell})")
            return result
        
        # ====================
        # BUY 信号：继续执行完整过滤逻辑
        # ====================
        
        # 1. 过滤策略（集成大盘联动控制）
        if not self._decide_action(action, vr):
            log.log(f"[立即策略-终止] {code} 未通过大盘/量比过滤")
            return False
        
        # 2. 重复保护
        if not self._check_repeat_protection(code, action):
            log.log(f"[保护] {code} {action} 在保护期内，跳过")
            return False
        
        # 3. 仓位计算
        allow, vol, reason = self._check_position_and_calculate_volume(code, action, price)
        if not allow:
            log.log(f"[仓位] {code} 计算失败: {reason}")
            return False
        
        # 4. 下单
        order_price = round(price * 1.01, 2)
        result = self.engine.order_stock(code, action, vol, order_price, "SIGNAL_V9")
        if result:
            log.log(f"[立即策略-成功] {code} 订单已提交")
        return result

    # ============================================================
    # ⭐ BUY/SELL 过滤逻辑（含大盘联动与时段区分）
    # ============================================================
    def _decide_action(self, action, vr):
        """
        根据大盘涨跌幅、量比和时间段决定是否交易
        
        【V9.2 新增】分时段差异化量比阈值:
        - 09:30-10:30: 量比 ≥ 1.2 (早盘宽松)
        - 10:30-11:30: 量比 ≥ 2.2 (上午严格)
        - 13:00-14:00: 量比 ≥ 3.0 (下午更严格)
        - 14:00-15:00: 量比 ≥ 3.8 (尾盘最严格)
        """
        log = get_logger()
        index_change = self._get_index_change()
        
        # 【调试】打印大盘状态
        if index_change is not None:
            log.log(f"[大盘监控] 上证指数涨跌幅: {index_change:.2f}%")
        else:
            log.log(f"[大盘监控] 无法获取上证指数数据（可能是非交易时间或API延迟），禁止交易")
            return False

        # 获取当前时间，判断具体时段
        now = datetime.datetime.now()
        time_str = now.strftime("%H%M")
        
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
        else:
            period = "非交易时段"
            time_slot = "non_trading"

        # ==================== 买入策略 ====================
        if action == "BUY":
            # 【V9.2 新增】分时段量比阈值
            vr_thresholds = {
                "morning_early": 1.2,    # 09:30-10:30
                "morning_late": 2.2,     # 10:30-11:30
                "afternoon_early": 3.0,  # 13:00-14:00
                "afternoon_late": 3.8,   # 14:00-15:00
            }
            
            threshold = vr_thresholds.get(time_slot, 999)  # 非交易时段默认极高阈值
            
            # 规则 1: 大盘在 -0.35% 至 1.9% 之间
            if -0.35 <= index_change <= 1.9:
                if vr >= threshold:
                    log.log(f"[买入通过] {period} | 大盘{index_change:.2f}% | 量比{vr:.2f} >= {threshold}")
                    return True
                else:
                    log.log(f"[买入拦截] {period} | 大盘{index_change:.2f}% | 量比{vr:.2f} < 阈值{threshold}")
                    return False
            
            # 规则 2: 大盘在 -1.0% 至 -0.35% 之间（弱势市场提高阈值）
            if -1.0 <= index_change < -0.35:
                weak_threshold = threshold * 1.5  # 弱势市场阈值提高50%
                if vr >= weak_threshold:
                    log.log(f"[买入通过] {period}(弱势) | 大盘{index_change:.2f}% | 量比{vr:.2f} >= {weak_threshold:.2f}")
                    return True
                else:
                    log.log(f"[买入拦截] {period}(弱势) | 大盘{index_change:.2f}% | 量比{vr:.2f} < 阈值{weak_threshold:.2f}")
                    return False
            
            log.log(f"[买入拦截] 大盘{index_change:.2f}% 超出安全区间 [-1.0%, 1.9%]")
            return False

        # ==================== 卖出策略 ====================
        else:
            # 规则 1: 大盘在 -0.35% 至 1.9% 之间
            if -0.35 <= index_change <= 1.9:
                if vr >= 1.5:
                    log.log(f"[卖出通过] 大盘{index_change:.2f}% | 量比{vr:.2f} >= 1.5")
                    return True
                else:
                    log.log(f"[卖出拦截] 大盘{index_change:.2f}% | 量比{vr:.2f} < 1.5")
                    return False
            
            # 规则 2: 大盘在 -1.0% 至 -0.35% 之间
            if -1.0 <= index_change < -0.35:
                if vr >= 0.8:
                    log.log(f"[卖出通过](弱势) 大盘{index_change:.2f}% | 量比{vr:.2f} >= 0.8")
                    return True
                else:
                    log.log(f"[卖出拦截](弱势) 大盘{index_change:.2f}% | 量比{vr:.2f} < 0.8")
                    return False
            
            log.log(f"[卖出拦截] 大盘{index_change:.2f}% 超出策略区间 [-1.0%, 1.9%]")
            return False

    # ============================================================
    # ⭐ 重复保护
    # ============================================================
    def _check_repeat_protection(self, code, action):
        key = f"{code}_{action}"
        now = time.time()
        
        with self.history_lock:
            if key in self.order_history and now - self.order_history[key] < settings.REPEAT_PROTECT_SECONDS:
                return False
            
            self.order_history[key] = now
            return True

    # ============================================================
    # ⭐ 仓位计算（掘金量化版）
    # ============================================================
    def _check_position_and_calculate_volume(self, code, action, price):
        """
        检查持仓并计算买入/卖出数量
        
        【V9.2 新增】仓位控制:
        - 首次买入: 使用总资产的33%
        - 火箭加仓: 利润达标后追加33%
        """
        log = get_logger()
            
        if action == "SELL":
            positions = self.engine.query_positions()
            pos = next((p for p in positions if p.stock_code == code), None)
            if not pos or pos.can_use_volume <= 0:
                return False, 0, "无可卖持仓"
            return True, pos.can_use_volume, "卖出全部可用"
            
        # BUY 逻辑
        asset = self.engine.query_asset()
        if not asset:
            return False, 0, "资产查询失败"
            
        available_cash = asset.get('cash', 0)
        total_asset = asset.get('total_asset', 0)
        
        if available_cash <= 0:
            return False, 0, "可用资金不足"
        
        # 【V9.2 新增】仓位控制：首次买入使用总资产的33%
        INITIAL_POSITION_RATIO = 0.33  # 33% 初始仓位
        
        # 计算目标买入金额（基于总资产而非可用现金）
        target_order_value = total_asset * INITIAL_POSITION_RATIO
        
        # 限制单笔最大金额（例如 50000 元）
        MAX_SINGLE_ORDER_VALUE = getattr(settings, 'FIXED_ORDER_AMOUNT', 50000)
        order_value = min(target_order_value, MAX_SINGLE_ORDER_VALUE)
        
        # 确保不超过可用现金的80%（保留安全边际）
        order_value = min(order_value, available_cash * 0.8)
        
        # 最小下单金额检查
        MIN_ORDER_VALUE = getattr(settings, 'MIN_ORDER_VALUE', 15000)
        if order_value < MIN_ORDER_VALUE:
            return False, 0, f"计算金额 {order_value:.2f} < 最小下单金额 {MIN_ORDER_VALUE}"
            
        if price <= 0:
            return False, 0, "价格无效"
                
        # 计算股数（100股整数倍）
        volume = int(order_value / price / 100) * 100
            
        if volume < 100:
            return False, 0, f"计算股数不足100股 (金额:{order_value:.2f})"
        
        actual_cost = volume * price
        log.log(f"[仓位计算] {code} 计划买入 {volume} 股 @ {price:.2f} ≈ {actual_cost:.2f} 元")
        log.log(f"[仓位控制] 总资产:{total_asset:.2f} | 33%={target_order_value:.2f} | 实际下单:{order_value:.2f}")
        
        return True, volume, "计算成功"