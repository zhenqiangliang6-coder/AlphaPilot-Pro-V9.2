import os

def extract_timestamp(filename):
    basename = os.path.basename(filename)
    parts = basename.split('_')
    
    if len(parts) >= 4:
        try:
            date_str = parts[2]  # 20260424
            time_str = parts[3]  # 095753
            
            if len(date_str) == 8 and len(time_str) == 6 and date_str.isdigit() and time_str.isdigit():
                return f"{date_str}_{time_str}"
        except:
            pass
    
    return str(os.path.getmtime(filename))

files = [
    'D:/mpython/signals/processed/test_new_signal_2.txt',
    'D:/mpython/signals/processed/signal_batch_20260424_150150_605215.txt',
    'D:/mpython/signals/processed/signal_batch_20260424_145656_725199.txt'
]

print("时间戳提取测试:")
print("=" * 60)
for f in files:
    ts = extract_timestamp(f)
    print(f"{os.path.basename(f)}: {ts}")

latest = max(files, key=extract_timestamp)
print(f"\n✅ 最新文件: {os.path.basename(latest)}")
print(f"   时间戳: {extract_timestamp(latest)}")
