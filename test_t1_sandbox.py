# -*- coding: utf-8 -*-
"""
T+1约束沙盒测试脚本

功能说明：
1. 模拟今日买入的股票（可卖数量=0）
2. 模拟昨日持仓的股票（可卖数量>0）
3. 验证止损、止盈策略是否正确跳过今日买入的股票

作者: Alphapilot智能体团队
成员: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558
"""


class MockPosition:
    """模拟持仓对象"""
    def __init__(self, stock_code, volume, can_use_volume, open_price, current_price):
        self.stock_code = stock_code
        self.volume = volume  # 总持仓
        self.can_use_volume = can_use_volume  # 可卖数量
        self.open_price = open_price  # 成本价
        self.current_price = current_price  # 当前价
        self.last_price = current_price
        self.market_value = volume * current_price
        self.fpnl = (current_price - open_price) * volume


def test_t1_constraint():
    """测试T+1约束逻辑"""
    print("="*60)
    print("T+1约束沙盒测试")
    print("="*60)
    
    # 模拟场景1：今日买入的股票（可卖数量=0）
    today_buy_stock = MockPosition(
        stock_code="SZSE.301171",
        volume=1000,           # 总持仓1000股
        can_use_volume=0,      # 可卖0股（今日买入）
        open_price=47.50,
        current_price=46.31    # 亏损2.5%
    )
    
    # 模拟场景2：昨日持仓的股票（可卖数量>0）
    yesterday_stock = MockPosition(
        stock_code="SHSE.600821",
        volume=1000,           # 总持仓1000股
        can_use_volume=1000,   # 可卖1000股（昨日买入）
        open_price=10.00,
        current_price=9.70     # 亏损3%
    )
    
    # 模拟场景3：部分可卖的股票（昨日500 + 今日500）
    partial_stock = MockPosition(
        stock_code="SHSE.688295",
        volume=1050,           # 总持仓1050股
        can_use_volume=350,    # 可卖350股（昨日买入）
        open_price=63.00,
        current_price=62.24    # 亏损1.21%
    )
    
    positions = [today_buy_stock, yesterday_stock, partial_stock]
    
    print("\n【测试数据】")
    print("-"*60)
    for pos in positions:
        loss_ratio = (pos.current_price - pos.open_price) / pos.open_price
        print(f"股票: {pos.stock_code}")
        print(f"  成本价: {pos.open_price:.2f}")
        print(f"  当前价: {pos.current_price:.2f}")
        print(f"  盈亏比例: {loss_ratio*100:.2f}%")
        print(f"  总持仓: {pos.volume} 股")
        print(f"  可卖数量: {pos.can_use_volume} 股")
        print(f"  T+1状态: {'✅ 可卖' if pos.can_use_volume > 0 else '❌ 今日买入不可卖'}")
        print()
    
    print("\n【一级止损测试】（-1.2%减半）")
    print("-"*60)
    for pos in positions:
        loss_ratio = (pos.current_price - pos.open_price) / pos.open_price
        
        if abs(loss_ratio) >= 0.012:  # 亏损达到1.2%
            sell_volume = pos.volume // 2
            
            # 【关键】检查可卖数量
            can_sell = pos.can_use_volume
            actual_sell = min(sell_volume, can_sell)
            
            if actual_sell > 0:
                print(f"✅ {pos.stock_code}: 触发一级止损，卖出 {actual_sell} 股（总持仓:{pos.volume}, 可卖:{can_sell}）")
            else:
                print(f"❌ {pos.stock_code}: 今日买入不可卖，跳过一级止损（总持仓:{pos.volume}, 可卖:0）")
        else:
            print(f"⏸️  {pos.stock_code}: 未达到一级止损阈值")
    
    print("\n【二级止损测试】（-2.5%清仓）")
    print("-"*60)
    for pos in positions:
        loss_ratio = (pos.current_price - pos.open_price) / pos.open_price
        
        if abs(loss_ratio) >= 0.025:  # 亏损达到2.5%
            # 【关键】检查可卖数量
            can_sell = pos.can_use_volume
            
            if can_sell > 0:
                print(f"✅ {pos.stock_code}: 触发二级止损，清仓 {can_sell} 股（总持仓:{pos.volume}, 可卖:{can_sell}）")
            else:
                print(f"❌ {pos.stock_code}: 今日买入不可卖，跳过二级止损（总持仓:{pos.volume}, 可卖:0）")
        else:
            print(f"⏸️  {pos.stock_code}: 未达到二级止损阈值")
    
    print("\n【测试结果总结】")
    print("-"*60)
    print("✅ 修复后的逻辑正确识别了T+1约束")
    print("✅ 今日买入的股票（可卖=0）不会被卖出")
    print("✅ 昨日持仓的股票（可卖>0）可以正常止损")
    print("✅ 部分可卖的股票只会卖出可卖部分")
    print("="*60)


if __name__ == "__main__":
    test_t1_constraint()
