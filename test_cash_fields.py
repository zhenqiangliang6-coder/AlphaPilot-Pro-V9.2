# -*- coding: utf-8 -*-
"""
调试 get_cash() 返回的字段名
必须在策略运行时执行（包含 strategy_id 和 token）
"""
from gm.api import *

def init(context):
    """初始化时调试"""
    from gm.api import get_cash
    
    print("=" * 60)
    print("调试 get_cash() 返回对象")
    print("=" * 60)
    
    try:
        cash_info = get_cash()
        print(f"\n返回类型: {type(cash_info)}")
        print(f"\n所有字段: {dir(cash_info)}")
        print(f"\n字段值:")
        
        # 打印所有非私有属性
        for attr in dir(cash_info):
            if not attr.startswith('_'):
                try:
                    value = getattr(cash_info, attr)
                    print(f"  {attr}: {value}")
                except:
                    pass
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

def on_bar(context, bars):
    pass

if __name__ == '__main__':
    run(strategy_id='a62d366d-3c78-11f1-8563-1ece51d839d6',
        filename='test_cash_fields.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562')
