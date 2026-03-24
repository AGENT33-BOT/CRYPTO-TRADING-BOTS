import psutil
import sys

for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in p.info['name'].lower():
            cmdline = ' '.join(p.info['cmdline']) if p.info['cmdline'] else ''
            print(f"PID {p.info['pid']}: {cmdline}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
