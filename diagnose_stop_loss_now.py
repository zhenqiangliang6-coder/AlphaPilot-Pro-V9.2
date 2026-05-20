# -*- coding: utf-8 -*-
"""
止损模块诊断脚本 - 验证止损是否真正执行
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558
"""

import os
import sys
from datetime import datetime

print("=" * 80)
print("🔍 止损模块诊断")
print("=" * 80)
print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 1. 检查日志文件
log_dir = os.path.join(os.path.dirname(__file__), "logs")
if os.path.exists(log_dir):
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.txt') or f.endswith('.log')]
    if log_files:
        latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
        log_path = os.path.join(log_dir, latest_log)
        
        print(f"\n【1】检查最新日志: {latest_log}")
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计止损相关日志
            stop_loss_check_count = content.count("[止损检查]")
            stop_loss_skip_count = content.count("[止损跳过]")
            stop_loss_analysis_count = content.count("[止损分析]")
            stop_loss_monitor_count = content.count("[止损-监控]")
            stop_loss_level1_count = content.count("[止损-一级]")
            stop_loss_level2_count = content.count("[止损-二级]")
            stop_loss_execute_count = content.count("[止损执行]")
            stop_loss_summary_count = content.count("[止损总结]")
            
            print(f"   ✅ [止损检查] 出现次数: {stop_loss_check_count}")
            print(f"   ⚠️  [止损跳过] 出现次数: {stop_loss_skip_count}")
            print(f"   📊 [止损分析] 出现次数: {stop_loss_analysis_count}")
            print(f"   👁️  [止损-监控] 出现次数: {stop_loss_monitor_count}")
            print(f"   🔴 [止损-一级] 出现次数: {stop_loss_level1_count}")
            print(f"   🔴 [止损-二级] 出现次数: {stop_loss_level2_count}")
            print(f"   💰 [止损执行] 出现次数: {stop_loss_execute_count}")
            print(f"   📋 [止损总结] 出现次数: {stop_loss_summary_count}")
            
            if stop_loss_check_count == 0:
                print("\n   ❌ 问题确认: 止损模块完全没有执行！")
                print("   可能原因:")
                print("   1. 日志时间戳延迟（异步日志特性）")
                print("   2. 止损模块未被心跳线程调用")
                print("   3. 止损检查频率过低（当前为15秒）")
            else:
                print(f"\n   ✅ 止损模块已执行 {stop_loss_check_count} 次")
                
                # 显示最近的止损日志
                lines = content.split('\n')
                stop_loss_lines = [line for line in lines if '[止损' in line]
                
                if stop_loss_lines:
                    print("\n   最近的止损日志（最后10条）:")
                    for line in stop_loss_lines[-10:]:
                        print(f"   {line.strip()}")
        
        except Exception as e:
            print(f"   ❌ 读取日志失败: {e}")
    else:
        print("\n   ⚠️  日志目录为空")
else:
    print("\n   ❌ logs 目录不存在")

print("\n" + "=" * 80)
print("💡 建议:")
print("=" * 80)
print("""
1. 如果 [止损检查] 次数为 0:
   - 等待更长时间（日志可能有延迟）
   - 检查心跳模块是否正确注册了止损实例
   
2. 如果 [止损检查] > 0 但没有 [止损分析]:
   - 可能是无持仓
   - 或时间不在窗口内（10:45-14:50）
   
3. 如果 [止损分析] > 0 但没有 [止损-一级/二级]:
   - 检查持仓亏损是否达到阈值
   - 当前配置: -0.5%监控 / -1.2%一级 / -2.5%二级
   
4. 如果 [止损-一级/二级] > 0 但没有 [止损执行]:
   - 可能是无可用持仓
   - 或下单失败
""")

print("=" * 80)
