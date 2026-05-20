# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - watchdog 信号监听器（事件驱动）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

职责：
- 监控 signals/ 目录的文件创建事件
- 新文件立即通知 signal_bus
- 零扫描开销，纯事件触发

依赖: pip install watchdog
"""

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class SignalFileHandler(FileSystemEventHandler):
    """信号文件事件处理器"""
    
    def __init__(self, signal_bus, log_func):
        """
        参数:
            signal_bus: 信号总线实例
            log_func: 日志函数
        """
        super().__init__()
        self.signal_bus = signal_bus
        self.log = log_func
    
    def on_created(self, event):
        """
        文件创建事件回调
        
        参数:
            event: watchdog 事件对象
        """
        # 只处理文件，忽略目录
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # 只处理 .txt 和 .json 信号文件
        if not (file_path.endswith('.txt') or file_path.endswith('.json')):
            return
        
        # 忽略 processed 子目录
        if 'processed' in file_path:
            return
        
        # 延迟 0.5 秒确保文件写入完成
        time.sleep(0.5)
        
        # 发布到信号总线
        self.signal_bus.publish(file_path)
        self.log(f"📩 [watchdog] 检测到新信号: {os.path.basename(file_path)}")


class SignalWatcher:
    """信号文件监听器"""
    
    def __init__(self, signals_dir, signal_bus, log_func):
        """
        参数:
            signals_dir: 信号文件目录
            signal_bus: 信号总线实例
            log_func: 日志函数
        """
        self.signals_dir = signals_dir
        self.signal_bus = signal_bus
        self.log = log_func
        self.observer = None
    
    def start(self):
        """启动监听器"""
        # 确保目录存在
        os.makedirs(self.signals_dir, exist_ok=True)
        
        # 创建事件处理器
        event_handler = SignalFileHandler(self.signal_bus, self.log)
        
        # 创建观察者
        self.observer = Observer()
        self.observer.schedule(event_handler, self.signals_dir, recursive=False)
        self.observer.start()
        
        self.log(f"👁️  [watchdog] 开始监听信号目录: {self.signals_dir}")
        self.log("💡 [提示] 新信号文件将立即触发处理（零扫描开销）")
    
    def stop(self):
        """停止监听器"""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.log("🛑 [watchdog] 监听器已停止")
