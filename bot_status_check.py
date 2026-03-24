import os, time, glob

print("=== BOT STATUS CHECK ===\n")

# Check log file ages
logs = {
    'Funding Arbitrage': 'logs/funding_arbitrage.log',
    'Momentum Bot': 'logs/momentum_bot.log', 
    'Scalping Bot': 'logs/scalping_bot.log',
    'Mean Reversion': 'logs/mean_reversion_bot.log',
    'Grid Trading': 'logs/grid_trading_bot.log'
}

for name, path in logs.items():
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        age_mins = (time.time() - mtime) / 60
        age_str = f"{age_mins:.1f} min ago" if age_mins < 60 else f"{age_mins/60:.1f} hours ago"
        status = "✅ RECENT" if age_mins < 30 else "⚠️ STALE" if age_mins < 120 else "🔴 STALE"
        print(f"{name}: {status} ({age_str})")
    else:
        print(f"{name}: 🔴 FILE NOT FOUND")

print("\n=== CLOSED TRADES ===")
if os.path.exists('trades/closed'):
    files = glob.glob('trades/closed/*.json')
    if files:
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        for f in files[:5]:
            mtime = os.path.getmtime(f)
            age_str = time.strftime('%H:%M', time.localtime(mtime))
            print(f"{os.path.basename(f)} @ {age_str}")
    else:
        print("No closed trades")
else:
    print("No closed trades folder")
