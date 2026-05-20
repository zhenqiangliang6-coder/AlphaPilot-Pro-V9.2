# -*- coding: utf-8 -*-
"""
全面检查止损/止盈模块的字段名兼容性
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

检查项:
1. 止损模块: cost_price, open_price, avg_price
2. 止盈模块: cost_price, open_price, avg_price
3. 交易引擎: 持仓字段映射
4. 所有策略模块: 持仓相关字段访问
"""

import os
import sys
import re

print("=" * 80)
print("🔍 全面检查止损/止盈模块字段名兼容性")
print("=" * 80)

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 需要检查的文件
files_to_check = [
    "risk/stop_loss.py",
    "risk/dynamic_take_profit.py",
    "core/trader_engine.py",
    "strategies/signal_strategy.py",
    "strategies/delayed_strategy.py",
    "strategies/rocket_boost.py",
    "strategies/auction_strategy.py",
]

# 检查项
checks = {
    "open_price": "标准字段名",
    "cost_price": "掘金字段名",
    "avg_price": "备用字段名",
    "getattr.*open_price": "动态获取open_price",
    "getattr.*cost_price": "动态获取cost_price",
    "getattr.*avg_price": "动态获取avg_price",
    "pos\\.open_price": "直接访问open_price",
    "pos\\.cost_price": "直接访问cost_price",
    "pos\\.avg_price": "直接访问avg_price",
}

print("\n📋 开始检查...\n")

for file_path in files_to_check:
    full_path = os.path.join(project_root, file_path)
    
    if not os.path.exists(full_path):
        print(f"⚠️  文件不存在: {file_path}")
        continue
    
    print(f"\n📄 {file_path}")
    print("-" * 80)
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 检查每个字段的使用情况
    for pattern, description in checks.items():
        matches = []
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                matches.append((i, line.strip()))
        
        if matches:
            print(f"\n  ✅ 找到 {description} ({pattern}): {len(matches)} 处")
            for line_num, line_content in matches[:3]:  # 只显示前3个
                print(f"     第 {line_num} 行: {line_content[:80]}")
            if len(matches) > 3:
                print(f"     ... 还有 {len(matches) - 3} 处")

print("\n" + "=" * 80)
print("🎯 检查完成")
print("=" * 80)
print("\n💡 建议:")
print("1. 如果所有模块都只使用 pos.open_price，需要添加 cost_price 兼容")
print("2. 优先使用 getattr() 动态获取，避免 AttributeError")
print("3. 确保所有字段访问都有默认值（如 0.0）")
print("\n" + "=" * 80)