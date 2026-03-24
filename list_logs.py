import os
import glob

# Check main dir logs
main_logs = [f for f in os.listdir('.') if f.endswith('.log')]
print("Main directory logs:")
for f in main_logs:
    mtime = os.path.getmtime(f)
    from datetime import datetime
    dt = datetime.fromtimestamp(mtime)
    print(f"  {f} - {dt.strftime('%Y-%m-%d %H:%M')}")

# Check archived logs
log_dir = r'C:\Users\digim\clawd\crypto_trader\archived_strategies\logs'
if os.path.exists(log_dir):
    archived_logs = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    print("\nArchived logs:")
    for f in archived_logs[-10:]:
        mtime = os.path.getmtime(os.path.join(log_dir, f))
        dt = datetime.fromtimestamp(mtime)
        print(f"  {f} - {dt.strftime('%Y-%m-%d %H:%M')}")
else:
    print("\nNo archived logs directory")
