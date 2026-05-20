"""
AlphaPilot Pro V9.1 - Lazy Mode: Replay All Historical Signals

Description:
- Automatically sync all unsynced signal files from D:\mpython\signals\processed in chronological order
- Each file is synced with N seconds interval (configurable), simulating real trading rhythm
- Suitable for batch testing strategy parameters without manually creating signal files

Usage:
    python lazy_replay_all.py
    
Configuration:
    DELAY_SECONDS: Time interval between signals (default 5 seconds)
    MAX_FILES: Maximum number of files to replay (default all, set to 0 for unlimited)
"""

import sys
import os
import time
from datetime import datetime

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.signal_syncer import SignalFileSyncer
from config.settings import *

# ==================== Configuration Section ====================
DELAY_SECONDS = 5  # Interval between each signal (seconds)
MAX_FILES = 0      # Maximum files to replay (0 = all)
# =============================================================


def main():
    """Main function"""
    print("=" * 80)
    print("AlphaPilot Pro V9.1 - Lazy Mode: Replay All Historical Signals")
    print("=" * 80)
    print()
    
    # Initialize syncer
    syncer = SignalFileSyncer(
        source_dir="D:/mpython/signals/processed",
        target_dir="D:/main_data/signals",
        check_interval=30
    )
    
    print(f"Source Directory: {syncer.source_dir}")
    print(f"Target Directory: {syncer.target_dir}")
    print(f"Signal Interval: {DELAY_SECONDS} seconds")
    print(f"Max Files: {'All' if MAX_FILES == 0 else MAX_FILES}")
    print()
    
    # Get all unsynced files
    all_files = syncer.get_all_unsynced_files()
    
    if not all_files:
        print("No new signal files to sync!")
        return
    
    print(f"Found {len(all_files)} files to sync:")
    for i, f in enumerate(all_files[:10], 1):  # Show first 10 only
        print(f"   {i}. {os.path.basename(f)}")
    if len(all_files) > 10:
        print(f"   ... and {len(all_files) - 10} more files")
    print()
    
    # Confirm start
    confirm = input("Start replay? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    print()
    print("Starting replay...")
    print("-" * 80)
    
    # Limit file count
    if MAX_FILES > 0:
        files_to_sync = all_files[:MAX_FILES]
    else:
        files_to_sync = all_files
    
    synced_count = 0
    start_time = time.time()
    
    for i, file_path in enumerate(files_to_sync, 1):
        filename = os.path.basename(file_path)
        
        print(f"\n[{i}/{len(files_to_sync)}] Syncing: {filename}")
        
        # Sync single file
        success = syncer.sync_single_file(file_path)
        
        if success:
            synced_count += 1
            print(f"   OK: Sync successful")
            
            # Wait specified time (don't wait for the last file)
            if i < len(files_to_sync):
                print(f"   Waiting {DELAY_SECONDS} seconds...")
                time.sleep(DELAY_SECONDS)
        else:
            print(f"   FAILED: Sync failed or already skipped")
    
    # Statistics
    elapsed = time.time() - start_time
    print()
    print("-" * 80)
    print(f"Replay Completed!")
    print(f"   Total Files: {len(files_to_sync)}")
    print(f"   Successfully Synced: {synced_count}")
    print(f"   Elapsed Time: {elapsed:.2f} seconds")
    print(f"   Average Speed: {elapsed/max(synced_count, 1):.2f} seconds/file")
    print()
    print("TIP: Strategy will automatically process synced signal files")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nWARNING: User interrupted")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
