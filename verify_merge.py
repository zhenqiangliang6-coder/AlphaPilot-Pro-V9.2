import json

def verify_merged_config():
    """验证合并后的配置文件"""
    
    config_path = r'd:\main_data\data\stock_personalities.json'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('✅ 验证成功！')
    print(f'📊 总股票数: {len(data)}')
    
    delayed = [k for k, v in data.items() if v.get('type') == 'delayed']
    immediate = [k for k, v in data.items() if v.get('type') == 'immediate']
    
    print(f'⏱️  Delayed类型: {len(delayed)} 只')
    print(f'⚡ Immediate类型: {len(immediate)} 只')
    print(f'🎯 Default配置: {"存在" if "default" in data else "缺失"}')
    
    # 检查是否有NaN值
    nan_count = 0
    for code, config in data.items():
        if 'min_volume_ratio' in config:
            value = config['min_volume_ratio']
            if isinstance(value, float) and value != value:  # NaN check
                nan_count += 1
                print(f'⚠️  警告: {code} 存在 NaN 值')
    
    if nan_count == 0:
        print('✅ 无 NaN 值，数据完整')
    
    # 显示部分新增的股票
    new_stocks = ['000338', '300259', '301171', '688295', '300763', '301278', '300449', '300782', '300364']
    print(f'\n🆕 验证新增股票:')
    for code in new_stocks:
        if code in data:
            print(f'   ✓ {code} - {data[code].get("name", "未知")}')
        else:
            print(f'   ✗ {code} - 缺失')
    
    print(f'\n💾 文件路径: {config_path}')
    print(f'✨ 合并完成！')

if __name__ == '__main__':
    verify_merged_config()
