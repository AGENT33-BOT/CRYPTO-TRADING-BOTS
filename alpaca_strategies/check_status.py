import os
from datetime import datetime

log_files = []
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.log'):
            path = os.path.join(root, f)
            stat = os.stat(path)
            log_files.append((f, path, stat.st_mtime))

log_files.sort(key=lambda x: x[2], reverse=True)
print('\n=== 10 Most Recently Modified Log Files ===')
for name, path, mtime in log_files[:10]:
    dt = datetime.fromtimestamp(mtime)
    print(f'{dt.strftime("%Y-%m-%d %H:%M")} - {name}')

# Check parallel_runner.log last lines
print('\n=== Last 20 lines of parallel_runner.log ===')
try:
    with open('parallel_runner.log', 'r') as f:
        lines = f.readlines()
        for line in lines[-20:]:
            print(line.strip())
except Exception as e:
    print(f'Error: {e}')

# Check strategy_manager.log last lines
print('\n=== Last 20 lines of strategy_manager.log ===')
try:
    with open('strategy_manager.log', 'r') as f:
        lines = f.readlines()
        for line in lines[-20:]:
            print(line.strip())
except Exception as e:
    print(f'Error: {e}')
