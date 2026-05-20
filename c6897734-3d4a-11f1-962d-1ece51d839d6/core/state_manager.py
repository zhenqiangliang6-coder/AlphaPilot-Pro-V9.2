# -*- coding: utf-8 -*-
import json
import os
import datetime
from config import settings
# 注意：这里只导入函数，不要在这里调用 get_logger()
from utils.logger import get_logger
from core.trader_engine import TraderEngine


def _normalize_stock_code(code):
    """
    标准化股票代码格式
    支持多种格式转换为掘金标准格式 (SHSE.XXXXXX / SZSE.XXXXXX)
    
    示例:
        688295.SH -> SHSE.688295
        SH.688295 -> SHSE.688295
        SHSE.688295 -> SHSE.688295 (保持不变)
    """
    # 如果已经是标准格式，直接返回
    if code.startswith('SHSE.') or code.startswith('SZSE.'):
        return code
    
    # 处理 688295.SH 格式
    if '.' in code:
        parts = code.split('.')
        stock_num = parts[0]
        suffix = parts[1].upper()
        
        if suffix in ['SH', 'SHANGHAI']:
            return f'SHSE.{stock_num}'
        elif suffix in ['SZ', 'SHENZHEN']:
            return f'SZSE.{stock_num}'
    
    # 纯数字代码，根据首位判断交易所
    if code.isdigit():
        if code.startswith('6'):
            return f'SHSE.{code}'
        else:
            return f'SZSE.{code}'
    
    # 无法识别，返回原样
    return code


class StateManager:
    def __init__(self, engine: TraderEngine):
        self.engine = engine
        self.elite_list = {}

    def load_elite_list(self):
        # 每次调用前先获取 logger 实例，确保不为 None
        logger = get_logger()
        
        if not os.path.exists(settings.STATE_FILE):
            self.elite_list = {}
            if logger: logger.log("[初始化] 未找到状态文件，初始化为空")
            return
        
        try:
            with open(settings.STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_positions = data.get('positions', {})
                
                # 【关键修复】标准化所有股票代码格式
                self.elite_list = {}
                for code, info in raw_positions.items():
                    normalized_code = _normalize_stock_code(code)
                    self.elite_list[normalized_code] = info
                
                if logger: 
                    logger.log("[初始化] 加载精英名单：" + str(len(self.elite_list)) + "只")
                    if self.elite_list:
                        logger.log("[调试] 精英名单内容: " + str(list(self.elite_list.keys())))
        except Exception as e:
            if logger: logger.log("[警告] 加载状态文件失败：" + str(e))
            import traceback
            if logger: logger.log("[调试] " + traceback.format_exc())
            self.elite_list = {}

    def save_elite_list(self):
        # 每次调用前先获取 logger 实例
        logger = get_logger()

        # 【修复】检查引擎是否连接（通过检查context是否存在）
        if not hasattr(self.engine, 'context') or self.engine.context is None:
            if logger: logger.log("[状态] 引擎未连接，跳过保存")
            return

        try:
            positions = self.engine.query_positions()
            new_list = {}
            
            if positions:
                codes = [p.stock_code for p in positions if p.volume > 0]
                latest_prices = self.engine.get_latest_prices(codes)
                
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
                            new_list[code] = {
                                'volume': p.volume,
                                'profit_ratio': round(profit, 4),
                                'close_price': price,
                                'cost_price': cost
                            }
                            count += 1
                
                self.elite_list = new_list
                if logger: logger.log("[保存] 扫描完成，" + str(count) + "只入选精英名单")
        except Exception as e:
            if logger: logger.log("[警告] 保存精英名单失败：" + str(e))
            import traceback
            if logger: logger.log("[调试] " + traceback.format_exc())
            return
