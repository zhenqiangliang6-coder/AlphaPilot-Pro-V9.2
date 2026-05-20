# -*- coding: utf-8 -*-
"""
火箭加仓策略 - 掘金量化版
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.0 - 基于掘金平台
"""
from config import settings
from utils.logger import get_logger


class RocketBoost:
    def __init__(self, engine):
        self.engine = engine
        self.stage = 0
        self.fired_l1 = False
        self.fired_l2 = False
        self.boosted_codes = set()  # 记录已加仓的股票

    def check_and_fire(self):
        """检查浮盈并执行火箭加仓"""
        log = get_logger()
        
        # 计算总浮盈
        total_profit, profit_details = self._calc_profit()
        
        if total_profit <= 0:
            return
        
        log.log(f"[火箭] 当前总浮盈: {total_profit:.2f}元，阶段: {self.stage}")
        
        # 状态同步与触发
        if self.stage == 0 and total_profit >= settings.LEVEL_1_THRESHOLD:
            log.log(f"[火箭] 触发一级点火 (浮盈 {total_profit:.2f} >= {settings.LEVEL_1_THRESHOLD})")
            self._execute_boost(1, profit_details)
            self.stage = 1
            self.fired_l1 = True
            
        elif self.stage == 1 and total_profit >= settings.LEVEL_2_THRESHOLD:
            log.log(f"[火箭] 触发二级点火 (浮盈 {total_profit:.2f} >= {settings.LEVEL_2_THRESHOLD})")
            self._execute_boost(2, profit_details)
            self.stage = 2
            self.fired_l2 = True

    def _calc_profit(self):
        """计算所有持仓的总浮盈"""
        positions = self.engine.query_positions()
        if not positions:
            return 0.0, {}
        
        total_profit = 0.0
        profit_details = {}
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            volume = pos.volume
            
            # 【关键修复】兼容多种成本价字段名
            # 掘金API可能返回: open_price, cost_price, avg_price
            open_price = getattr(pos, 'open_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
            
            if open_price <= 0:
                continue
            
            # 【修复】使用真正的实时行情API获取最新价格
            latest_prices = self.engine.get_latest_prices([code])
            current_price = latest_prices.get(code)
            
            if current_price is None or current_price <= 0:
                current_price = open_price
            
            if open_price > 0 and current_price > 0:
                profit = (current_price - open_price) * volume
                if profit > 0:
                    total_profit += profit
                    profit_details[code] = {
                        'volume': volume,
                        'cost': open_price,
                        'current': current_price,
                        'profit': profit
                    }
        
        return round(total_profit, 2), profit_details

    def _execute_boost(self, stage, profit_details):
        """
        执行加仓逻辑
        
        【V9.2 优化】仓位控制:
        - 每次加仓使用总资产的33%
        - 必须利润达到阈值才能触发
        - 选择浮盈最高的股票进行加仓
        """
        log = get_logger()
        
        if not profit_details:
            log.log("[火箭] 无盈利持仓，跳过加仓")
            return
        
        # 【V9.2 新增】获取总资产用于仓位计算
        asset = self.engine.query_asset()
        if not asset:
            log.log("[火箭] 资产查询失败，跳过加仓")
            return
        
        total_asset = asset.get('total_asset', 0)
        available_cash = asset.get('cash', 0)
        
        # 【V9.2 新增】每次加仓使用总资产的33%
        BOOST_POSITION_RATIO = 0.33  # 33% 加仓仓位
        target_boost_value = total_asset * BOOST_POSITION_RATIO
        
        # 限制单笔最大金额
        MAX_SINGLE_ORDER_VALUE = getattr(settings, 'FIXED_ORDER_AMOUNT', 50000)
        order_value = min(target_boost_value, MAX_SINGLE_ORDER_VALUE)
        
        # 确保不超过可用现金的80%
        order_value = min(order_value, available_cash * 0.8)
        
        log.log(f"[火箭仓位] 总资产:{total_asset:.2f} | 33%={target_boost_value:.2f} | 实际可用:{order_value:.2f}")
        
        # 按浮盈排序，选择最好的股票
        sorted_stocks = sorted(
            profit_details.items(), 
            key=lambda x: x[1]['profit'], 
            reverse=True
        )
        
        # 一级点火：加仓 1 只，二级点火：加仓 2 只
        boost_count = 1 if stage == 1 else 2
        
        for i, (code, data) in enumerate(sorted_stocks[:boost_count]):
            if code in self.boosted_codes:
                log.log(f"[火箭] {code} 已加仓过，跳过")
                continue
            
            current_price = data['current']
            volume = data['volume']
            
            # 【V9.2 优化】根据目标金额计算加仓数量
            boost_volume = int(order_value / current_price / 100) * 100
            
            # 最小加仓数量检查
            if boost_volume < 100:
                log.log(f"[火箭] {code} 加仓数量不足100股，跳过")
                continue
            
            # 检查现金是否足够
            actual_cost = boost_volume * current_price
            if actual_cost > available_cash:
                log.log(f"[火箭] {code} 现金不足（需要{actual_cost:.2f}，可用{available_cash:.2f}），跳过加仓")
                continue
            
            # 执行买入
            order_price = round(current_price * 1.01, 2)
            if self.engine.order_stock(code, "BUY", boost_volume, order_price, f"BOOST_L{stage}"):
                self.boosted_codes.add(code)
                log.log(f"[火箭] L{stage} 加仓: {code} 买入 {boost_volume}股 @ {order_price} ≈ {actual_cost:.2f}元")
            else:
                log.log(f"[火箭] L{stage} 加仓失败: {code}")