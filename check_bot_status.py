import os
import glob

print('=== BOT STATUS ===')
pid_files = glob.glob('*.pid')
for pid_file in pid_files:
    bot_name = pid_file.replace('.pid', '').replace('_', ' ').title()
    try:
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        try:
            os.kill(int(pid), 0)
            print(f'✅ {bot_name}: Running (PID: {pid})')
        except ProcessLookupError:
            print(f'❌ {bot_name}: Stale PID file (PID: {pid})')
    except Exception as e:
        print(f'⚠️ {bot_name}: Error reading PID - {e}')

if not pid_files:
    print('No PID files found')
