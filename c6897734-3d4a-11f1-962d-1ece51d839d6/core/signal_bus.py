# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 信号总线（事件驱动核心）
"""

import queue
import threading


class SignalBus:
    """信号总线 - 生产者-消费者模式的核心"""
    
    def __init__(self, max_size=1000):
        self.queue = queue.Queue(maxsize=max_size)
        self.consumers = []
        self.running = False
        self.dispatcher_thread = None
    
    def register_consumer(self, consumer_func):
        self.consumers.append(consumer_func)
    
    def publish(self, signal_file_path):
        try:
            self.queue.put_nowait(signal_file_path)
        except queue.Full:
            print(f"[警告] 信号队列已满，丢弃信号: {signal_file_path}")
    
    def start_dispatcher(self, log_func):
        """
        启动信号分发线程
        
        参数:
            log_func: 日志函数
        """
        self.running = True
        self.dispatcher_thread = threading.Thread(
            target=self._dispatch_loop,
            args=(log_func,),
            daemon=True,
            name="SignalDispatcher"
        )
        self.dispatcher_thread.start()
        log_func("📡 [信号总线] 分发线程已启动")
    
    def stop_dispatcher(self):
        self.running = False
        if self.dispatcher_thread:
            self.dispatcher_thread.join(timeout=5)
    
    def _dispatch_loop(self, log_func):
        while self.running:
            try:
                signal_file = self.queue.get(timeout=1)
                
                for consumer in self.consumers:
                    try:
                        consumer(signal_file)
                    except Exception as e:
                        log_func.error(f"[错误] 消费者处理信号失败: {e}")
                
                self.queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                log_func.error(f"[错误] 信号分发异常: {e}")
