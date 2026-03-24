import os, time

logs = {
    'Funding Arbitrage': 'logs/funding_arbitrage.log',
    'Momentum Bot': 'logs/momentum_bot.log', 
    'Scalping Bot': 'logs/scalping_bot.log',
    'Mean Reversion': 'logs/mean_reversion_bot.log',
    'Grid Trading': 'logs/grid_trading_bot.log'
}

print("=== BOT STATUS CHECK ===")
for name, path in logs.items():
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        age_mins = (time.time() - mtime) / 60
        age_str = f"{age_mins:.1f} min ago" if age_mins < 60 else f"{age_mins/60:.1f} hours ago"
        status = "OK" if age_mins < 30 else "STALE" if age_mins < 120 else "DEAD"
        print(f"{name}: {status} ({age_str})")
    else:
        print(f"{name}: FILE NOT FOUND")
