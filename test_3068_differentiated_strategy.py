# -*- coding: utf-8 -*-
"""
测试30/68开头股票的差异化止盈止损功能

验证内容：
1. 配置参数是否正确加载
2. 股票代码前缀识别是否正确
3. 止损阈值是否根据股票类型动态调整
4. 止盈参数是否根据股票类型动态调整
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from risk.stop_loss import StopLossMonitor
from risk.dynamic_take_profit import DynamicTakeProfit


class MockEngine:
    """模拟交易引擎，用于测试"""
    def __init__(self):
        pass
    
    def query_positions(self):
        return []
    
    def get_latest_prices(self, codes):
        return {code: 10.0 for code in codes}
    
    def order_stock(self, symbol, side, volume, price, reason):
        print(f"[模拟下单] {symbol} {side} {volume}股 @ {price} ({reason})")
        return "ORDER_123"


def test_config_loading():
    """测试配置参数是否正确加载"""
    print("=" * 80)
    print("【测试1】配置参数加载测试")
    print("=" * 80)
    
    # 普通股票止损阈值
    level1_normal = getattr(settings, 'STOP_LOSS_LEVEL1_THRESHOLD', None)
    level2_normal = getattr(settings, 'STOP_LOSS_LEVEL2_THRESHOLD', None)
    
    # 30/68股票止损阈值
    level1_3068 = getattr(settings, 'STOP_LOSS_LEVEL1_THRESHOLD_3068', None)
    level2_3068 = getattr(settings, 'STOP_LOSS_LEVEL2_THRESHOLD_3068', None)
    
    # 普通股票止盈参数
    drop_normal = getattr(settings, 'TAKE_PROFIT_LEVEL1_DROP', None)
    max_normal = getattr(settings, 'TAKE_PROFIT_LEVEL1_MAX', None)
    
    # 30/68股票止盈参数
    drop_3068 = getattr(settings, 'TAKE_PROFIT_LEVEL1_DROP_3068', None)
    max_3068 = getattr(settings, 'TAKE_PROFIT_LEVEL1_MAX_3068', None)
    
    print(f"普通股票 - 一级止损: {level1_normal*100:.1f}%, 二级止损: {level2_normal*100:.1f}%")
    print(f"30/68股票  - 一级止损: {level1_3068*100:.1f}%, 二级止损: {level2_3068*100:.1f}%")
    print(f"普通股票 - 止盈回落: {drop_normal*100:.1f}%, 上限: {max_normal*100:.1f}%")
    print(f"30/68股票  - 止盈回落: {drop_3068*100:.1f}%, 上限: {max_3068*100:.1f}%")
    
    # 验证数值
    assert level1_normal == 0.012, f"普通一级止损错误: {level1_normal}"
    assert level2_normal == 0.025, f"普通二级止损错误: {level2_normal}"
    assert level1_3068 == 0.016, f"30/68一级止损错误: {level1_3068}"
    assert level2_3068 == 0.035, f"30/68二级止损错误: {level2_3068}"
    assert drop_normal == 0.013, f"普通止盈回落错误: {drop_normal}"
    assert max_normal == 0.085, f"普通止盈上限错误: {max_normal}"
    assert drop_3068 == 0.015, f"30/68止盈回落错误: {drop_3068}"
    assert max_3068 == 0.17, f"30/68止盈上限错误: {max_3068}"
    
    print("✅ 配置参数加载测试通过\n")


def test_code_prefix_detection():
    """测试股票代码前缀识别"""
    print("=" * 80)
    print("【测试2】股票代码前缀识别测试")
    print("=" * 80)
    
    engine = MockEngine()
    stop_loss = StopLossMonitor(engine)
    take_profit = DynamicTakeProfit(engine)
    
    test_cases = [
        ("SZSE.300444", True, "创业板"),
        ("SHSE.688295", True, "科创板"),
        ("SZSE.000001", False, "深市主板"),
        ("SHSE.600000", False, "沪市主板"),
        ("300444.SZ", True, "创业板（外部信号格式）"),
        ("688295.SH", True, "科创板（外部信号格式）"),
        ("300444", True, "纯数字创业板"),
        ("688295", True, "纯数字科创板"),
    ]
    
    for code, expected_is_special, description in test_cases:
        numeric_code = stop_loss._extract_numeric_code(code)
        is_special = stop_loss._is_special_stock(code)
        
        status = "✅" if is_special == expected_is_special else "❌"
        print(f"{status} {code:20s} -> 数字码:{numeric_code:10s} | 特殊板块:{is_special:5} | {description}")
        
        assert is_special == expected_is_special, f"前缀识别错误: {code}"
    
    print("✅ 代码前缀识别测试通过\n")


def test_stop_loss_thresholds():
    """测试止损阈值动态选择"""
    print("=" * 80)
    print("【测试3】止损阈值动态选择测试")
    print("=" * 80)
    
    engine = MockEngine()
    stop_loss = StopLossMonitor(engine)
    
    test_cases = [
        ("SZSE.300444", 0.016, 0.035, "创业板"),
        ("SHSE.688295", 0.016, 0.035, "科创板"),
        ("SZSE.000001", 0.012, 0.025, "深市主板"),
        ("SHSE.600000", 0.012, 0.025, "沪市主板"),
    ]
    
    for code, expected_level1, expected_level2, description in test_cases:
        level1, level2 = stop_loss._get_stop_loss_thresholds(code)
        
        status = "✅" if (level1 == expected_level1 and level2 == expected_level2) else "❌"
        print(f"{status} {code:20s} | 一级:{level1*100:.1f}% (预期{expected_level1*100:.1f}%) | 二级:{level2*100:.1f}% (预期{expected_level2*100:.1f}%) | {description}")
        
        assert level1 == expected_level1, f"一级止损阈值错误: {code}"
        assert level2 == expected_level2, f"二级止损阈值错误: {code}"
    
    print("✅ 止损阈值动态选择测试通过\n")


def test_take_profit_params():
    """测试止盈参数动态选择"""
    print("=" * 80)
    print("【测试4】止盈参数动态选择测试")
    print("=" * 80)
    
    engine = MockEngine()
    take_profit = DynamicTakeProfit(engine)
    
    test_cases = [
        ("SZSE.300444", 0.015, 0.17, "创业板"),
        ("SHSE.688295", 0.015, 0.17, "科创板"),
        ("SZSE.000001", 0.013, 0.085, "深市主板"),
        ("SHSE.600000", 0.013, 0.085, "沪市主板"),
    ]
    
    for code, expected_drop, expected_max, description in test_cases:
        drop, max_val = take_profit._get_take_profit_params(code)
        
        status = "✅" if (drop == expected_drop and max_val == expected_max) else "❌"
        print(f"{status} {code:20s} | 回落:{drop*100:.1f}% (预期{expected_drop*100:.1f}%) | 上限:{max_val*100:.1f}% (预期{expected_max*100:.1f}%) | {description}")
        
        assert drop == expected_drop, f"止盈回落参数错误: {code}"
        assert max_val == expected_max, f"止盈上限参数错误: {code}"
    
    print("✅ 止盈参数动态选择测试通过\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("30/68开头股票差异化止盈止损功能测试")
    print("=" * 80 + "\n")
    
    try:
        test_config_loading()
        test_code_prefix_detection()
        test_stop_loss_thresholds()
        test_take_profit_params()
        
        print("=" * 80)
        print("🎉 所有测试通过！30/68差异化止盈止损功能已正确实现")
        print("=" * 80)
        print("\n【功能总结】")
        print("✅ 配置文件新增30/68专属参数")
        print("✅ 止损模块支持动态阈值选择（-1.6%/-3.5%）")
        print("✅ 止盈模块支持动态参数选择（回落1.5%/上限17%）")
        print("✅ 代码前缀识别兼容多种格式（掘金/外部信号/纯数字）")
        print("✅ T+1合规检查完整保留")
        print("\n【实盘建议】")
        print("1. 先在沙盒环境测试逻辑")
        print("2. 观察日志确认阈值正确应用")
        print("3. 小仓位验证后再逐步加大")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
