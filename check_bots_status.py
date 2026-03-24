import psutil

bots = {
    'Mean Reversion': ['mean_reversion'],
    'Momentum': ['momentum'],
    'Scalping': ['scalping'],
    'Grid Trader': ['grid'],
    'Funding Arbitrage': ['funding']
}

running = {name: [] for name in bots}

for p in psutil.process_iter(['pid', 'cmdline']):
    try:
        cmdline = p.info['cmdline']
        if cmdline:
            cmd_str = ' '.join(cmdline).lower()
            for bot_name, keywords in bots.items():
                if any(kw in cmd_str for kw in keywords):
                    running[bot_name].append(p.info['pid'])
    except:
        pass

print("="*50)
print("AGENT33 BOT STATUS CHECK")
print("="*50)
all_running = True
for bot, pids in running.items():
    status = f"RUNNING (PID: {pids[0]})" if pids else "STOPPED"
    symbol = "✅" if pids else "❌"
    print(f"{symbol} {bot}: {status}")
    if not pids:
        all_running = False

print("="*50)
print(f"Status: {'ALL BOTS RUNNING' if all_running else 'SOME BOTS STOPPED'}")
