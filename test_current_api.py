from gm.api import *
import pprint

def init(context):
    print("========================================")
    print("🔍 测试 gm 3.0.183 的 current() 返回格式")
    print("========================================")

    symbols = ["SZSE.300285"]

    print("\n📌 调用：current(symbols=['SZSE.300285'], fields='price')\n")

    try:
        data = current(
            symbols=symbols,
            fields='price'
        )
        print("✅ 返回类型:", type(data))
        print("✅ 返回内容:")
        pprint.pprint(data)

    except Exception as e:
        print("❌ 调用失败:", e)

    print("\n🎯 测试结束")
    print("========================================")

def on_bar(context, bars):
    pass


# ❗❗❗ run() 必须放在最外层，不能缩进
run(
    strategy_id='c2dd98da-3d5a-11f1-962d-1ece51d839d6',
    filename='test_current_api.py',
    mode=MODE_LIVE,
    token='fdf08e9d00c4da3b635c2616724ddae3f7793562'
)
