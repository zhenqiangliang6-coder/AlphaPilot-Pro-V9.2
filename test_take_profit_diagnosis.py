# -*- coding: utf-8 -*-
"""
动态止盈模块独立测试策略（专家级诊断版）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

用途：在掘金策略环境中诊断动态止盈模块是否正常工作
"""

from gm.api import *
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings

# 全局变量
test_engine = None
test_log_func = None


def init(context):
    """初始化函数 - 在掘金策略环境中执行"""
    global test_engine, test_log_func
    
    print("=" * 80)
    print("🔍 动态止盈模块独立诊断工具（掘金环境）")
    print("=" * 80)
    
    # 初始化日志
    from utils.logger import init_logger, get_logger
    init_logger(settings.LOG_DIR)
    logger = get_logger()
    test_log_func = logger.log
    
    def log(msg=""):
        """同时输出到控制台和日志文件"""
        print(msg)
        if test_log_func:
            test_log_func(msg)
    
    # 测试1：直接使用掘金API查询持仓
    log("\n📌 测试1：查询当前持仓")
    log("-" * 80)
    
    try:
        positions_raw = get_position(account_id=settings.ACCOUNT_ID)
        
        if not positions_raw:
            log("❌ 未查询到任何持仓")
            return
        
        log(f"✅ 查询到 {len(positions_raw)} 只持仓股票\n")
        
        # 显示前5只持仓的详细信息
        for i, pos in enumerate(positions_raw[:5], 1):
            log(f"【持仓 #{i}】")
            log(f"  代码: {pos.get('symbol', 'N/A')}")
            log(f"  数量: {pos.get('volume', 0)}")
            
            if isinstance(pos, dict):
                vwap = pos.get('vwap', 0)
                last_price = pos.get('last_price', 0)
                log(f"  vwap: {vwap}")
                log(f"  last_price: {last_price}")
                
                if vwap > 0 and last_price > 0:
                    profit_pct = (last_price - vwap) / vwap * 100
                    log(f"  盈亏: {profit_pct:.2f}%")
            
            log("")  # 换行
    
    except Exception as e:
        log(f"❌ 查询失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    # 测试2：使用交易引擎查询持仓
    log("\n📌 测试2：使用交易引擎查询持仓")
    log("-" * 80)
    
    try:
        from core.trader_engine import TraderEngine
        
        test_engine = TraderEngine(context)
        positions = test_engine.query_positions()
        
        log(f"✅ 交易引擎查询到 {len(positions)} 只持仓股票\n")
        
        for i, pos in enumerate(positions[:5], 1):
            log(f"【持仓 #{i}】")
            log(f"  股票代码: {pos.stock_code}")
            log(f"  持仓数量: {pos.volume}")
            log(f"  可卖数量: {getattr(pos, 'can_use_volume', 'N/A')}")
            
            open_price = getattr(pos, 'open_price', 0.0)
            log(f"  成本价: {open_price}")
            
            log("")
    
    except Exception as e:
        log(f"❌ 查询失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    # 测试3：验证动态止盈模块字段获取逻辑
    log("\n📌 测试3：验证动态止盈模块字段获取逻辑")
    log("-" * 80)
    
    try:
        from risk.dynamic_take_profit import DynamicTakeProfit
        
        take_profit = DynamicTakeProfit(test_engine)
        positions = test_engine.query_positions()
        
        log(f"✅ 持仓数量: {len(positions)}")
        log(f"✅ 止盈模块实例: {take_profit}")
        log(f"✅ 止盈模块方法: check()\n")
        
        for i, pos in enumerate(positions[:3], 1):
            log(f"【测试股票 #{i}: {pos.stock_code}】")
            
            open_price = getattr(pos, 'open_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
            
            log(f"  成本价: {open_price}")
            
            if open_price <= 0:
                log("  ❌ 结论：成本价为0，止盈模块会跳过此股票\n")
            else:
                log(f"  ✅ 成功获取成本价 {open_price}，止盈模块会正常执行\n")
    
    except Exception as e:
        log(f"❌ 测试失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    # 测试4：实际调用动态止盈模块 check()
    log("\n📌 测试4：实际调用动态止盈模块 check()")
    log("-" * 80)
    
    try:
        from risk.dynamic_take_profit import DynamicTakeProfit
        
        take_profit = DynamicTakeProfit(test_engine)
        
        log("⏳ 开始执行止盈检查...\n")
        take_profit.check()
        
        log("\n✅ 止盈检查完成")
        log("💡 查看日志是否出现 '止盈分析' 或 '止盈执行'")
        log("💡 如果只有 '止盈跳过' → 涨幅未达阈值或时间未到")
    
    except Exception as e:
        log(f"❌ 测试失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    log("\n" + "=" * 80)
    log("🎯 诊断完成")
    log("=" * 80)
    log("\n💡 下一步:")
    log("1. 查看测试输出，定位止盈触发情况")
    log("2. 若出现 '止盈执行' → 系统正常工作")
    log("3. 若出现 '止盈跳过' → 涨幅未达阈值（正常现象）")
    log("4. 将输出发给技术支持分析")
    log("\n📞 技术支持: 497720537@qq.com | 13392077558")


def on_bar(context, bars):
    """本测试策略不做任何交易"""
    pass


if __name__ == '__main__':
    """
    掘金量化策略启动入口
    ⚠️ 重要：必须修改 strategy_id 为掘金终端中创建的策略实例ID！
    """
    run(
        strategy_id='a62d366d-3c78-11f1-8563-1ece51d839d6',
        filename='test_take_profit_diagnosis.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562'
    )
