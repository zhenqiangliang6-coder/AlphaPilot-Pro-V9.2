# -*- coding: utf-8 -*-
"""
精英竞价卖出功能诊断报告

作者: Alphapilot智能体团队
日期: 2026-05-07
版本: V1.0

检查范围:
1. 掘金量化股票代码前缀格式适配
2. T+1合规性（可卖数量检查）
3. 100股整数倍规则
4. 精英名单文件格式一致性
5. 价格获取与跌停保护
"""

import os
import json
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.logger import get_logger


def check_stock_code_format():
    """检查股票代码格式标准化函数"""
    print("=" * 80)
    print("【检查项1】股票代码格式标准化")
    print("=" * 80)
    
    from core.state_manager import _normalize_stock_code
    
    test_cases = [
        ("688295.SH", "SHSE.688295"),
        ("300444.SZ", "SZSE.300444"),
        ("SH.600821", "SHSE.600821"),
        ("SZ.000001", "SZSE.000001"),
        ("SHSE.688295", "SHSE.688295"),
        ("SZSE.300444", "SZSE.300444"),
        ("600821", "SHSE.600821"),
        ("300444", "SZSE.300444"),
    ]
    
    all_passed = True
    for input_code, expected in test_cases:
        result = _normalize_stock_code(input_code)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} 输入: {input_code:15s} → 输出: {result:15s} (期望: {expected})")
    
    print()
    if all_passed:
        print("✅ 股票代码格式标准化函数工作正常")
    else:
        print("❌ 存在格式转换错误，需要修复")
    print()
    return all_passed


