#!/usr/bin/env python3
"""Stop funding arbitrage and close related positions"""
import psutil
import os
import time

print("=" * 60)
print("STOPPING FUNDING ARBITRAGE STRATEGIES")
print("=" * 60)

# Kill all funding arbitrage processes
killed = []
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] == 'python.exe':
            cmdline = proc.info.get('cmdline', [])
            if cmdline:
                script = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)
                if 'funding' in script.lower() and 'arbitrage' in script.lower():
                    try:
                        proc.kill()
                        killed.append((proc.info['pid'], script))
                        print(f"✅ KILLED: PID {proc.info['pid']} - {script[:80]}...")
                    except:
                        pass
    except:
        pass

print(f"\nTotal killed: {len(killed)} funding arbitrage processes")

# List of funding arbitrage files to archive/delete
files_to_archive = [
    'funding_arbitrage.py',
    'funding_futures_only.py',
    'funding_arbitrage.log',
    'funding_futures_only.log',
    'funding_futures_only_restart.log'
]

print("\n" + "=" * 60)
print("ARCHIVING FUNDING ARBITRAGE FILES")
print("=" * 60)

# Create archive directory
archive_dir = 'archived_strategies'
os.makedirs(archive_dir, exist_ok=True)

archived = []
for filename in files_to_archive:
    if os.path.exists(filename):
        import shutil
        dest = os.path.join(archive_dir, filename)
        shutil.move(filename, dest)
        archived.append(filename)
        print(f"✅ ARCHIVED: {filename}")

print(f"\nTotal archived: {len(archived)} files")
print(f"Location: ./{archive_dir}/")

print("\n" + "=" * 60)
print("FUNDING ARBITRAGE STRATEGIES DELETED")
print("=" * 60)
