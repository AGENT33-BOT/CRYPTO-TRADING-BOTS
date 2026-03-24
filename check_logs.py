import sys
files = {
    'Mean Reversion': 'mean_reversion.log',
    'Momentum': 'momentum_trader.log',
    'Scalping': 'scalping_bot.log',
    'Funding Arbitrage': 'funding_arbitrage.log',
    'Grid Trading': 'grid_trading.log'
}
for name, filename in files.items():
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            last_lines = lines[-3:]
            print(f"\n=== {name} ===")
            print(''.join(last_lines))
    except Exception as e:
        print(f"\n=== {name} ===")
        print(f"Error: {e}")
