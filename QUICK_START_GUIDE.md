# AlphaPilot Pro V9.1 - Quick Start Guide

## Quick Start

### Easiest Way (Recommended for Beginners)

**Double-click:** [`start_lazy_mode.bat`](d:\main_data\start_lazy_mode.bat)

This script will:
1. Automatically check Python environment
2. Create/activate virtual environment
3. Install required dependencies
4. Display configuration and confirm
5. Start lazy mode to replay all historical signals

---

## Three Launch Methods

### Method 1: Standard Mode (Recommended)

**File:** [`start_lazy_mode.bat`](d:\main_data\start_lazy_mode.bat)

**Features:**
- Complete environment check and configuration confirmation
- Optional sync history clearing
- Detailed progress display
- Suitable for first-time use or scenarios requiring careful control

**Usage:**
```bash
Double-click start_lazy_mode.bat
```

---

### Method 2: Quick Mode (For Experienced Users)

**File:** [`start_quick_test.bat`](d:\main_data\start_quick_test.bat)

**Features:**
- Skip all confirmation steps
- Automatically clear sync history
- Start replay directly
- Fastest launch, suitable for frequent testing

**Usage:**
```bash
Double-click start_quick_test.bat
```

---

### Method 3: Multi-Account Parallel Test (Parameter Tuning Tool)

**File:** [`start_multi_account_test.bat`](d:\main_data\start_multi_account_test.bat)

**Features:**
- Launch 3 independent windows simultaneously
- Each window uses different volume ratio threshold
- Automatically compare performance of different parameters
- Quickly find optimal strategy configuration

**Launched Accounts:**
```
Account A: Volume Ratio Threshold 2.0 (Conservative)
Account B: Volume Ratio Threshold 3.0 (Balanced)
Account C: Volume Ratio Threshold 4.0 (Aggressive)
```

**Usage:**
```bash
Double-click start_multi_account_test.bat
```

**Expected Result:**
- Automatically opens 3 CMD windows
- Each window runs replay test independently
- Observe which account has the best profit rate
- Select optimal parameter for live trading

---

## Configuration

To adjust parameters, edit [`lazy_replay_all.py`](d:\main_data\lazy_replay_all.py):

```python
# ==================== Configuration Section ====================
DELAY_SECONDS = 5   # Signal interval time (seconds)
MAX_FILES = 0       # Maximum files to replay (0 = all)
# =============================================================
```

### Common Configuration Examples

**Quick test first 10 signals:**
```python
DELAY_SECONDS = 2
MAX_FILES = 10
```

**Complete backtest all signals:**
```python
DELAY_SECONDS = 10
MAX_FILES = 0
```

**Slow observation mode:**
```python
DELAY_SECONDS = 30
MAX_FILES = 50
```

---

## Output Example

### Standard Mode Output

```
================================================================================
   AlphaPilot Pro V9.1 - Lazy Mode: Replay All Historical Signals
================================================================================

[1/5] Checking Python environment...
OK: Python environment ready.

[2/5] Checking virtual environment...
OK: Virtual environment already exists.

[3/5] Activating virtual environment and installing dependencies...
OK: Dependencies check completed.

[4/5] Configuration confirmation...

Source Directory: D:\mpython\signals\processed
Target Directory: D:\main_data\signals
Signal Interval: 5 seconds
Max Files: All

Found 223 historical signal files

Clear sync history? (y/n, default n): y
OK: Sync history cleared.

[5/5] Starting Lazy Mode...

================================================================================
   Ready to replay all historical signals
   TIP: Press Ctrl+C to interrupt at any time
================================================================================

Press any key to continue...

Starting execution...

================================================================================
AlphaPilot Pro V9.1 - Lazy Mode: Replay All Historical Signals
================================================================================

Source Directory: D:/mpython/signals/processed
Target Directory: D:/main_data/signals
Signal Interval: 5 seconds
Max Files: All

Found 223 files to sync:
   1. signal_batch_20260416_093012_123456.txt
   2. signal_batch_20260416_093545_234567.txt
   ...

Start replay? (y/n): y

Starting replay...
--------------------------------------------------------------------------------

[1/223] Syncing: signal_batch_20260416_093012_123456.txt
   OK: Sync successful
   Waiting 5 seconds...

...

Replay Completed!
   Total Files: 223
   Successfully Synced: 223
   Elapsed Time: 1115.00 seconds
   Average Speed: 5.00 seconds/file

TIP: Strategy will automatically process synced signal files
================================================================================

================================================================================
   Lazy Mode Execution Completed!
================================================================================

Next Steps:
   1. Check Goldminer terminal logs to confirm strategy execution
   2. To adjust parameters, edit configuration section in lazy_replay_all.py
   3. Run this script again to continue testing

Documentation: LAZY_MODE_GUIDE.md

Press any key to continue...
```

