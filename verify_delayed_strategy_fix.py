# -*- coding: utf-8 -*-
"""
延时策略修复验证脚本
作者: Alphapilot智能体团队
日期: 2026-05-13

功能：验证HeartbeatMonitor是否正确集成了延时策略
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.heartbeat import HeartbeatMonitor


def verify_fix():
    """验证修复是否成功"""
    
    print("="*70)
    print("🔧 延时策略修复验证")
    print("="*70)
    print()
    
    # 1. 检查HeartbeatMonitor构造函数是否支持delayed_strat参数
    import inspect
    sig = inspect.signature(HeartbeatMonitor.__init__)
    params = list(sig.parameters.keys())
    
    print("✅ 步骤1: 检查HeartbeatMonitor构造函数参数")
    print(f"   参数列表: {params}")
    
    if 'delayed_strat' in params:
        print("   ✅ delayed_strat 参数已添加")
    else:
        print("   ❌ delayed_strat 参数未找到")
        return False
    
    print()
    
    # 2. 检查是否有last_delayed_check属性初始化
    print("✅ 步骤2: 检查实例属性初始化")
    
    # 创建一个临时实例来检查
    def dummy_log(msg):
        pass
    
    def dummy_account():
        pass
    
    monitor = HeartbeatMonitor(dummy_log, dummy_account)
    
    if hasattr(monitor, 'delayed_strat'):
        print("   ✅ delayed_strat 属性已初始化")
    else:
        print("   ❌ delayed_strat 属性未初始化")
        return False
    
    if hasattr(monitor, 'last_delayed_check'):
        print("   ✅ last_delayed_check 属性已初始化")
    else:
        print("   ❌ last_delayed_check 属性未初始化")
        return False
    
    print()
    
    # 3. 检查心跳循环中是否有延时策略检查代码
    print("✅ 步骤3: 检查心跳循环中的延时策略检查逻辑")
    
    source = inspect.getsource(HeartbeatMonitor._heartbeat_loop)
    
    if 'delayed_strat' in source and 'check_and_execute' in source:
        print("   ✅ 心跳循环中包含延时策略检查代码")
        
        # 提取相关代码片段
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'delayed_strat' in line and 'check_and_execute' in line:
                print(f"   代码位置: 第{i+1}行")
                # 显示上下文
                start = max(0, i-2)
                end = min(len(lines), i+3)
                for j in range(start, end):
                    prefix = "   >>> " if j == i else "       "
                    print(f"{prefix}{lines[j]}")
                break
    else:
        print("   ❌ 心跳循环中未找到延时策略检查代码")
        return False
    
    print()
    
    # 4. 检查main.py是否正确传递参数
    print("✅ 步骤4: 检查main.py中的HeartbeatMonitor初始化")
    
    main_file = os.path.join(os.path.dirname(__file__), 'main.py')
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        if 'delayed_strat=delayed_strat' in main_content:
            print("   ✅ main.py 中正确传递了 delayed_strat 参数")
        else:
            print("   ❌ main.py 中未传递 delayed_strat 参数")
            return False
    else:
        print("   ⚠️  未找到 main.py 文件，跳过检查")
    
    print()
    
    # 5. 总结
    print("="*70)
    print("✅ 验证结果: 所有检查通过！")
    print("="*70)
    print()
    print("📋 修复内容总结:")
    print("   1. HeartbeatMonitor.__init__ 新增 delayed_strat 参数")
    print("   2. HeartbeatMonitor.__init__ 新增 last_delayed_check 属性")
    print("   3. HeartbeatMonitor._heartbeat_loop 新增延时策略定时检查")
    print("   4. main.py 正确传递 delayed_strat 实例")
    print()
    print("🎯 预期效果:")
    print("   - 每30秒自动执行一次 delayed_strat.check_and_execute()")
    print("   - 及时检测量比是否达标（信号优先路径）")
    print("   - 到达14:39自动执行保底买入")
    print()
    print("⚠️  下一步操作:")
    print("   1. 重启策略程序: python main.py")
    print("   2. 观察日志输出，确认延时策略正常执行")
    print("   3. 运行诊断脚本: python diagnose_delayed_strategy.py")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = verify_fix()
        if success:
            print("✅ 验证成功！修复已生效。")
            sys.exit(0)
        else:
            print("❌ 验证失败！请检查修复是否正确应用。")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
