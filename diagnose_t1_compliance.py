# -*- coding: utf-8 -*-
"""
T+1交易约束诊断脚本

功能说明：
1. 检查所有卖出逻辑是否正确使用了 can_use_volume（可卖数量）
2. 验证止损、止盈、竞价策略是否符合A股T+1制度
3. 输出详细的检查结果和修改建议

作者: Alphapilot智能体团队
成员: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558
"""
import os
import re


def check_file_for_t1_compliance(file_path, file_name):
    """检查单个文件是否符合T+1约束"""
    print(f"\n{'='*60}")
    print(f"检查文件: {file_name}")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    issues = []
    passed = []
    
    # 检查1: 是否使用了 volume 而非 can_use_volume 进行卖出
    # 查找 order_stock 或 _execute_sell 调用前的 volume 使用
    sell_patterns = [
        (r'order_stock.*volume', 'order_stock调用'),
        (r'_execute_sell.*volume', '_execute_sell调用'),
    ]
    
    for pattern, desc in sell_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            # 检查附近是否有 can_use_volume 的使用
            context_start = max(0, match.start() - 500)
            context_end = min(len(content), match.end() + 100)
            context = content[context_start:context_end]
            
            if 'can_use_volume' not in context and 'can_sell' not in context:
                issues.append(f"⚠️  第{line_num}行: {desc}可能未使用can_use_volume")
            else:
                passed.append(f"✅ 第{line_num}行: {desc}已正确使用可卖数量")
    
    # 检查2: 是否有明确的T+1相关注释
    if 'T+1' in content or '今日买入不可卖' in content or '可卖数量' in content:
        passed.append("✅ 包含T+1约束相关注释")
    else:
        issues.append("⚠️  缺少T+1约束相关注释")
    
    # 检查3: 是否有 can_use_volume 的查询逻辑
    if 'can_use_volume' in content or 'can_sell' in content:
        passed.append("✅ 使用了can_use_volume或can_sell变量")
    else:
        issues.append("❌ 未检测到can_use_volume或can_sell的使用")
    
    # 输出结果
    print(f"\n通过的检查 ({len(passed)}):")
    for p in passed:
        print(f"  {p}")
    
    if issues:
        print(f"\n发现的问题 ({len(issues)}):")
        for i in issues:
            print(f"  {i}")
    else:
        print(f"\n🎉 未发现明显问题！")
    
    return len(issues) == 0


def main():
    """主函数"""
    print("="*60)
    print("AlphaPilot Pro V9.1 - T+1交易约束诊断工具")
    print("作者: Alphapilot智能体团队")
    print("="*60)
    
    # 需要检查的文件列表
    files_to_check = [
        ("d:\\main_data\\risk\\stop_loss.py", "止损模块"),
        ("d:\\main_data\\risk\\dynamic_take_profit.py", "动态止盈模块"),
        ("d:\\main_data\\strategies\\auction_strategy.py", "集合竞价策略"),
        ("d:\\main_data\\core\\trader_engine.py", "交易引擎"),
    ]
    
    results = {}
    
    for file_path, file_name in files_to_check:
        if os.path.exists(file_path):
            is_compliant = check_file_for_t1_compliance(file_path, file_name)
            results[file_name] = is_compliant
        else:
            print(f"\n❌ 文件不存在: {file_path}")
            results[file_name] = False
    
    # 总结
    print(f"\n{'='*60}")
    print("诊断总结")
    print(f"{'='*60}")
    
    compliant_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n总文件数: {total_count}")
    print(f"符合T+1约束: {compliant_count}")
    print(f"需要修复: {total_count - compliant_count}")
    
    if compliant_count == total_count:
        print("\n🎉 恭喜！所有文件都符合A股T+1交易制度约束！")
    else:
        print("\n⚠️  以下文件需要进一步检查:")
        for file_name, is_compliant in results.items():
            if not is_compliant:
                print(f"  - {file_name}")
    
    print("\n" + "="*60)
    print("关键要点提醒:")
    print("="*60)
    print("1. 所有卖出操作必须基于 can_use_volume（可卖数量）")
    print("2. volume 是总持仓，包含今日买入不可卖部分")
    print("3. can_use_volume 是昨日及之前买入的可卖部分")
    print("4. 日志必须明确显示'总持仓'和'可卖数量'")
    print("="*60)


if __name__ == "__main__":
    main()
