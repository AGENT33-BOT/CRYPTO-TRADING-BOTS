import os

# Check funding arbitrage last 5 lines
print('=== FUNDING ARBITRAGE LAST 5 LINES ===')
with open('funding_arbitrage.log', 'r') as f:
    lines = f.readlines()
    for line in lines[-5:]:
        print(line.strip())

print('\n=== GRID TRADING LAST 10 LINES ===')
with open('grid_trading.log', 'r') as f:
    lines = f.readlines()
    for line in lines[-10:]:
        print(line.strip())

# Check if grid trader PID exists
print('\n=== CHECKING GRID TRADER PID ===')
with open('grid_trading.log', 'r') as f:
    content = f.read()
    if 'PID' in content:
        # Find the most recent PID
        import re
        pids = re.findall(r'PID[:\s]+(\d+)', content)
        if pids:
            latest_pid = pids[-1]
            print(f'Latest Grid Trader PID mentioned: {latest_pid}')
            # Check if process exists
            import subprocess
            result = subprocess.run(['tasklist', '/FI', f'PID eq {latest_pid}'], capture_output=True, text=True)
            if latest_pid in result.stdout:
                print(f'PID {latest_pid} is RUNNING')
            else:
                print(f'PID {latest_pid} is NOT RUNNING - needs restart')