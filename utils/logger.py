# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 异步日志系统（工业级）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

特性:
- 异步队列写入（非阻塞）
- 自动日志轮转
- 多线程安全
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import threading
import queue
import datetime


class AsyncLogQueue:
    """异步日志队列 - 生产者-消费者模式"""
    
    def __init__(self, max_size=10000):
        self.queue = queue.Queue(maxsize=max_size)
        self.running = False
        self.worker_thread = None
    
    def start(self, log_dir):
        """启动异步日志工作线程"""
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker,
            args=(log_dir,),
            daemon=True,
            name="AsyncLogger"
        )
        self.worker_thread.start()
    
    def stop(self):
        """停止异步日志"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def put(self, message):
        """放入日志消息（非阻塞）"""
        try:
            self.queue.put_nowait(message)
        except queue.Full:
            # 队列满时丢弃最旧的日志
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(message)
            except:
                pass
    
    def _worker(self, log_dir):
        """日志工作线程 - 从队列消费并写入文件"""
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "alphapilot.log")
        
        # 使用 RotatingFileHandler 实现日志轮转
        logger = logging.getLogger("AsyncLogger")
        logger.setLevel(logging.INFO)
        
        # 清除已有 handler
        logger.handlers.clear()
        
        # 文件处理器（每个文件最大 10MB，保留 5 个备份）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # 消费队列
        while self.running:
            try:
                # 超时等待，避免永久阻塞
                message = self.queue.get(timeout=1)
                logger.info(message)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # 即使出错也不影响主程序
                print("[日志错误] {}".format(e))


class Logger:
    """统一日志接口"""
    
    def __init__(self):
        self.async_queue = AsyncLogQueue()
        self.initialized = False
    
    def init(self, log_dir):
        """初始化异步日志系统"""
        self.async_queue.start(log_dir)
        self.initialized = True
        self.log("=" * 60)
        self.log("🚀 [日志系统] 异步日志已启动（工业级）")
        self.log("=" * 60)
    
    def log(self, message):
        """记录日志（非阻塞）"""
        if not self.initialized:
            # 未初始化时使用同步输出（仅用于启动阶段）
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("{} | {}".format(timestamp, message))
            return
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_msg = "{} | {}".format(timestamp, message)
        self.async_queue.put(formatted_msg)
    
    def shutdown(self):
        """关闭日志系统"""
        self.log("🛑 [日志系统] 正在关闭...")
        self.async_queue.stop()


# 全局单例
_logger_instance = None


def init_logger(log_dir):
    """初始化日志系统"""
    global _logger_instance
    _logger_instance = Logger()
    _logger_instance.init(log_dir)
    return _logger_instance


def get_logger():
    """获取日志实例"""
    global _logger_instance
    if _logger_instance is None:
        raise RuntimeError("日志系统未初始化，请先调用 init_logger()")
    return _logger_instance