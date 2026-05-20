# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 智能信号文件同步器
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

职责：
- 从源目录(D:\mpython\signals\processed)检测最新信号文件
- 复制到目标目录(D:\main_data\signals)触发策略执行
- 防止重复同步同一文件
- 支持定时轮询和手动触发两种模式

使用场景：
- 在掘金仿真账户中测试不同策略参数
- 无需重复构造邮件信号,复用历史数据
- 多账户并行运行,各自独立同步
"""

import os
import shutil
import json
import time
import glob
from datetime import datetime


class SignalFileSyncer:
    """智能信号文件同步器"""
    
    def __init__(self, source_dir, target_dir, log_func=None):
        """
        参数:
            source_dir: 源目录 (D:\mpython\signals\processed)
            target_dir: 目标目录 (D:\main_data\signals)
            log_func: 日志函数(可选)
        """
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.log = log_func or print
        
        # 记录已同步的文件(防止重复)
        self.synced_files = set()
        
        # 加载历史记录
        self._load_sync_history()
        
        self.log(f"[同步器] 初始化完成")
        self.log(f"  源目录: {source_dir}")
        self.log(f"  目标目录: {target_dir}")
        self.log(f"  已同步文件数: {len(self.synced_files)}")
    
    def _load_sync_history(self):
        """加载同步历史记录"""
        history_file = os.path.join(self.target_dir, ".sync_history.json")
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.synced_files = set(data.get('synced_files', []))
                self.log(f"[同步器] 加载历史记录: {len(self.synced_files)} 个文件")
            except Exception as e:
                self.log(f"[警告] 加载同步历史失败: {e}")
                self.synced_files = set()
    
    def _save_sync_history(self):
        """保存同步历史记录"""
        history_file = os.path.join(self.target_dir, ".sync_history.json")
        
        try:
            # 只保留最近100条记录
            recent_files = list(self.synced_files)[-100:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'synced_files': recent_files,
                    'last_update': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"[警告] 保存同步历史失败: {e}")
    
    def get_latest_signal_file(self):
        """
        获取源目录中最新的信号文件(按文件名中的时间戳排序)
        
        返回:
            str: 最新文件的完整路径,如果没有则返回 None
        """
        if not os.path.exists(self.source_dir):
            self.log(f"[警告] 源目录不存在: {self.source_dir}")
            return None
        
        # 查找所有 .txt 文件
        txt_files = glob.glob(os.path.join(self.source_dir, "*.txt"))
        
        if not txt_files:
            return None
        
        # 过滤掉隐藏文件和历史记录
        txt_files = [f for f in txt_files if not os.path.basename(f).startswith('.')]
        
        if not txt_files:
            return None
        
        # 方法1: 按文件名中的时间戳排序(推荐)
        # 文件名格式: signal_batch_20260424_095753_864066.txt
        def extract_timestamp(filename):
            basename = os.path.basename(filename)
            # 提取日期时间部分: 20260424_095753
            parts = basename.split('_')
            
            # 【修复】根据实际文件名格式调整索引
            # signal_batch_20260424_095753_864066.txt
            #   parts[0] = "signal"
            #   parts[1] = "batch"  
            #   parts[2] = "20260424"  ← 日期
            #   parts[3] = "095753"    ← 时间
            #   parts[4] = "864066.txt"
            
            if len(parts) >= 4:
                try:
                    date_str = parts[2]  # 20260424
                    time_str = parts[3]  # 095753
                    
                    # 验证是否为有效的日期时间格式
                    if len(date_str) == 8 and len(time_str) == 6 and date_str.isdigit() and time_str.isdigit():
                        return f"{date_str}_{time_str}"
                except:
                    pass
            
            # 降级: 使用文件修改时间
            return str(os.path.getmtime(filename))
        
        # 按时间戳降序排序,取最新的
        latest_file = max(txt_files, key=extract_timestamp)
        
        return latest_file
    
    def sync_latest_file(self, force=False):
        """
        同步最新的信号文件到目标目录
        
        参数:
            force: 是否强制同步(忽略历史记录)
        
        返回:
            bool: 是否成功同步
        """
        latest_file = self.get_latest_signal_file()
        
        if not latest_file:
            self.log("[同步器] 未找到新的信号文件")
            return False
        
        filename = os.path.basename(latest_file)
        
        # 检查是否已同步过
        if not force and filename in self.synced_files:
            self.log(f"[同步器] 文件已同步过,跳过: {filename}")
            return False
        
        try:
            # 复制到目标目录
            target_path = os.path.join(self.target_dir, filename)
            
            # 如果目标文件已存在,先删除
            if os.path.exists(target_path):
                os.remove(target_path)
            
            shutil.copy2(latest_file, target_path)
            
            # 记录已同步
            self.synced_files.add(filename)
            self._save_sync_history()
            
            file_mtime = datetime.fromtimestamp(os.path.getmtime(latest_file))
            self.log(f"[同步器] ✅ 同步成功: {filename}")
            self.log(f"  修改时间: {file_mtime}")
            self.log(f"  目标路径: {target_path}")
            
            return True
            
        except Exception as e:
            self.log(f"[同步器] ❌ 同步失败: {e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    def sync_all_new_files(self):
        """
        同步所有未处理的新文件
        
        返回:
            int: 成功同步的文件数量
        """
        if not os.path.exists(self.source_dir):
            return 0
        
        txt_files = glob.glob(os.path.join(self.source_dir, "*.txt"))
        txt_files = [f for f in txt_files if not os.path.basename(f).startswith('.')]
        
        if not txt_files:
            return 0
        
        # 按时间戳排序
        def extract_timestamp(filename):
            basename = os.path.basename(filename)
            parts = basename.split('_')
            if len(parts) >= 3:
                try:
                    date_str = parts[1]
                    time_str = parts[2]
                    return f"{date_str}_{time_str}"
                except:
                    pass
            return str(os.path.getmtime(filename))
        
        sorted_files = sorted(txt_files, key=extract_timestamp)
        
        synced_count = 0
        for file_path in sorted_files:
            filename = os.path.basename(file_path)
            
            if filename in self.synced_files:
                continue
            
            if self.sync_latest_file(force=True):
                synced_count += 1
        
        self.log(f"[同步器] 批量同步完成: {synced_count}/{len(sorted_files)} 个文件")
        return synced_count
    
    def start_auto_sync(self, interval_seconds=30):
        """
        启动自动同步(后台线程)
        
        参数:
            interval_seconds: 检查间隔(秒)
        """
        import threading
        
        def sync_loop():
            self.log(f"[同步器] 启动自动同步 (间隔: {interval_seconds}秒)")
            
            while True:
                try:
                    self.sync_latest_file()
                except Exception as e:
                    self.log(f"[同步器] 自动同步异常: {e}")
                
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()
        
        self.log("[同步器] 自动同步线程已启动")


# ==================== 使用示例 ====================

if __name__ == '__main__':
    """
    独立测试脚本
    """
    # 配置路径
    SOURCE_DIR = r"D:\mpython\signals\processed"
    TARGET_DIR = r"D:\main_data\signals"
    
    # 创建同步器
    syncer = SignalFileSyncer(SOURCE_DIR, TARGET_DIR)
    
    # 方式1: 手动同步最新文件
    print("\n=== 方式1: 手动同步最新文件 ===")
    success = syncer.sync_latest_file()
    
    if success:
        print("✅ 同步成功!")
    else:
        print("❌ 同步失败或无新文件")
    
    # 方式2: 批量同步所有新文件
    print("\n=== 方式2: 批量同步所有新文件 ===")
    count = syncer.sync_all_new_files()
    print(f"同步了 {count} 个文件")
    
    # 方式3: 启动自动同步(每30秒检查一次)
    print("\n=== 方式3: 启动自动同步 ===")
    print("按 Ctrl+C 停止...")
    try:
        syncer.start_auto_sync(interval_seconds=30)
        
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[同步器] 已停止")
