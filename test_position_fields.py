# -*- coding: utf-8 -*-
"""
测试掘金SDK持仓字段 - T+1可平数量验证
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

用途：在掘金策略框架内测试Position对象的字段，确认可平数量字段的正确性
运行方式：在掘金量化终端中运行此策略
"""
from gm.api import *
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init(context):
    """策略初始化函数"""
    print("\n" + "="*80)
    print("🧪 掘金SDK持仓字段测试工具 - T+1可平数量验证")
    print("Alphapilot智能体团队 | 497720537@qq.com | 13392077558")
    print("="*80 + "\n")
    
    # 订阅沪深300指数（确保能收到行情，激活策略运行）
    subscribe(symbols='SHSE.000300', frequency='60s', count=1)
    
    # 延迟2秒后执行测试（确保系统完全初始化及交易通道连接）
    import threading
    timer = threading.Timer(2.0, test_position_fields)
    timer.start()


def test_position_fields():
    """测试持仓对象的所有字段"""
    
    print("=" * 80)
    print("📊 开始测试持仓字段")
    print("=" * 80)
    print()
    
    try:
        # 查询持仓
        positions = query_positions()
        
        if not positions:
            print("⚠️  当前无持仓，无法测试")
            print("💡 建议：请先买入一些股票，然后再次运行此策略")
            print("\n" + "="*80)
            print("✅ 测试完成（无持仓）")
            print("="*80)
            return
        
        print(f"✅ 当前持仓数量: {len(positions)} 只股票\n")
        
        for i, pos in enumerate(positions, 1):
            print(f"{'='*80}")
            print(f"📈 持仓 #{i}")
            print(f"{'='*80}")
            
            # 基本信息
            print(f"\n【基本信息】")
            print(f"  股票代码: {pos.stock_code}")
            print(f"  股票名称: {getattr(pos, 'stock_name', 'N/A')}")
            
            # 持仓数量（关键！）
            print(f"\n【持仓数量 - 核心字段】")
            print(f"  📦 总持仓 (volume): {pos.volume} 股")
            
            # ⭐ T+1合规模块：测试所有可卖相关字段
            print(f"\n【T+1合规字段测试】")
            
            # 方式1：available_now（✅ 正确字段）
            available_now = getattr(pos, 'available_now', None)
            if available_now is not None:
                print(f"  ✅ 当前可卖 (available_now): {available_now} 股 ⭐ 推荐使用")
            else:
                print(f"  ❌ 当前可卖 (available_now): 字段不存在")
            
            # 方式2：can_use_volume（兼容字段，映射到available_now）
            can_use_volume = getattr(pos, 'can_use_volume', None)
            if can_use_volume is not None:
                print(f"  ✅ 可平数量 (can_use_volume): {can_use_volume} 股")
            else:
                print(f"  ❌ 可平数量 (can_use_volume): 字段不存在")
            
            # 方式3：available（❌ 错误字段，包含今日买入）
            available = getattr(pos, 'available', None)
            if available is not None:
                warning = " ⚠️ 包含今日买入，不可用于卖出" if available != available_now else ""
                print(f"  ❌ 总可平 (available): {available} 股{warning}")
            else:
                print(f"  ❌ 总可平 (available): 字段不存在")
            
            # 今日买入数量
            available_today = getattr(pos, 'available_today', None)
            if available_today is not None:
                print(f"  📊 今日买入 (available_today): {available_today} 股")
            
            volume_today = getattr(pos, 'volume_today', None)
            if volume_today is not None:
                print(f"  📊 今日成交 (volume_today): {volume_today} 股")
            
            # 从raw字典验证
            if hasattr(pos, 'raw') and pos.raw:
                raw_available_now = pos.raw.get('available_now', None)
                raw_available = pos.raw.get('available', None)
                raw_available_today = pos.raw.get('available_today', None)
                
                print(f"\n【raw字典验证】")
                if raw_available_now is not None:
                    print(f"  ✅ raw['available_now']: {raw_available_now} 股")
                if raw_available is not None:
                    print(f"  ❌ raw['available']: {raw_available} 股（⚠️ 包含今日买入）")
                if raw_available_today is not None:
                    print(f"  📊 raw['available_today']: {raw_available_today} 股")
            
            # 验证T+1逻辑
            print(f"\n【T+1合规验证】")
            # 优先使用 available_now
            can_sell = available_now if available_now is not None else (can_use_volume if can_use_volume is not None else 0)
            
            if can_sell == 0:
                print(f"  ⚠️  今日买入或无持仓，不可卖出（T+1限制）")
            elif can_sell < pos.volume:
                today_buy = pos.volume - can_sell
                print(f"  ⚠️  部分可卖：{can_sell}/{pos.volume} 股")
                print(f"  💡 估计今日买入: {today_buy} 股（不可卖）")
                print(f"  ✅ 估计昨日持仓: {can_sell} 股（可卖）")
            else:
                print(f"  ✅ 全部可卖：{can_sell} 股")
            
            # 成本价字段
            print(f"\n【成本价字段】")
            if hasattr(pos, 'raw') and pos.raw:
                vwap_open = pos.raw.get('vwap_open', 0)
                vwap = pos.raw.get('vwap', 0)
                cost = pos.raw.get('cost', 0)
                
                if vwap_open > 0:
                    print(f"  ✅ VWAP_Open (vwap_open): {vwap_open:.2f} 元 ⭐ 优先使用")
                if vwap > 0:
                    print(f"  ✅ VWAP (vwap): {vwap:.2f} 元")
                if cost > 0:
                    calc_cost = cost / pos.volume if pos.volume > 0 else 0
                    print(f"  ✅ 成本总额 (cost): {cost:.2f} 元")
                    print(f"  💡 计算成本价: {calc_cost:.2f} 元")
            
            open_price = getattr(pos, 'open_price', 0) or getattr(pos, 'cost_price', 0) or getattr(pos, 'avg_price', 0)
            print(f"  💡 Position对象成本价: {open_price:.2f} 元")

            # 其他信息
            print(f"\n【其他信息】")
            open_price = getattr(pos, 'open_price', 0) or getattr(pos, 'cost_price', 0) or getattr(pos, 'avg_price', 0)
            print(f"  成本价: {open_price:.2f} 元")
            print(f"  持仓市值: {getattr(pos, 'market_value', 0):.2f} 元")
            print(f"  浮动盈亏: {getattr(pos, 'floating_pnl', 0):.2f} 元")
            
            # 列出所有可用属性
            print(f"\n【完整属性列表】")
            attrs = [attr for attr in dir(pos) if not attr.startswith('_')]
            print(f"  可用属性 ({len(attrs)}个): {', '.join(attrs[:20])}")
            if len(attrs) > 20:
                print(f"  ... 还有 {len(attrs) - 20} 个属性")
            
            # 显示raw内容（如果有）
            if hasattr(pos, 'raw') and pos.raw:
                print(f"\n【raw属性完整内容】")
                for key, value in pos.raw.items():
                    print(f"  {key}: {value}")
            
            print()
        
        print("=" * 80)
        print("✅ 测试完成！")
        print("=" * 80)
        print()
        print("📝 总结：")
        print("  1. 确认哪个字段代表'可平数量'（can_use_volume 或 available）")
        print("  2. 验证T+1逻辑是否正确（今日买入不可卖）")
        print("  3. 更新代码中所有卖出操作使用该字段")
        print()
        print("💡 提示：测试完成后，可以在掘金终端中停止策略")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def on_bar(context, bars):
    """K线数据回调（本测试不需要具体逻辑，但需存在以维持策略运行）"""
    pass


if __name__ == '__main__':
    """
    掘金量化策略启动入口
    
    参数说明:
        strategy_id: 策略ID，必须与掘金终端中创建的策略实例ID一致
        filename: 文件名，使用相对路径（与本文件名保持一致）
        mode: 运行模式 - MODE_LIVE(实时) / MODE_BACKTEST(回测)
        token: 绑定计算机的ID，可在系统设置-密钥管理中生成
    """
    run(strategy_id='6901bc32-3d4b-11f1-962d-1ece51d839d6',
        filename='test_position_fields.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562')
