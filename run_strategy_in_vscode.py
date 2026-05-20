"""
Alphapilot Pro - 掘金策略运行脚本

Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

说明: 
本脚本用于在 VSCode 中直接运行掘金策略
前提条件:
1. 掘金量化终端已启动并连接账户
2. 已激活 quant_env 虚拟环境
3. .env 文件中配置了正确的 GM_TOKEN 和 GM_ACCOUNT_ID

运行方式:
python run_strategy_in_vscode.py
"""

import os
import sys
from dotenv import load_dotenv
from gm.api import *

# 加载环境变量
load_dotenv()

GM_TOKEN = os.getenv('GM_TOKEN')
GM_ACCOUNT_ID = os.getenv('GM_ACCOUNT_ID')

print("=" * 80)
print("🚀 Alphapilot Pro - 在 VSCode 中运行掘金策略")
print("=" * 80)

print(f"\n📋 [环境配置]")
print(f"   Python 解释器: {sys.executable}")
print(f"   GM_TOKEN: {'✅ 已设置' if GM_TOKEN else '❌ 未设置'}")
print(f"   GM_ACCOUNT_ID: {GM_ACCOUNT_ID if GM_ACCOUNT_ID else '❌ 未设置'}")
print(f"\n💡 [运行说明]")
print(f"   1. 确保掘金量化终端已启动")
print(f"   2. 确保账户已连接: {GM_ACCOUNT_ID}")
print(f"   3. 策略将自动使用终端中已连接的账户")


def init(context):
    """策略初始化"""
    print(f"\n{'='*80}")
    print(f"✅ 策略初始化成功")
    print(f"{'='*80}")
    
    # 查询账户状态
    try:
        cash = get_cash(account_id=GM_ACCOUNT_ID)
        if cash:
            print(f"\n💰 账户资金:")
            print(f"   账户ID: {cash.get('account_id', 'N/A')}")
            print(f"   可用资金: ¥{cash.get('available', 0):,.2f}")
            print(f"   总资产: ¥{cash.get('nav', 0):,.2f}")
    except Exception as e:
        print(f"\n⚠️  查询账户失败: {e}")
    
    # 测试下单
    print(f"\n🧪 [测试下单]")
    print(f"   测试标的: SHSE.688295")
    print(f"   测试数量: 100 股")
    
    try:
        result = order_volume(
            symbol='SHSE.688295',
            volume=100,
            side=OrderSide_Buy,
            order_type=OrderType_Market,
            position_effect=PositionEffect_Open
        )
        print(f"   ✅ 下单成功: {result}")
    except Exception as e:
        print(f"   ❌ 下单失败: {e}")
        print(f"\n💡 如果下单失败，可能原因:")
        print(f"   1. 掘金终端未启动或未连接账户")
        print(f"   2. 当前不在交易时段（精准撮合账户）")
        print(f"   3. Token 权限不足")
    
    print(f"\n{'='*80}")
    print(f"✅ 策略执行完成")
    print(f"{'='*80}")
    
    # 停止策略
    stop()


if __name__ == '__main__':
    # 设置 Token
    print(f"\n🔑 [Token认证]")
    try:
        set_token(GM_TOKEN)
        print(f"   ✅ Token 设置成功")
    except Exception as e:
        print(f"   ❌ Token 设置失败: {e}")
        sys.exit(1)
    
    # 运行策略
    print(f"\n🚀 [启动策略]")
    try:
        run(
            strategy_id='alphapilot_vscode_test_' + str(int(os.time.time() if hasattr(os, 'time') else 0)),
            filename='run_strategy_in_vscode.py',
            mode=MODE_LIVE,
            token=GM_TOKEN
        )
    except Exception as e:
        print(f"   ❌ 策略启动失败: {e}")
        sys.exit(1)
