from backtest_strategies import MultiStrategyBacktester

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT']
print('='*70)
print('ORB STRATEGY - 30 DAY BACKTEST (720 candles)')
print('='*70)

results = []
for symbol in symbols:
    print(f'\n>>> Testing {symbol}...')
    bt = MultiStrategyBacktester(initial_balance=100.0, leverage=3)
    result = bt.run_backtest(symbol, 'orb', '1h', 720, 70, 0.02)
    if result:
        result['symbol'] = symbol
        results.append(result)
        print(f"Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.1f}%, PnL: ${result['total_pnl']:+.2f}")

print('\n' + '='*70)
print('SUMMARY')
print('='*70)
print(f"{'Symbol':<15} {'Trades':<8} {'Win Rate':<10} {'Total P&L':<12}")
print('-'*70)
for r in results:
    print(f"{r['symbol']:<15} {r['total_trades']:<8} {r['win_rate']:>7.1f}%   ${r['total_pnl']:>+8.2f}")