---

## Troubleshooting

### Problem 1: "Python not found"

**Solution:**
1. Download and install Python 3.8+
2. Check "Add Python to PATH" during installation
3. Restart command line and retry

### Problem 2: "No signal files found in source directory"

**Solution:**
1. Confirm `D:\mpython\signals\processed` directory exists
2. Confirm `.txt` format signal files exist in that directory
3. If directory is different, modify path configuration in script

### Problem 3: Dependency installation failed

**Solution:**
```bash
# Manual dependency installation
pip install gm python-dotenv watchdog -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Problem 4: Strategy not responding

**Check:**
1. Is Goldminer terminal logged in?
2. Is simulation account working properly?
3. Check log files in `logs` directory

---

## Tips

### Tip 1: Read-Only Observation Mode

Before live trading, enable read-only mode to prevent accidental orders:

Edit `config/settings.py`:
```python
READ_ONLY_MODE = True  # Only log, no orders
TEST_SAFE_MODE = True  # Limit order amount
```

### Tip 2: Continue After Interruption

If interrupted by `Ctrl+C`:
- Already synced files will be skipped
- Next run continues from unsynced position
- No duplicate processing

### Tip 3: Multi-Round Testing

**Round 1:** Quick logic verification
```python
DELAY_SECONDS = 2
MAX_FILES = 10
```

**Round 2:** Complete backtest
```python
DELAY_SECONDS = 10
MAX_FILES = 0
```

**Round 3:** Multi-account comparison
```bash
Double-click start_multi_account_test.bat
```

---

## Practical Cases

### Case 1: Quick Strategy Verification

**Scenario:** Just finished writing strategy code, want to quickly verify it runs correctly

**Steps:**
1. Edit `lazy_replay_all.py`:
   ```python
   DELAY_SECONDS = 2
   MAX_FILES = 5
   ```
2. Double-click `start_quick_test.bat`
3. Complete 5 signal tests within 2 minutes
4. Check logs to confirm buy/sell logic is correct

### Case 2: Parameter Optimization

**Scenario:** Want to find optimal volume ratio threshold

**Steps:**
1. Double-click `start_multi_account_test.bat`
2. Wait for 3 windows to complete testing
3. Compare results:
   ```
   Account A (Threshold 2.0): 45 buys, 60% success, +12% profit
   Account B (Threshold 3.0): 30 buys, 75% success, +18% profit  <- Best
   Account C (Threshold 4.0): 15 buys, 85% success, +10% profit
   ```
4. Apply Account B's parameters to live trading

### Case 3: Complete Backtest

**Scenario:** Have time on weekend, want comprehensive strategy evaluation

**Steps:**
1. Edit `lazy_replay_all.py`:
   ```python
   DELAY_SECONDS = 10
   MAX_FILES = 0  # All 223 files
   ```
2. Double-click `start_lazy_mode.bat`
3. Complete full backtest in ~37 minutes
4. Analyze overall performance, decide whether to go live

---

## Summary

### Applicable Scenarios for Three Scripts

| Script | Scenario | Features |
|--------|----------|----------|
| `start_lazy_mode.bat` | First-time use, need fine control | Complete check, optional config |
| `start_quick_test.bat` | Frequent testing, experienced users | Quick launch, auto-clear |
| `start_multi_account_test.bat` | Parameter tuning, comparison test | 3-account parallel, auto-compare |

### Core Advantages

- **Zero Workload** - No need to manually create signal files
- **One-Click Launch** - Double-click to run
- **Smart Management** - Automatically handle environment, dependencies, history
- **Flexible Configuration** - Adjustable interval, quantity, parameters

---

## Related Documentation

- [LAZY_MODE_GUIDE.md](d:\main_data\LAZY_MODE_GUIDE.md) - Detailed feature description
- [LAZY_MODE_SUMMARY.md](d:\main_data\LAZY_MODE_SUMMARY.md) - Technical implementation summary
- [REPLAY_MODE_GUIDE.md](d:\main_data\REPLAY_MODE_GUIDE.md) - Complete replay mode guide

---

**Try it now!** 

Double-click [`start_lazy_mode.bat`](d:\main_data\start_lazy_mode.bat) to start your first lazy mode test!

Good luck with parameter tuning and successful trading!
