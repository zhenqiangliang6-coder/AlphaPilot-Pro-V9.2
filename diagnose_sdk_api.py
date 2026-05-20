# -*- coding: utf-8 -*-
"""
掘金SDK API 兼容性诊断工具

用于检测当前环境中可用的账户查询API
"""

def diagnose_sdk_api():
    """诊断掘金SDK的API兼容性"""
    print("=" * 60)
    print("掘金SDK API 兼容性诊断")
    print("=" * 60)
    
    # 1. 检查可用的账户相关API
    from gm import api
    account_apis = [x for x in dir(api) if 'account' in x.lower() or 'cash' in x.lower()]
    print(f"\n[1] 账户相关API列表:")
    for api_name in sorted(account_apis):
        print(f"    - {api_name}")
    
    # 2. 测试 get_cash
    print(f"\n[2] 测试 get_cash():")
    try:
        from gm.api import get_cash
        cash_info = get_cash()
        print(f"    ✅ get_cash() 可用")
        print(f"    返回类型: {type(cash_info)}")
        print(f"    可用字段: {[attr for attr in dir(cash_info) if not attr.startswith('_')]}")
        
        # 尝试提取关键字段
        if hasattr(cash_info, 'cash'):
            print(f"    可用资金 (cash): {cash_info.cash}")
        if hasattr(cash_info, 'frozen_cash'):
            print(f"    冻结资金 (frozen_cash): {cash_info.frozen_cash}")
    except Exception as e:
        print(f"    ❌ get_cash() 失败: {e}")
    
    # 3. 测试 get_account（如果存在）
    print(f"\n[3] 测试 get_account():")
    try:
        from gm.api import get_account
        acc_info = get_account()
        print(f"    ✅ get_account() 可用")
        print(f"    返回类型: {type(acc_info)}")
        print(f"    可用字段: {[attr for attr in dir(acc_info) if not attr.startswith('_')]}")
    except ImportError:
        print(f"    ⚠️  get_account() 不存在（当前SDK版本不支持）")
    except Exception as e:
        print(f"    ❌ get_account() 失败: {e}")
    
    # 4. 测试 get_position
    print(f"\n[4] 测试 get_position():")
    try:
        from gm.api import get_position
        positions = get_position()
        print(f"    ✅ get_position() 可用")
        print(f"    持仓数量: {len(positions) if positions else 0}")
        if positions and len(positions) > 0:
            pos = positions[0]
            print(f"    示例持仓字段: {[attr for attr in dir(pos) if not attr.startswith('_')][:10]}")
    except Exception as e:
        print(f"    ❌ get_position() 失败: {e}")
    
    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)


if __name__ == '__main__':
    diagnose_sdk_api()
