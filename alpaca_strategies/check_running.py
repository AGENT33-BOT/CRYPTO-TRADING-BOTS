import psutil
import json
from datetime import datetime

alpaca_procs = []
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
    try:
        if p.info['name'] == 'python.exe' and p.info['cmdline']:
            cmdline = ' '.join(p.info['cmdline'])
            if 'alpaca' in cmdline.lower() and 'strategy' in cmdline.lower():
                alpaca_procs.append({
                    'pid': p.info['pid'],
                    'cmdline': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline,
                    'started': datetime.fromtimestamp(p.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                })
    except:
        pass

print(f"Running Alpaca strategy processes: {len(alpaca_procs)}")
for p in alpaca_procs[:10]:
    print(f"  PID {p['pid']} ({p['started']}): {p['cmdline']}")
if len(alpaca_procs) > 10:
    print(f"  ... and {len(alpaca_procs) - 10} more")
