import os

logs = [
    ('Mean Reversion', 'logs/mean_reversion_bot.log'),
    ('Momentum', 'logs/momentum_bot.log'),
    ('Scalping', 'logs/scalping_bot.log'),
    ('Grid Trading', 'logs/grid_trading_bot.log'),
    ('Funding Arbitrage', 'logs/funding_arbitrage_bot.log')
]

print('='*60)
print('BOT LOG TAIL CHECK')
print('='*60)

for name, logfile in logs:
    print(f'\n=== {name} ===')
    if os.path.exists(logfile):
        try:
            with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if lines:
                    for line in lines[-3:]:
                        print(line.strip())
                else:
                    print('(empty file)')
        except Exception as e:
            print(f'Error reading: {e}')
    else:
        print('(file not found)')
