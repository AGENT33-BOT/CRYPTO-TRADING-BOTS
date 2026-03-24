import psutil

bots = ['mean_reversion', 'momentum', 'scalping', 'grid_trader', 'funding_arbitrage']
status = {bot: 'STOPPED' for bot in bots}

for proc in psutil.process_iter(['pid', 'cmdline']):
    try:
        cmd = ' '.join(proc.cmdline()) if proc.cmdline() else ''
        for bot in bots:
            if bot in cmd.lower():
                status[bot] = f'RUNNING (PID: {proc.pid})'
    except:
        pass

for bot, stat in status.items():
    print(f'{bot}: {stat}')
