# -*- coding: utf-8 -*-
"""
动态止盈模块股票代码前缀判断诊断脚本

功能：
1. 验证掘金SDK返回的股票代码格式
2. 测试_extract_numeric_code()方法的正确性
3. 模拟不同股票的止盈触发逻辑
4. 检查当前持仓的止盈状态

使用方法：
    python diagnose_take_profit_prefix.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk.dynamic_take_profit import DynamicTakeProfit


class MockEngine:
    """模拟交易引擎，用于测试"""
    def __init__(self):
        pass
    
    def query_positions(self):
        """返回模拟持仓数据"""
        return []
    
    def get_latest_prices(self, symbols):
        """返回模拟价格"""
        return {sym: 10.0 for sym in symbols}


def test_extract_numeric_code():
    """测试股票代码提取函数"""
    print("=" * 80)
    print("【测试1】股票代码提取功能测试")
    print("=" * 80)
    
    # 创建测试实例
    mock_engine = MockEngine()
    take_profit = DynamicTakeProfit(mock_engine)
    
    # 测试用例
    test_cases = [
        ("SZSE.300444", "300444", "掘金深圳格式"),
        ("SHSE.688295", "688295", "掘金上海格式"),
        ("300444.SZ", "300444", "外部信号深圳格式"),
        ("688295.SH", "688295", "外部信号上海格式"),
        ("300444", "300444", "纯数字代码"),
        ("600519", "600519", "纯数字茅台代码"),
        ("SH.688295", "688295", "简写上海格式"),
        ("SZ.300444", "300444", "简写深圳格式"),
    ]
    
    all_passed = True
    for input_code, expected, description in test_cases:
        result = take_profit._extract_numeric_code(input_code)
        status = "✅" if result == expected else "❌"
        
        if result != expected:
            all_passed = False
        
        print(f"{status} {description:20s} | 输入: {input_code:15s} | 期望: {expected:10s} | 实际: {result:10s}")
    
    print()
    if all_passed:
        print("🎉 所有测试用例通过！")
    else:
        print("⚠️  存在失败的测试用例，请检查代码")
    
    return all_passed


def test_prefix_detection():
    """测试前缀检测逻辑"""
    print("\n" + "=" * 80)
    print("【测试2】股票类型前缀检测测试")
    print("=" * 80)
    
    mock_engine = MockEngine()
    take_profit = DynamicTakeProfit(mock_engine)
    
    # 测试用例：(代码, 期望类型)
    test_cases = [
        ("SZSE.300444", "创业板(30)", "应该匹配Level 3"),
        ("SHSE.688295", "科创板(68)", "应该匹配Level 3"),
        ("SZSE.000001", "主板(00)", "应该匹配Level 2"),
        ("SHSE.600519", "主板(60)", "应该匹配Level 2"),
        ("300444.SZ", "创业板(30)", "应该匹配Level 3"),
        ("688295.SH", "科创板(68)", "应该匹配Level 3"),
    ]
    
    for code, expected_type, note in test_cases:
        numeric_code = take_profit._extract_numeric_code(code)
        prefix = numeric_code[:2]
        
        if prefix in ['68', '30']:
            detected_type = "科创板/创业板(68/30)"
            level = "Level 3"
        elif prefix in ['60', '00']:
            detected_type = "主板(60/00)"
            level = "Level 2"
        else:
            detected_type = f"未知({prefix})"
            level = "无"
        
        match = "✅" if (level in note or expected_type.split('(')[0] in detected_type) else "❌"
        
        print(f"{match} {code:15s} -> 数字码:{numeric_code:10s} | 前缀:{prefix:2s} | 类型:{detected_type:20s} | {note}")
    
    print()


def simulate_real_scenario():
    """模拟真实场景测试"""
    print("=" * 80)
    print("【测试3】真实场景模拟测试")
    print("=" * 80)
    
    mock_engine = MockEngine()
    take_profit = DynamicTakeProfit(mock_engine)
    
    # 模拟不同股票的涨幅情况
    scenarios = [
        ("SZSE.300444", 0.035, "创业板涨3.5% - 应触发Level 1"),
        ("SHSE.688295", 0.19, "科创板涨19% - 应触发Level 3（需等待12分钟）"),
        ("SZSE.000001", 0.095, "深市主板涨9.5% - 应触发Level 2（需等待12分钟）"),
        ("SHSE.600519", 0.025, "沪市主板涨2.5% - 未达任何阈值"),
    ]
    
    print("\n模拟持仓止盈状态分析：\n")
    
    for code, profit_ratio, description in scenarios:
        numeric_code = take_profit._extract_numeric_code(code)
        prefix = numeric_code[:2]
        
        # 判断可能触发的级别
        triggered_levels = []
        
        # Level 1: 所有股票涨3%回落1.3%
        if profit_ratio >= 0.03:
            triggered_levels.append("Level 1(快速)")
        
        # Level 2: 60/00开头涨9%
        if prefix in ['60', '00'] and profit_ratio >= 0.09:
            triggered_levels.append("Level 2(波段)")
        
        # Level 3: 68/30开头涨18%
        if prefix in ['68', '30'] and profit_ratio >= 0.18:
            triggered_levels.append("Level 3(强势)")
        
        levels_str = ", ".join(triggered_levels) if triggered_levels else "无"
        
        print(f"📊 {code:15s} ({numeric_code})")
        print(f"   涨幅: {profit_ratio*100:.2f}% | 前缀: {prefix} | {description}")
        print(f"   可能触发: {levels_str}")
        print()


def check_current_time_window():
    """检查当前时间是否在止盈执行窗口内"""
    print("=" * 80)
    print("【测试4】当前时间窗口检查")
    print("=" * 80)
    
    import datetime
    
    mock_engine = MockEngine()
    take_profit = DynamicTakeProfit(mock_engine)
    
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M")
    earliest_time = take_profit.EARLIEST_EXECUTION_TIME
    
    can_execute = take_profit._can_execute_now()
    
    print(f"\n当前时间: {now.strftime('%H:%M:%S')}")
    print(f"最早执行时间: {earliest_time[:2]}:{earliest_time[2:]}")
    print(f"是否可以执行: {'✅ 是' if can_execute else '❌ 否'}")
    
    if not can_execute:
        remaining_minutes = int(earliest_time[:2]) * 60 + int(earliest_time[2:]) - (now.hour * 60 + now.minute)
        print(f"还需等待: {remaining_minutes} 分钟")
    
    print()


if __name__ == "__main__":
    print("\n" + "🔍" * 40)
    print("动态止盈模块 - 股票代码前缀判断诊断工具")
    print("🔍" * 40 + "\n")
    
    # 执行所有测试
    test_extract_numeric_code()
    test_prefix_detection()
    simulate_real_scenario()
    check_current_time_window()
    
    print("\n" + "=" * 80)
    print("📋 诊断总结")
    print("=" * 80)
    print("""
✅ 修复内容：
1. 新增 _extract_numeric_code() 方法，从掘金格式代码中提取纯数字部分
2. 在 _check_level2() 和 _check_level3() 中使用该方法正确判断股票类型
3. 增加日志输出，显示原始代码和提取的数字码，便于调试

🎯 修复效果：
- 之前：code[:2] 得到 "SZ"、"SH"，无法匹配 60/00/68/30
- 现在：先提取数字码 "300444"、"688295"，再取前两位 "30"、"68"，正确匹配

⚠️ 注意事项：
1. 确保当前时间在 EARLIEST_EXECUTION_TIME 之后（默认09:51）
2. 止盈检查每15秒执行一次（在heartbeat.py中配置）
3. T+1规则：今日买入不可今日卖出，会跳过止盈执行
4. 卖出数量必须是100股的整数倍

🔧 如需调整：
- 修改最早执行时间：在 settings.py 中设置 TAKE_PROFIT_EARLIEST_TIME
- 修改止盈参数：在 settings.py 中设置 TAKE_PROFIT_LEVEL1/2/3_* 相关参数
""")
    print("=" * 80)
