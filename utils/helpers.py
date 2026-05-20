# -*- coding: utf-8 -*-
"""
工具函数 - 掘金量化版
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.0 - 基于掘金平台
"""
import os
import math
import datetime
from gm.api import *
from config import settings
from utils.logger import get_logger


def ensure_dirs():
    """确保所有必要目录存在
    
    【重要】此函数可能在日志系统初始化之前被调用，因此需要容错处理
    """
    # 【容错处理】尝试获取日志对象，如果未初始化则静默执行
    try:
        log = get_logger()
    except RuntimeError:
        log = None  # 日志系统未初始化，使用None
    
    dirs = [
        settings.DATA_DIR, 
        settings.LOG_DIR, 
        settings.SIGNAL_DIR_INPUT, 
        settings.SIGNAL_DIR_PROCESSED
    ]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d)
                if log:
                    log.log(f"[初始化] 创建目录: {d}")
            except Exception as e:
                if log:
                    log.log(f"[错误] 创建目录失败 {d}: {e}")


def is_auction_time(time_str):
    """集合竞价时间：09:20-09:25"""
    return "0921" <= time_str <= "0925"


def is_silent_time(time_str):
    """静默期：09:25-09:30（不进行交易）"""
    return "0925" < time_str < "0930"


def is_trading_time(time_str):
    """判断是否在交易时间内"""
    return ("0930" <= time_str <= "1136") or ("1300" <= time_str <= "1730")


def round_lot(volume):
    """
    将股票数量向下取整到100的整数倍（A股交易规则：1手=100股）
    
    参数:
        volume: 原始股票数量
    
    返回:
        int: 取整后的数量（100的倍数）
    
    示例:
        >>> round_lot(250)
        200
        >>> round_lot(1800)
        1800
        >>> round_lot(99)
        0
    """
    return (volume // 100) * 100


def is_after_take_profit_start(time_str):
    """
    判断是否已过动态止盈启动时间
    默认在 09:50 后开始执行，避开开盘剧烈波动
    """
    try:
        return int(time_str) >= settings.EARLIEST_EXECUTION_TIME
    except Exception:
        return False


def get_index_change_percent():
    """获取上证指数涨跌幅"""
    log = get_logger()
    
    index_code = "SHSE.000001"  # 掘金格式
    
    try:
        # 获取最新行情
        tick_data = current([index_code], fields=['symbol', 'price', 'open'])
        
        if not tick_data or len(tick_data) == 0:
            return None
        
        data = tick_data[0]
        current_price = data.get('price', 0.0)
        open_price = data.get('open', 0.0)
        
        if current_price <= 0 or open_price <= 0:
            return None
            
        change_pct = (current_price - open_price) / open_price * 100.0
        
        if not math.isfinite(change_pct):
            return None
            
        return round(change_pct, 2)
    except Exception as e:
        if log:
            log.log(f"[数据] 获取大盘指数失败: {e}")
        return None


def is_weekend(date_str):
    """
    判断日期是否为周末
    
    Args:
        date_str: 日期字符串 (YYYY-MM-DD) 或 datetime 对象
    
    Returns:
        bool: True=周末，False=交易日
    """
    try:
        if isinstance(date_str, str):
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        else:
            dt = date_str
        
        return dt.weekday() >= 5  # 5=周六，6=周日
    except Exception:
        return False


def add_trading_days(start_date, days):
    """
    计算 N 个交易日后的日期（跳过周末）
    
    Args:
        start_date: 起始日期 (datetime 或 YYYY-MM-DD 字符串)
        days: 要增加的天数
    
    Returns:
        str: 目标日期 (YYYY-MM-DD)
    """
    log = get_logger()
    
    try:
        if isinstance(start_date, str):
            dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            dt = start_date
        
        remaining_days = days
        while remaining_days > 0:
            dt += datetime.timedelta(days=1)
            if dt.weekday() < 5:  # 周一到周五
                remaining_days -= 1
        
        return dt.strftime('%Y-%m-%d')
    except Exception as e:
        if log:
            log.log(f"[工具] 计算交易日失败: {e}")
        if isinstance(start_date, str):
            dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            dt = start_date
        result = dt + datetime.timedelta(days=days)
        return result.strftime('%Y-%m-%d')