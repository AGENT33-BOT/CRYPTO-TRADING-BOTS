import time
import subprocess
import sys

print("="*60)
print("TP/SL GUARDIAN - CONTINUOUS MODE")
print("Checking every 60 seconds...")
print("Press Ctrl+C to stop")
print("="*60)

count = 0
while True:
    try:
        count += 1
        result = subprocess.run([sys.executable, 'ensure_tp_sl.py'], 
                               capture_output=True, text=True, timeout=45)
        if result.returncode == 0:
            print(f"[{count}] Guardian check complete ✓")
        else:
            print(f"[{count}] Guardian error: {result.stderr[:100]}")
    except Exception as e:
        print(f"[{count}] Error: {e}")
    
    time.sleep(60)
