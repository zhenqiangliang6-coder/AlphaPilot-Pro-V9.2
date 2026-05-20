# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 信号同步器快速测试脚本
Alphapilot智能体团队

用途：
- 独立测试信号同步功能,无需启动完整策略
- 验证源目录到目标目录的文件复制
- 检查防重复同步机制

使用方法：
    python test_signal_sync.py
"""

import os
import sys

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from utils.signal_syncer import SignalFileSyncer


def main():
    """主测试函数"""
    
    print("=" * 70)
    print("🧪 AlphaPilot Pro - 信号同步器测试")
    print("=" * 70)
    
    # 配置路径
    SOURCE_DIR = r"D:\mpython\signals\processed"
    TARGET_DIR = r"D:\main_data\signals"
    
    print(f"\n[配置] 源目录: {SOURCE_DIR}")
    print(f"[配置] 目标目录: {TARGET_DIR}")
    
    # 检查源目录
    if not os.path.exists(SOURCE_DIR):
        print(f"\n❌ [错误] 源目录不存在: {SOURCE_DIR}")
        return
    
    # 列出源目录中的文件
    import glob
    txt_files = glob.glob(os.path.join(SOURCE_DIR, "*.txt"))
    txt_files = [f for f in txt_files if not os.path.basename(f).startswith('.')]
    
    if not txt_files:
        print(f"\n⚠️  [警告] 源目录中没有找到信号文件")
        return
    
    print(f"\n📁 源目录中找到 {len(txt_files)} 个信号文件:")
    for i, f in enumerate(sorted(txt_files, reverse=True)[:5], 1):
        basename = os.path.basename(f)
        mtime = os.path.getmtime(f)
        from datetime import datetime
        time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"   {i}. {basename} (修改时间: {time_str})")
    
    # 创建同步器
    print("\n" + "=" * 70)
    print("🔄 初始化信号同步器...")
    print("=" * 70)
    
    syncer = SignalFileSyncer(SOURCE_DIR, TARGET_DIR, log_func=print)
    
    # 测试1: 查看最新文件
    print("\n" + "=" * 70)
    print("📋 测试1: 检测最新信号文件")
    print("=" * 70)
    
    latest = syncer.get_latest_signal_file()
    if latest:
        print(f"✅ 最新文件: {os.path.basename(latest)}")
        print(f"   完整路径: {latest}")
    else:
        print("❌ 未检测到最新文件")
        return
    
    # 测试2: 手动同步一次
    print("\n" + "=" * 70)
    print("🚀 测试2: 手动同步最新文件")
    print("=" * 70)
    
    success = syncer.sync_latest_file(force=False)
    
    if success:
        print("✅ 同步成功!")
        
        # 验证目标文件是否存在
        target_path = os.path.join(TARGET_DIR, os.path.basename(latest))
        if os.path.exists(target_path):
            print(f"✅ 目标文件已创建: {target_path}")
            print(f"   文件大小: {os.path.getsize(target_path)} bytes")
        else:
            print("❌ 目标文件未找到!")
    else:
        print("ℹ️  文件已同步过或无新文件")
    
    # 测试3: 尝试再次同步(应该被跳过)
    print("\n" + "=" * 70)
    print("🔁 测试3: 尝试重复同步(应被防重复机制拦截)")
    print("=" * 70)
    
    success2 = syncer.sync_latest_file(force=False)
    
    if not success2:
        print("✅ 防重复机制正常工作!")
    else:
        print("⚠️  警告: 防重复机制可能失效")
    
    # 测试4: 强制重新同步
    print("\n" + "=" * 70)
    print("💪 测试4: 强制重新同步(force=True)")
    print("=" * 70)
    
    success3 = syncer.sync_latest_file(force=True)
    
    if success3:
        print("✅ 强制同步成功!")
    else:
        print("❌ 强制同步失败")
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"✅ 同步器初始化: 成功")
    print(f"✅ 文件检测: 成功")
    print(f"✅ 文件同步: {'成功' if success else '跳过'}")
    print(f"✅ 防重复机制: {'正常' if not success2 else '异常'}")
    print(f"✅ 强制同步: {'成功' if success3 else '失败'}")
    print(f"\n💡 提示: 现在可以启动 main.py,watchdog 会自动处理同步过来的文件")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[测试] 用户中断")
    except Exception as e:
        print(f"\n❌ [错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()