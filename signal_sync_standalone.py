# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 信号同步器独立运行脚本(纯本地版)
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

用途：
- 独立运行,无需掘金环境
- 自动从源目录同步最新信号文件到目标目录
- 支持手动触发和自动同步两种模式
- 配合 main.py 使用,实现跨目录信号测试

使用方法：
方式1: 直接运行(推荐)
    python signal_sync_standalone.py

方式2: 使用一键启动脚本
    start_with_sync.bat

配置说明：
- SOURCE_DIR: 源目录路径(默认 D:\mpython\signals\processed)
- TARGET_DIR: 目标目录路径(默认 D:\main_data\signals)
- SYNC_INTERVAL: 同步检查间隔(默认30秒)
"""

import os
import sys
import time

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from utils.signal_syncer import SignalFileSyncer


def main():
    """主函数 - 独立运行模式"""
    
    # ==================== 配置区 ====================
    # ⚠️ 可根据需要修改路径
    SOURCE_DIR = r"D:\mpython\signals\processed"   # 源目录(邮件信号归档)
    TARGET_DIR = r"D:\main_data\signals"            # 目标目录(策略监听)
    
    # 自动同步间隔(秒)
    SYNC_INTERVAL = 30
    
    # 启动时是否立即同步
    SYNC_ON_STARTUP = True
    # ================================================
    
    print("=" * 70)
    print("🔄 AlphaPilot Pro - 信号文件同步器(独立运行模式)")
    print("=" * 70)
    print(f"[配置] 源目录: {SOURCE_DIR}")
    print(f"[配置] 目标目录: {TARGET_DIR}")
    print(f"[配置] 同步间隔: {SYNC_INTERVAL}秒")
    print(f"[配置] 启动同步: {'是' if SYNC_ON_STARTUP else '否'}")
    print("=" * 70)
    
    # 检查源目录
    if not os.path.exists(SOURCE_DIR):
        print(f"\n❌ [错误] 源目录不存在: {SOURCE_DIR}")
        print("   请确认路径是否正确,或放入信号文件后再运行")
        input("\n按回车键退出...")
        return
    
    # 创建同步器
    syncer = SignalFileSyncer(SOURCE_DIR, TARGET_DIR, log_func=print)
    
    # 启动时同步一次
    if SYNC_ON_STARTUP:
        print("\n🚀 [启动同步] 同步最新信号文件...")
        success = syncer.sync_latest_file()
        
        if success:
            print("✅ 启动同步成功!")
        else:
            print("ℹ️  无新文件或同步失败(可能已同步过)")
    
    # 启动自动同步
    print(f"\n⏰ [自动同步] 每 {SYNC_INTERVAL} 秒检查一次...")
    syncer.start_auto_sync(interval_seconds=SYNC_INTERVAL)
    
    print("\n💡 [提示] 同步器已在后台运行")
    print("   - 检测到新文件会自动复制到目标目录")
    print("   - 已同步的文件不会重复处理")
    print("   - 保持此窗口开启,按 Ctrl+C 停止\n")
    print("=" * 70)
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[同步器] 用户中断,正在停止...")
        print("✅ 同步器已停止")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ [错误] 同步器运行失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")