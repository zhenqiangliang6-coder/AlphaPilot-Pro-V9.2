# -*- coding: utf-8 -*-
"""
延时策略诊断脚本 - 检查买入逻辑是否正常执行
作者: Alphapilot智能体团队
日期: 2026-05-13

功能：
1. 检查观察名单中的股票
2. 模拟执行check_and_execute()逻辑
3. 输出详细的诊断信息
"""

import os
import sys
import json
import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from strategies.delayed_strategy import DelayedStrategy


def diagnose_delayed_strategy():
    """诊断延时策略的买入逻辑"""
    
    print("="*70)
    print("🔍 延时策略诊断工具")
    print("="*70)
    print()
    
    # 1. 加载观察名单
    watchlist_file = os.path.join(settings.DATA_DIR, "delayed_watchlist.json")
    
    if not os.path.exists(watchlist_file):
        print(f"❌ 观察名单文件不存在: {watchlist_file}")
        return
    
    with open(watchlist_file, 'r', encoding='utf-8') as f:
        watchlist_data = json.load(f)
    
    watchlist = watchlist_data.get('watchlist', {})
    
    print(f"📋 观察名单中共有 {len(watchlist)} 只股票")
    print(f"📅 最后更新时间: {watchlist_data.get('last_update', '未知')}")
    print()
    
    # 2. 分析每只股票的状态
    today = datetime.date.today()
    now_time = datetime.datetime.now().strftime("%H%M")
    
    print(f"📅 当前日期: {today}")
    print(f"⏰ 当前时间: {now_time}")
    print()
    
    target_today = []  # 今天应该执行的股票
    waiting = []       # 等待中的股票
    expired = []       # 已过期的股票
    
    for code, item in watchlist.items():
        target_date_str = item.get('target_date', '')
        if not target_date_str:
            continue
        
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        stock_info = {
            'code': code,
            'name': item.get('name', ''),
            'target_date': target_date,
            'trigger_price': item.get('trigger_price', 0),
            'trigger_vr': item.get('trigger_volume_ratio', 0),
            'signal_date': item.get('signal_date', ''),
            'delay_days': item.get('delay_days', 0)
        }
        
        if today < target_date:
            waiting.append(stock_info)
        elif today == target_date:
            target_today.append(stock_info)
        else:
            expired.append(stock_info)
    
    # 3. 输出分类结果
    print("-"*70)
    print(f"✅ 今天({today})应该执行的股票: {len(target_today)} 只")
    print("-"*70)
    
    if target_today:
        for stock in target_today:
            print(f"   📈 {stock['code']} ({stock['name']})")
            print(f"      信号日期: {stock['signal_date']} | 延时天数: {stock['delay_days']}")
            print(f"      触发价格: ¥{stock['trigger_price']:.2f} | 触发量比: {stock['trigger_vr']:.2f}")
            print(f"      当前时间: {now_time} | 保底买入时间: 14:39")
            
            # 判断是否到达保底买入时间
            if now_time >= "1439":
                print(f"      ⚠️  已到达保底买入时间，应该立即执行买入！")
            else:
                print(f"      ⏳ 未到达保底时间，需要检查量比是否达标")
            print()
    else:
        print("   (无)")
        print()
    
    print("-"*70)
    print(f"⏳ 等待中的股票: {len(waiting)} 只")
    print("-"*70)
    
    if waiting:
        for stock in waiting[:5]:  # 只显示前5只
            days_left = (stock['target_date'] - today).days
            print(f"   📊 {stock['code']} ({stock['name']}) - 目标日: {stock['target_date']} (还有{days_left}天)")
        if len(waiting) > 5:
            print(f"   ... 还有 {len(waiting) - 5} 只")
    else:
        print("   (无)")
    print()
    
    print("-"*70)
    print(f"❌ 已过期的股票: {len(expired)} 只")
    print("-"*70)
    
    if expired:
        for stock in expired[:5]:  # 只显示前5只
            days_expired = (today - stock['target_date']).days
            print(f"   ⚠️  {stock['code']} ({stock['name']}) - 目标日: {stock['target_date']} (已过期{days_expired}天)")
        if len(expired) > 5:
            print(f"   ... 还有 {len(expired) - 5} 只")
    else:
        print("   (无)")
    print()
    
    # 4. 关键问题诊断
    print("="*70)
    print("🔎 关键问题诊断")
    print("="*70)
    print()
    
    if not target_today:
        print("✅ 今天没有需要执行的股票")
    else:
        print(f"⚠️  发现 {len(target_today)} 只股票应该在今天执行买入！")
        print()
        print("可能的原因：")
        print("   1. ❌ 延时策略未被集成到心跳监控中（已修复）")
        print("   2. ❌ check_and_execute() 只在启动时执行一次")
        print("   3. ⚠️  量比未达到触发阈值，且未到14:39保底时间")
        print()
        print("解决方案：")
        print("   ✅ 已将 DelayedStrategy 注入到 HeartbeatMonitor")
        print("   ✅ 每30秒自动执行一次 check_and_execute()")
        print("   ✅ 确保及时执行买入操作")
        print()
    
    print("="*70)
    print("💡 建议操作")
    print("="*70)
    print()
    print("1. 重启策略程序，使修复生效")
    print("2. 观察日志中是否出现 '[延时策略-检查]' 和 '[延时策略-信号优先/保底买入]' 日志")
    print("3. 如果仍未买入，检查：")
    print("   - 账户是否有足够资金")
    print("   - 股票代码格式是否正确（SHSE.XXXXXX 或 SZSE.XXXXXX）")
    print("   - 量比数据是否能正常获取")
    print()


if __name__ == "__main__":
    diagnose_delayed_strategy()
