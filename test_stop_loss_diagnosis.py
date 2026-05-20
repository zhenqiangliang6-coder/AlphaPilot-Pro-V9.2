# -*- coding: utf-8 -*-
"""
止损模块独立测试策略（最终修复版）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

用途：在掘金策略环境中诊断"成本价为0"的根本原因
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
    print("🔍 止损模块独立诊断工具（掘金环境）")
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
    log("\n📌 测试1：直接使用掘金API查询持仓")
    log("-" * 80)
    
    try:
        positions_raw = get_position(account_id=settings.ACCOUNT_ID)
        
        if not positions_raw:
            log("❌ 未查询到任何持仓")
            return
        
        log(f"✅ 查询到 {len(positions_raw)} 只持仓股票\n")
        
        # 显示前5只持仓的详细信息
        for i, pos in enumerate(positions_raw[:2], 1):
            log(f"【持仓 #{i}】")
            log(f"  类型: {type(pos)}")
            log(f"  代码: {pos.get('symbol', 'N/A')}")
            
            if isinstance(pos, dict):
                log(f"  字段列表: {list(pos.keys())}")
                
                cost_fields = ['cost_price', 'open_price', 'avg_price', 'vwap', 'open_avg_price', 'vwap_open', 'cost']
                for field in cost_fields:
                    if field in pos:
                        log(f"  ⚠️  {field} = {pos[field]}")
            else:
                log(f"  字段列表: {[attr for attr in dir(pos) if not attr.startswith('_')]}")
            
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
        
        for i, pos in enumerate(positions[:2], 1):
            log(f"【持仓 #{i}】")
            log(f"  类型: {type(pos)}")
            log(f"  股票代码: {pos.stock_code}")
            log(f"  持仓数量: {pos.volume}")
            
            open_price = getattr(pos, 'open_price', '不存在')
            cost_price = getattr(pos, 'cost_price', '不存在')
            avg_price = getattr(pos, 'avg_price', '不存在')
            
            log(f"  open_price: {open_price}")
            log(f"  cost_price: {cost_price}")
            log(f"  avg_price: {avg_price}")
            
            if open_price == '不存在' or open_price <= 0:
                if cost_price != '不存在' and cost_price > 0:
                    log(f"  ⚠️ open_price=0，但 cost_price 有值 → TraderEngine 字段映射问题")
                elif avg_price != '不存在' and avg_price > 0:
                    log(f"  ⚠️ open_price=0，但 avg_price 有值 → TraderEngine 字段映射问题")
                else:
                    log(f"  ❌ 所有成本价字段都为0或不存在")
            
            log("")
    
    except Exception as e:
        log(f"❌ 查询失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    # 测试3：验证止损模块字段获取逻辑
    log("\n📌 测试3：验证止损模块字段获取逻辑")
    log("-" * 80)
    
    try:
        from risk.stop_loss import StopLossMonitor
        
        stop_loss = StopLossMonitor(test_engine)
        positions = test_engine.query_positions()
        
        log(f"✅ 持仓数量: {len(positions)}")
        log(f"✅ 止损模块实例: {stop_loss}")
        log(f"✅ 止损模块方法: check()\n")
        
        for i, pos in enumerate(positions[:2], 1):
            log(f"【测试股票 #{i}: {pos.stock_code}】")
            
            open_price = getattr(pos, 'open_price', 0.0)
            log(f"  第一步 open_price = {open_price}")
            
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
                log(f"  第二步 cost_price = {open_price}")
            
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
                log(f"  第三步 avg_price = {open_price}")
            
            if open_price <= 0:
                log("  ❌ 结论：所有字段都为0，止损模块会跳过此股票\n")
            else:
                log(f"  ✅ 成功获取成本价 {open_price}，止损模块会正常执行\n")
    
    except Exception as e:
        log(f"❌ 测试失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    # 测试4：实际调用止损模块 check()
    log("\n📌 测试4：实际调用止损模块 check()")
    log("-" * 80)
    
    try:
        from risk.stop_loss import StopLossMonitor
        
        stop_loss = StopLossMonitor(test_engine)
        
        log("⏳ 开始执行止损检查...\n")
        stop_loss.check()
        
        log("\n✅ 止损检查完成")
        log("💡 查看日志是否出现 '止损分析' 或 '止损执行'")
        log("💡 如果只有 '止损跳过' → 成本价字段仍有问题")
    
    except Exception as e:
        log(f"❌ 测试失败: {e}")
        import traceback
        log(f"[调试] {traceback.format_exc()}")
        return
    
    log("\n" + "=" * 80)
    log("🎯 诊断完成")
    log("=" * 80)
    log("\n💡 下一步:")
    log("1. 查看测试输出，定位成本价字段问题")
    log("2. 若测试1显示 vwap / cost 存在 → 修 TraderEngine 字段映射")
    log("3. 若测试2 显示 open_price=0 但 vwap 有值 → 映射未生效（缓存）")
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
        strategy_id='c2dd98da-3d5a-11f1-962d-1ece51d839d6',
        filename='test_stop_loss_diagnosis.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562'
    )
