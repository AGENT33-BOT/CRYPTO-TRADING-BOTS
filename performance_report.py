"""
Generate Trading Performance Report
Analyzes all strategy logs and trade history
"""
import ccxt
import json
import os
from datetime import datetime, timedelta

print("=" * 70)
print("TRADING STRATEGY PERFORMANCE REPORT")
print("=" * 70)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

try:
    exchange.load_markets()
    
    # Fetch balance
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    
    print("\nCURRENT ACCOUNT STATUS")
    print("-" * 70)
    print(f"Total Balance: ${usdt.get('total', 0):.2f} USDT")
    print(f"Free: ${usdt.get('free', 0):.2f} USDT")
    print(f"Used: ${usdt.get('used', 0):.2f} USDT")
    
    # Fetch positions
    positions = exchange.fetch_positions()
    
    print("\nCURRENT OPEN POSITIONS")
    print("-" * 70)
    
    total_pnl = 0
    winning = 0
    losing = 0
    
    for pos in positions:
        contracts = float(pos.get('contracts', 0))
        if contracts == 0:
            continue
            
        symbol = pos.get('symbol', '')
        side = pos.get('side', '')
        entry = float(pos.get('entryPrice', 0))
        mark = float(pos.get('markPrice', 0))
        pnl = float(pos.get('unrealizedPnl', 0))
        notional = float(pos.get('notional', 0))
        
        total_pnl += pnl
        if pnl > 0:
            winning += 1
        elif pnl < 0:
            losing += 1
        
        status = "[WIN]" if pnl > 0 else "[LOSS]" if pnl < 0 else "[B/E]"
        print(f"\n{status} {symbol}")
        print(f"   Side: {side.upper()}")
        print(f"   Entry: ${entry:.4f} | Mark: ${mark:.4f}")
        print(f"   Size: {contracts}")
        print(f"   Notional: ${abs(notional):.2f}")
        print(f"   P&L: ${pnl:.2f}")
    
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total Unrealized P&L: ${total_pnl:.2f}")
    print(f"Winning Positions: {winning}")
    print(f"Losing Positions: {losing}")
    print(f"Total Positions: {winning + losing}")
    
    if winning + losing > 0:
        win_rate = (winning / (winning + losing)) * 100
        print(f"Win Rate: {win_rate:.1f}%")
    
    # Try to fetch recent trades
    print("\n" + "=" * 70)
    print("RECENT TRADE HISTORY (Last 50)")
    print("=" * 70)
    
    try:
        trades = exchange.fetch_my_trades(limit=50)
        
        if trades:
            print(f"\n{'Time':<20} {'Symbol':<15} {'Side':<6} {'Amount':<10} {'Price':<12} {'Cost':<10}")
            print("-" * 70)
            
            for trade in trades[-20:]:  # Show last 20
                time = trade.get('datetime', '')[:16]
                symbol = trade.get('symbol', '')[:14]
                side = trade.get('side', '').upper()
                amount = float(trade.get('amount', 0))
                price = float(trade.get('price', 0))
                cost = float(trade.get('cost', 0))
                
                print(f"{time:<20} {symbol:<15} {side:<6} {amount:<10.4f} ${price:<11.2f} ${cost:<10.2f}")
        else:
            print("\nNo recent trades found or API access limited")
            
    except Exception as e:
        print(f"\nCould not fetch trade history: {e}")
    
    print("\n" + "=" * 70)
    print("STRATEGY ANALYSIS")
    print("=" * 70)
    
    # Analyze by symbol
    symbols = {}
    for pos in positions:
        contracts = float(pos.get('contracts', 0))
        if contracts == 0:
            continue
        symbol = pos.get('symbol', '')
        pnl = float(pos.get('unrealizedPnl', 0))
        symbols[symbol] = pnl
    
    if symbols:
        print("\nP&L by Symbol:")
        for symbol, pnl in sorted(symbols.items(), key=lambda x: x[1], reverse=True):
            status = "[WIN]" if pnl > 0 else "[LOSS]" if pnl < 0 else "[B/E]"
            print(f"   {status} {symbol:<20} ${pnl:+.2f}")
    
    print("\n" + "=" * 70)
    print("Report Complete")
    print("=" * 70)
    
except Exception as e:
    print(f"Error generating report: {e}")
    import traceback
    traceback.print_exc()
