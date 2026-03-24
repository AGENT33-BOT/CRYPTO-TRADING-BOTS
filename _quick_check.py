import psutil

bots = ['mean_reversion', 'momentum', 'scalping', 'grid_trader', 'funding_arbitrage']
found_bots = []

for proc in psutil.process_iter(['pid', 'cmdline', 'name']):
    try:
        cmd = ' '.join(proc.cmdline()) if proc.cmdline() else ''
        for bot in bots:
            if bot in cmd.lower():
                found_bots.append(f"{bot}: RUNNING (PID: {proc.pid})")
    except:
        pass

if found_bots:
    for bot in found_bots:
        print(bot)
else:
    print("WARNING: No trading bots found running!")

print("\nAll Python processes:")
count = 0
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    if proc.name() and 'python' in proc.name().lower():
        cmd = ' '.join(proc.cmdline())[:60] if proc.cmdline() else ''
        print(f"  PID {proc.pid}: {cmd}")
        count += 1
        if count >= 10:
            print("  ... (more processes)")
            break

if count == 0:
    print("  No Python processes found!")
