import os
import glob
import json

# Check for closed trades
files = glob.glob('closed_trades_*.json')
if files:
    print(f'Found {len(files)} closed trades file(s)')
    for f in sorted(files)[-3:]:
        print(f'  - {f}')
        if os.path.getsize(f) > 10:
            with open(f) as fp:
                trades = json.load(fp)
                if trades:
                    print(f'    {len(trades)} trades recorded')
                    for t in trades[-3:]:
                        print(f'    {t.get("timestamp", "N/A")}: {t.get("symbol", "N/A")} {t.get("side", "N/A")} @ {t.get("entry", "N/A")} -> {t.get("exit", "N/A")}, PnL: {t.get("pnl", "N/A")}')
else:
    print('No closed trades files found')

print()

# Check bot status
bot_files = ['mean_reversion_bot.py', 'momentum_bot.py', 'scalping_bot.py', 'grid_bot.py', 'funding_arbitrage.py']
running = []
for bot in bot_files:
    pid_file = bot.replace('.py', '.pid')
    try:
        with open(pid_file) as f:
            pid = f.read().strip()
            print(f'{bot}: Running (PID: {pid})')
            running.append(bot)
    except FileNotFoundError:
        print(f'{bot}: Not running')

print(f'\nRunning bots: {len(running)}/{len(bot_files)}')
