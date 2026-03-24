#!/usr/bin/env python3
"""
ORB Strategy 30-Day Backtest Report
Tests ORB (Opening Range Breakout) on major crypto pairs
"""

import sys
sys.path.insert(0, '.')
from backtest_strategies import MultiStrategyBacktester

# Symbols to test
symbols = [
    'BTC/USDT:USDT',
    'ETH/USDT:USDT', 
    'SOL/USDT:USDT',
    'XRP/USDT:USDT',
    'DOGE/USDT:USDT',
    'LINK/USDT:USDT',
    'DOT/USDT:USDT',
    'ADA/USDT:USDT'
]

# 30 days of 1h candles = 720 candles
LIMIT = 720
TIMEFRAME = '1h'

print("="*75)
print("ORB STRATEGY - 30 DAY BACKTEST REPORT")
print("="*75)
print(f"Timeframe: {TIMEFRAME}")
print(f"Candles: {LIMIT} (~30 days)")
print(f"Opening Range: First 4 candles of each 24-candle session")
print(f"Risk per trade: 2% | Leverage: 3x | Min Confidence: 70%")
print("="*75)

all_results = []

for symbol in symbols:
    print(f"\n\n{'#'*75}")
    print(f"Testing: {symbol}")
    print('#'*75)
    
    try:
        backtester = MultiStrategyBacktester(initial_balance=100.0, leverage=3)
        result = backtester.run_backtest(
            symbol=symbol,
            strategy_name='orb',
            timeframe=TIMEFRAME,
            limit=LIMIT,
            min_confidence=70,
            risk_per_trade=0.02
        )
        
        if result:
            result['symbol'] = symbol
            all_results.append(result)
            
    except Exception as e:
        print(f"Error testing {symbol}: {e}")

# Summary table
print("\n\n" + "="*75)
print("ORB STRATEGY - 30 DAY SUMMARY ACROSS ALL PAIRS")
print("="*75)
print(f"{'Symbol':<15} {'Trades':<8} {'Win Rate':<10} {'Total P&L':<12} {'Max DD':<10} {'Profit Fac':<10}")
print("-"*75)

total_pnl = 0
total_trades = 0

for r in all_results:
    print(f"{r['symbol']:<15} {r['total_trades']:<8} {r['win_rate']:>7.1f}%   ${r['total_pnl']:>+8.2f}   {r['max_drawdown']:>7.1f}%   {r['profit_factor']:>8.2f}")
    total_pnl += r['total_pnl']
    total_trades += r['total_trades']

print("-"*75)
avg_pnl = total_pnl / len(all_results) if all_results else 0
print(f"{'AVERAGE':<15} {total_trades//len(all_results) if all_results else 0:<8} {'':<10} ${avg_pnl:>+8.2f}")
print(f"{'TOTAL':<15} {total_trades:<8} {'':<10} ${total_pnl:>+8.2f}")

# Best and worst performers
if all_results:
    best = max(all_results, key=lambda x: x['total_pnl'])
    worst = min(all_results, key=lambda x: x['total_pnl'])
    best_wr = max(all_results, key=lambda x: x['win_rate'])
    
    print("\n" + "="*75)
    print("KEY INSIGHTS")
    print("="*75)
    print(f"Best P&L:      {best['symbol']} (${best['total_pnl']:+.2f})")
    print(f"Worst P&L:     {worst['symbol']} (${worst['total_pnl']:+.2f})")
    print(f"Best Win Rate: {best_wr['symbol']} ({best_wr['win_rate']:.1f}%)")
    print(f"Total Trades:  {total_trades}")
    print(f"Combined P&L:  ${total_pnl:+.2f} on $100 per pair (${total_pnl/len(all_results):+.2f} avg per pair)")
    
    # Calculate overall win rate
    total_wins = sum(r['total_trades'] * r['win_rate']/100 for r in all_results)
    overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
    print(f"Overall Win Rate: {overall_wr:.1f}%")

print("\n" + "="*75)
print("ORB STRATEGY EXPLANATION")
print("="*75)
print("""
Opening Range Breakout (ORB) Strategy:

1. Define "Opening Range" as first 4 candles of each 24-candle session
   (For 1h charts = first 4 hours of each day)

2. Calculate ORB High/Low from the opening range

3. Entry: Price breaks above ORB High (LONG) or below ORB Low (SHORT)
   - Volume must be > 1.3x average
   - RSI confirmation (50-75 for longs, 25-50 for shorts)
   - Skip if opening range is < 0.3% (choppy market)

4. Exit: 
   - Take Profit: 2x the opening range width
   - Stop Loss: Just outside the opposite side of range

5. Time Window: Only trade between candles 4-20 of each session
   (Avoid late session breakouts which are less reliable)

PROS:
- Captures early momentum after price consolidation
- Clear, objective entry/exit rules
- Works well in volatile markets

CONS:
- Can produce false breakouts in ranging markets
- Requires sufficient opening range volatility
- Limited trading windows per day
""")

print("\nDone!")
