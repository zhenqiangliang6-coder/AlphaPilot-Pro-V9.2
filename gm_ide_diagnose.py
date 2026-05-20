# coding=utf-8
"""
Alphapilot Pro - 掘金IDE专用账户诊断

Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

说明:
此策略必须在掘金IDE中运行，不能使用VSCode独立运行
功能: 验证掘金IDE是否能正确绑定账户上下文
"""
from __future__ import print_function, absolute_import
from gm.api import *


def init(context):
    """策略初始化 - 诊断账户绑定"""
    print("\n" + "=" * 80)
    print("🔍 Alphapilot Pro - 掘金IDE账户诊断")
    print("=" * 80)
    
    # 步骤1: 获取当前策略绑定的账户
    print("\n💰 [步骤1] 获取当前绑定账户")
    try:
        # 在策略中，使用 context.account() 获取当前账户
        account = context.account()
        if account:
            print(f"   ✅ 账户上下文绑定成功")
            print(f"   账户ID: {account.account_id}")
        else:
            print(f"   ❌ 账户上下文为空")
            print(f"   💡 请检查掘金终端中是否已连接账户")
    except Exception as e:
        print(f"   ❌ 获取账户失败: {e}")
        print(f"   💡 这可能是掘金IDE环境问题")
    
    # 步骤2: 查询资金（不指定account_id）
    print("\n💰 [步骤2] 查询资金（自动使用绑定账户）")
    try:
        cash = get_cash()  # 不传参数，使用默认账户
        if cash:
            print(f"   ✅ 资金查询成功")
            print(f"   账户ID: {cash.account_id}")
            print(f"   可用资金: ¥{cash.available:,.2f}")
            print(f"   总资产: ¥{cash.nav:,.2f}")
        else:
            print(f"   ❌ 资金查询返回空")
    except Exception as e:
        print(f"   ❌ 资金查询失败: {e}")
    
    # 步骤3: 查询持仓
    print("\n📊 [步骤3] 查询持仓")
    try:
        positions = get_position()  # 不传参数
        if positions:
            print(f"   ✅ 持仓查询成功")
            print(f"   持仓数量: {len(positions)} 只股票")
            for pos in positions[:3]:
                print(f"      - {pos.symbol}: {pos.volume} 股")
        else:
            print(f"   ℹ️  当前无持仓")
    except Exception as e:
        print(f"   ❌ 持仓查询失败: {e}")
    
    # 步骤4: 测试下单
    print("\n📈 [步骤4] 测试下单")
    try:
        result = order_volume(
            symbol='SHSE.688295',
            volume=100,
            side=OrderSide_Buy,
            order_type=OrderType_Market,
            position_effect=PositionEffect_Open
        )
        print(f"   ✅ 下单成功!")
        print(f"   订单号: {result[0].order_id}")
        print(f"\n{'='*80}")
        print(f"🎉 掘金IDE账户绑定正常，下单功能可用")
        print(f"{'='*80}")
    except Exception as e:
        print(f"   ❌ 下单失败: {e}")
        print(f"\n{'='*80}")
        print(f"💡 诊断建议:")
        print(f"   1. 确认掘金终端'账户管理'中账户状态为'已连接'")
        print(f"   2. 尝试断开账户后重新连接")
        print(f"   3. 只保留一个账户连接（避免多账户冲突）")
        print(f"   4. 重启掘金终端后重试")
        print(f"{'='*80}")
    
    # 停止策略
    stop()


if __name__ == '__main__':
    run(
        strategy_id='gm_ide_account_diagnose',
        filename='gm_ide_diagnose.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562'
    )
