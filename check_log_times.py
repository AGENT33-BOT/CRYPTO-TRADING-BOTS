import os, datetime
logs = [
    ('Mean Reversion', 'logs/mean_reversion_bot.log'),
    ('Momentum', 'logs/momentum.log'),
    ('Scalping', 'logs/scalping.log'),
    ('Grid', 'logs/grid_trader.log'),
    ('Funding', 'logs/funding_arbitrage.log')
]
now = datetime.datetime.now()
print("Log Freshness Check:")
for name, log in logs:
    try:
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(log))
        age = (now - mtime).total_seconds() / 60
        status = "[OK]" if age < 10 else "[WARN]" if age < 30 else "[STALE]"
        print(f"  {status} {name}: Last update {age:.1f}m ago")
    except FileNotFoundError:
        print(f"  [MISSING] {name}: No log file found")
