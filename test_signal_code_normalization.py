# -*- coding: utf-8 -*-
"""
测试股票代码标准化逻辑
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

用途：验证 _get_latest_volume_ratio 方法能否正确解析AlphaPilot信号文件格式
"""
import json
import os


def test_code_normalization():
    """测试股票代码标准化逻辑"""
    
    print("=" * 60)
    print("🧪 测试股票代码标准化逻辑")
    print("=" * 60)
    
    # 测试用例：各种格式的股票代码
    test_cases = [
        # (输入格式, 期望提取的纯数字代码)
        ("300444.SZ", "300444"),      # AlphaPilot格式（深交所）
        ("603353.SH", "603353"),      # AlphaPilot格式（上交所）
        ("SZSE.300444", "300444"),    # 系统内部格式（深交所）
        ("SHSE.603353", "603353"),    # 系统内部格式（上交所）
        ("688295.SH", "688295"),      # 科创板
        ("301358.SZ", "301358"),      # 创业板
    ]
    
    print("\n📋 测试场景：从信号文件读取股票代码并标准化\n")
    
    for sig_code, expected in test_cases:
        # 模拟 _get_latest_volume_ratio 中的标准化逻辑
        if '.' in sig_code:
            parts = sig_code.split('.')
            # 判断哪部分是数字代码
            if parts[0].isdigit():
                # 格式：300444.SZ
                sig_pure = parts[0]
            elif parts[1].isdigit():
                # 格式：SZSE.300444
                sig_pure = parts[1]
            else:
                sig_pure = None
        else:
            sig_pure = sig_code
        
        # 验证结果
        status = "✅" if sig_pure == expected else "❌"
        print(f"{status} 输入: {sig_code:15s} → 提取: {sig_pure:10s} (期望: {expected})")
    
    print("\n" + "=" * 60)
    print("📋 测试场景：模拟信号文件解析\n")
    
    # 模拟信号文件内容
    sample_signal = {
        "ts": "2026-04-15 14:32:59",
        "code": "603353.SH",
        "name": "和顺电气",
        "action": "BUY",
        "price": 38.63,
        "volume_ratio": 22.50,
        "source": "AlphaPilot_Email"
    }
    
    print(f"📨 信号数据: {json.dumps(sample_signal, ensure_ascii=False)}")
    
    # 测试匹配逻辑
    system_code = "SHSE.603353"  # 系统内部格式
    sig_code = sample_signal['code']  # AlphaPilot格式
    
    # 提取系统代码的纯数字部分
    system_pure = system_code.split('.')[-1] if '.' in system_code else system_code
    
    # 提取信号代码的纯数字部分
    if '.' in sig_code:
        parts = sig_code.split('.')
        if parts[0].isdigit():
            sig_pure = parts[0]
        elif parts[1].isdigit():
            sig_pure = parts[1]
        else:
            sig_pure = None
    else:
        sig_pure = sig_code
    
    match_result = "✅ 匹配成功" if system_pure == sig_pure else "❌ 匹配失败"
    print(f"\n🔍 匹配测试:")
    print(f"   系统代码: {system_code} → {system_pure}")
    print(f"   信号代码: {sig_code} → {sig_pure}")
    print(f"   结果: {match_result}")
    print(f"   量比: {sample_signal['volume_ratio']}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_code_normalization()
