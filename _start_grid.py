import subprocess
import sys

# Start grid trader in background
subprocess.Popen(
    [sys.executable, 'grid_trader.py'],
    stdout=open('grid_trader_restart.log', 'a'),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NO_WINDOW
)
print("Grid trader started")
