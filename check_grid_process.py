#!/usr/bin/env python3
import psutil

grid_pids = []
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if p.info['name'] and 'python' in p.info['name'].lower():
            cmdline = str(p.info['cmdline']).lower()
            if 'grid' in cmdline:
                grid_pids.append((p.info['pid'], p.info['cmdline']))
    except:
        pass

if grid_pids:
    print(f"Found {len(grid_pids)} grid trading process(es):")
    for pid, cmd in grid_pids:
        print(f"  PID {pid}: {cmd}")
else:
    print("No grid trading process found - BOT NOT RUNNING")
