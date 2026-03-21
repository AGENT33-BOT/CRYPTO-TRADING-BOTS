import psutil

bots = {
    'mean_reversion_trader.py': 'Mean Reversion Bot',
    'momentum_trader.py': 'Momentum Bot', 
    'scalping_bot.py': 'Scalping Bot',
    'grid_trader.py': 'Grid Trading Bot',
    'funding_arbitrage.py': 'Funding Arbitrage Bot'
}

running = {}
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = ' '.join(proc.info['cmdline'] or [])
        for script, name in bots.items():
            if script in cmdline:
                running[name] = 'RUNNING'
    except:
        pass

print("BOT STATUS CHECK")
print("=" * 40)
for script, name in bots.items():
    status = running.get(name, 'STOPPED')
    icon = "[OK]" if status == "RUNNING" else "[STOPPED]"
    print(f"{icon} {name}: {status}")
