import os, time

print('='*50)
print('BOT STATUS - LOG ACTIVITY CHECK')
print('='*50)

bots = [
    ('Mean Reversion', 'logs/mean_reversion_bot.log'),
    ('Momentum', 'logs/momentum_bot.log'),
    ('Scalping', 'logs/scalping_bot.log'),
    ('Grid Trading', 'logs/grid_trading_bot.log'),
    ('Funding Arbitrage', 'logs/funding_arbitrage_bot.log')
]

for name, logfile in bots:
    if os.path.exists(logfile):
        mtime = os.path.getmtime(logfile)
        age_min = (time.time() - mtime) / 60
        status = 'RUNNING' if age_min < 10 else 'STALE' if age_min < 60 else 'ERROR'
        print(f'{name}: {status} ({age_min:.1f} min ago)')
    else:
        print(f'{name}: NO LOG FILE')
