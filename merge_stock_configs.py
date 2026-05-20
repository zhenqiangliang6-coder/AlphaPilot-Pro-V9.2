#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stock Config Merger Tool
合并 qmt_delay_config.json 到 stock_personalities.json

使用方法:
    python merge_stock_configs.py
    
功能说明:
    - 以 qmt_delay_config.json 的新数据覆盖重复个股
    - 保留 stock_personalities.json 中独有的配置（如 immediate 类型和 default）
    - 自动处理 NaN 值问题
"""

import json
import math
import os
import sys


def merge_stock_configs():
    """合并 qmt_delay_config.json 到 stock_personalities.json"""
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    
    base_path = os.path.join(data_dir, 'stock_personalities.json')
    override_path = os.path.join(data_dir, 'qmt_delay_config.json')
    output_path = os.path.join(data_dir, 'stock_personalities.json')
    
    # Check if files exist
    if not os.path.exists(base_path):
        print(f'[ERROR] Base config not found: {base_path}')
        return False
    if not os.path.exists(override_path):
        print(f'[ERROR] Override config not found: {override_path}')
        return False
    
    # Read base config
    with open(base_path, 'r', encoding='utf-8') as f:
        base_config = json.load(f)
    
    # Read override config
    with open(override_path, 'r', encoding='utf-8') as f:
        override_config = json.load(f)
    
    print(f'[INFO] Base config stocks: {len(base_config)}')
    print(f'[INFO] Override config stocks: {len(override_config)}')
    
    # Start merging
    merged = {}
    
    # 1. Copy all stocks from base config except 'default'
    for code, config in base_config.items():
        if code != 'default':
            merged[code] = config.copy()
    
    # 2. Update with override config
    overridden_codes = []
    new_codes = []
    
    for code, config in override_config.items():
        # Handle NaN values
        if 'min_volume_ratio' in config:
            value = config['min_volume_ratio']
            if isinstance(value, float) and math.isnan(value):
                config['min_volume_ratio'] = 0.0
                print(f'[WARN] {code} ({config.get("name", "Unknown")}) min_volume_ratio is NaN, set to 0.0')
        
        if code in merged:
            overridden_codes.append(code)
        else:
            new_codes.append(code)
        
        merged[code] = config.copy()
    
    # 3. Keep default config
    if 'default' in base_config:
        merged['default'] = base_config['default'].copy()
    
    print('')
    print(f'[SUCCESS] Merge Statistics:')
    print(f'   - Overridden stocks: {len(overridden_codes)}')
    print(f'   - New stocks: {len(new_codes)}')
    print(f'   - Total after merge: {len(merged)}')
    
    if overridden_codes:
        preview = ', '.join(overridden_codes[:10])
        if len(overridden_codes) > 10:
            preview += '...'
        print(f'[INFO] Overridden codes: {preview}')
    
    if new_codes:
        preview = ', '.join(new_codes[:10])
        if len(new_codes) > 10:
            preview += '...'
        print(f'[NEW] New codes: {preview}')
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    
    print('')
    print(f'[DONE] Merge completed! File saved to: {output_path}')
    return True


if __name__ == '__main__':
    try:
        success = merge_stock_configs()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f'[ERROR] Merge failed: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