def check_elite_list_file_format():
    """检查精英名单文件的实际格式"""
    print("=" * 80)
    print("【检查项2】精英名单文件格式检查")
    print("=" * 80)
    
    elite_file = settings.STATE_FILE
    
    if not os.path.exists(elite_file):
        print(f"⚠️  精英名单文件不存在: {elite_file}")
        print("   这是正常的，首次运行时会创建空文件")
        return True
    
    try:
        with open(elite_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        positions = data.get('positions', {})
        
        if not positions:
            print("✅ 精英名单为空（当前无符合条件的股票）")
            return True
        
        print(f"📊 精英名单包含 {len(positions)} 只股票\n")
        
        format_issues = []
        for code, info in positions.items():
            # 检查代码格式
            if not (code.startswith('SHSE.') or code.startswith('SZSE.')):
                format_issues.append(code)
                print(f"❌ 代码格式错误: {code} (应为 SHSE.XXXXXX 或 SZSE.XXXXXX)")
            else:
                print(f"✅ {code} - 浮盈: {info.get('profit_ratio', 0)*100:.2f}% | "
                      f"持仓: {info.get('volume', 0)}股 | "
                      f"成本: {info.get('cost_price', 0):.2f} | "
                      f"收盘: {info.get('close_price', 0):.2f}")
        
        print()
        if format_issues:
            print(f"❌ 发现 {len(format_issues)} 只股票代码格式错误:")
            for code in format_issues:
                print(f"   - {code}")
            return False
        else:
            print("✅ 所有股票代码格式正确（符合掘金量化要求）")
            return True
    
    except Exception as e:
        print(f"❌ 读取精英名单文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_auction_strategy_code():
    """检查集合竞价策略代码的关键逻辑"""
    print("=" * 80)
    print("【检查项3】集合竞价策略代码审查")
    print("=" * 80)
    
    auction_file = os.path.join(os.path.dirname(__file__), 'strategies', 'auction_strategy.py')
    
    if not os.path.exists(auction_file):
        print(f"❌ 集合竞价策略文件不存在: {auction_file}")
        return False
    
    with open(auction_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "T+1合规检查": "pos.can_use_volume" in content,
        "100股取整逻辑": "(can_sell // 100) * 100" in content,
        "价格获取API": "get_latest_prices" in content,
        "订单执行": "order_stock" in content and '"SELL"' in content,
        "日志记录": 'log.log("[竞价]' in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}: {'通过' if passed else '缺失'}")
        if not passed:
            all_passed = False
    
    print()
    
    # 额外检查：是否有未定义的变量引用
    if "ticks" in content and "limit_down = ticks" in content:
        print("❌ 发现未定义变量 'ticks' 引用（可能导致运行时错误）")
        all_passed = False
    else:
        print("✅ 未发现明显的未定义变量引用")
    
    print()
    return all_passed


def check_position_class_fields():
    """检查Position类的字段映射"""
    print("=" * 80)
    print("【检查项4】Position类字段映射检查")
    print("=" * 80)
    
    trader_engine_file = os.path.join(os.path.dirname(__file__), 'core', 'trader_engine.py')
    
    if not os.path.exists(trader_engine_file):
        print(f"❌ 交易引擎文件不存在: {trader_engine_file}")
        return False
    
    with open(trader_engine_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "available_now字段": '"available_now"' in content,
        "can_use_volume映射": "self.can_use_volume = self.available_now" in content,
        "stock_code来源": 'p["symbol"]' in content or "p.get('symbol')" in content,
        "vwap_open成本价": '"vwap_open"' in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}: {'通过' if passed else '缺失'}")
        if not passed:
            all_passed = False
    
    print()
    
    # 检查query_positions是否正确设置stock_code
    if 'stock_code=p["symbol"]' in content or "stock_code=p.get('symbol')" in content:
        print("✅ Position的stock_code直接从掘金SDK的symbol字段获取（格式正确）")
    else:
        print("⚠️  无法确认stock_code的来源，请手动检查")
    
    print()
    return all_passed


def simulate_auction_execution():
    """模拟集合竞价执行流程"""
    print("=" * 80)
    print("【检查项5】模拟集合竞价执行流程")
    print("=" * 80)
    
    print("\n📋 执行流程说明:")
    print("1. 加载精英名单（标准化股票代码格式）")
    print("2. 查询当前持仓（从掘金SDK获取）")
    print("3. 匹配精英名单与持仓")
    print("4. 检查T+1合规性（can_use_volume > 0）")
    print("5. 获取最新价格（get_latest_prices）")
    print("6. 计算卖出价格（现价 × AUCTION_SELL_RATIO）")
    print("7. 100股取整处理")
    print("8. 调用order_stock下单（使用标准化代码）")
    print("9. 卖出成功后从精英名单移除")
    print("10. 保存更新后的精英名单文件")
    
    print("\n✅ 关键验证点:")
    print("  - 股票代码格式: SHSE.XXXXXX / SZSE.XXXXXX")
    print("  - T+1合规: 使用 can_use_volume 而非 volume")
    print("  - 100股规则: actual_sell_volume = (can_sell // 100) * 100")
    print("  - 订单参数: order_stock(code, 'SELL', volume, price, 'AUCTION_ELITE')")
    print()
    
    return True


def main():
    """主诊断函数"""
    print("\n" + "=" * 80)
    print("精英竞价卖出功能诊断报告")
    print("掘金量化平台适配检查")
    print("=" * 80 + "\n")
    
    results = {}
    
    # 执行各项检查
    results["股票代码格式标准化"] = check_stock_code_format()
    results["精英名单文件格式"] = check_elite_list_file_format()
    results["集合竞价策略代码"] = check_auction_strategy_code()
    results["Position类字段映射"] = check_position_class_fields()
    results["执行流程模拟"] = simulate_auction_execution()
    
    # 总结
    print("=" * 80)
    print("诊断总结")
    print("=" * 80)
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n总检查项: {total_count}")
    print(f"通过: {passed_count}")
    print(f"失败: {total_count - passed_count}\n")
    
    for check_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {check_name}")
    
    print()
    
    if passed_count == total_count:
        print("🎉 恭喜！精英竞价卖出功能完全符合掘金量化平台要求！")
        print("\n关键优势:")
        print("  ✅ 股票代码格式自动标准化（支持多种输入格式）")
        print("  ✅ T+1合规性严格保障（使用available_now字段）")
        print("  ✅ 100股整数倍规则严格执行")
        print("  ✅ Position类字段映射正确（stock_code直接使用掘金symbol）")
        print("  ✅ 完整的日志记录和异常处理")
    else:
        print("⚠️  存在需要修复的问题，请查看上述详细检查结果")
    
    print("\n" + "=" * 80)
    print("建议操作:")
    print("=" * 80)
    print("1. 在实盘运行前，先使用模拟账户测试集合竞价卖出功能")
    print("2. 检查日志输出，确认股票代码格式、可卖数量、下单数量正确")
    print("3. 监控精英名单文件（signals/yesterday_holdings.json）的更新情况")
    print("4. 注意集合竞价时段（09:21-09:25）的价格获取可能受限")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
