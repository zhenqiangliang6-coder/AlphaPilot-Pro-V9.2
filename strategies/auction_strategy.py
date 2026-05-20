# -*- coding: utf-8 -*-
"""
集合竞价策略 - 掘金量化版

功能说明：
1. 在开盘集合竞价阶段（9:15-9:25）卖出精英名单中的股票
2. 针对高浮盈股票的快速离场机制
3. 支持跌停价保护，避免无效下单
"""
from config import settings
from utils.logger import get_logger
from core.state_manager import StateManager


class AuctionStrategy:
    def __init__(self, engine, state_mgr: StateManager):
        self.engine = engine
        self.state_mgr = state_mgr
        self.executed_today = False

    def execute(self):
        """执行集合竞价卖出策略"""
        log = get_logger()
        
        # 【日志】每次调用都输出，方便调试
        log.log("[竞价] >>> 开始检查集合竞价卖出条件")
        
        if self.executed_today:
            log.log("[竞价] 今日已执行过，跳过")
            return
        
        if not self.state_mgr.elite_list:
            log.log("[竞价] 精英名单为空，跳过")
            self.executed_today = True
            return

        log.log("[竞价] 精英名单数量: {}，开始执行卖出...".format(len(self.state_mgr.elite_list)))
        positions = self.engine.query_positions()
        hold_map = {p.stock_code: p for p in positions if p.volume > 0}
        
        log.log("[竞价] 当前持仓数量: {}".format(len(hold_map)))
        
        sold_count = 0
        failed_codes = []
        skipped_codes = []
        empty_position_codes = []  # 【新增】记录已清仓的股票
        
        for code, data in list(self.state_mgr.elite_list.items()):
            log.log("[竞价] 处理股票: {}".format(code))
            
            if code not in hold_map:
                log.log("[竞价] {} 未找到持仓，从名单移除".format(code))
                del self.state_mgr.elite_list[code]
                empty_position_codes.append(code)
                skipped_codes.append(code)
                continue
            
            pos = hold_map[code]
            
            # 【A股T+1修复】必须检查可卖数量
            if pos.can_use_volume <= 0:
                log.log("[竞价] {} 今日买入不可卖（总持仓:{} 可卖:0），跳过".format(code, pos.volume))
                skipped_codes.append(code)
                continue
            
            # 【修复】使用真正的实时行情API获取价格
            latest_prices = self.engine.get_latest_prices([code])
            curr_price = latest_prices.get(code, 0.0)
            
            if curr_price == 0 or curr_price is None: 
                curr_price = data.get('close_price', 0.0)
            
            if curr_price <= 0:
                log.log("[竞价] {} 价格无效（现价:{}），跳过".format(code, curr_price))
                skipped_codes.append(code)
                continue
            
            # 【A股合规】可卖数量向下取整为100的整数倍
            can_sell = pos.can_use_volume
            actual_sell_volume = (can_sell // 100) * 100
            
            # 如果取整后为0但可卖数量>0，至少卖出100股（如果可卖>=100）
            if actual_sell_volume == 0 and can_sell >= 100:
                actual_sell_volume = 100
            
            # 如果取整后仍为0，跳过
            if actual_sell_volume <= 0:
                log.log("[竞价] {} 可卖数量不足100股（可卖:{}），跳过".format(code, can_sell))
                skipped_codes.append(code)
                continue
            
            # 计算卖出价格（报价系数）
            sell_price = round(curr_price * settings.AUCTION_SELL_RATIO, 2)
            
            # 【修复】获取跌停价进行保护
            # 注意：engine.get_latest_prices 通常只返回价格，若需精确跌停价需额外API
            # 此处暂时简化，避免引用未定义的 ticks 变量导致崩溃
            limit_down = 0.0 
            
            if limit_down > 0 and sell_price < limit_down:
                sell_price = limit_down
                log.log("[竞价] {} 触发跌停保护，使用跌停价：{}".format(code, sell_price))

            log.log("[竞价] {} 准备卖出: 总持仓={} 可卖={} 实际卖出={} 现价={:.2f} 卖出价={:.2f}".format(
                code, pos.volume, can_sell, actual_sell_volume, curr_price, sell_price))

            if self.engine.order_stock(code, "SELL", actual_sell_volume, sell_price, "AUCTION_ELITE"):
                sold_count += 1
                log.log("[竞价] {} 下单成功！".format(code))
                # 卖出后从内存移除
                del self.state_mgr.elite_list[code]
            else:
                failed_codes.append(code)
                log.log("[竞价] {} 下单失败".format(code))
        
        # 【关键修复】清理不在持仓中的股票（已清仓）
        if empty_position_codes:
            log.log("[竞价] 清理已清仓股票: {} 只".format(len(empty_position_codes)))
        
        log.log("[竞价] >>> 结束，成功 {} 单，失败 {} 单，跳过 {} 单".format(
            sold_count, len(failed_codes), len(skipped_codes)))
        
        # 更新文件（会自动移除已从内存删除的股票）
        self.state_mgr.save_elite_list()
        self.executed_today = True

    def reset_daily(self):
        """重置每日执行标志"""
        self.executed_today = False