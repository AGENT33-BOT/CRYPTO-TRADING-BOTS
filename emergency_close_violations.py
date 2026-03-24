#!/usr/bin/env python3
"""Emergency position closer - Close all positions violating $5 max loss rule"""
import ccxt
import time

print("=" * 70)
print("EMERGENCY: CLOSING POSITIONS VIOLATING $5 MAX LOSS RULE")
print("=" * 70)

# Initialize exchange
exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

MAX_LOSS_USD = 5.0

positions = exchange.fetch_positions()
active = [p for p in positions if float(p.get('contracts', 0)) != 0]

print(f"\nFound {len(active)} active positions")
print("-" * 70)

closed = []
for pos in active:
    symbol = pos['symbol']
    side = pos['side']
    size = abs(float(pos['contracts']))
    entry = float(pos.get('entryPrice', 0))
    pnl = float(pos.get('unrealizedPnl', 0))
    
    print(f"\n{symbol}: {side.upper()} {size} @ ${entry:.4f}")
    print(f"  Unrealized PnL: ${pnl:.2f}")
    
    # Check if violating $5 max loss
    if pnl < -MAX_LOSS_USD:
        print(f"  VIOLATION: Loss ${pnl:.2f} exceeds -${MAX_LOSS_USD} limit!")
        print(f"  CLOSING POSITION NOW...")
        
        try:
            if side == 'long':
                order = exchange.create_market_sell_order(symbol, size)
            else:
                order = exchange.create_market_buy_order(symbol, size)
            
            closed.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'pnl': pnl
            })
            print(f"  CLOSED! Order ID: {order['id']}")
            time.sleep(1)
        except Exception as e:
            print(f"  ERROR: {e}")
    else:
        print(f"  Within $5 limit. Keeping open.")

print("\n" + "=" * 70)
print("CLOSURE SUMMARY")
print("=" * 70)
if closed:
    print(f"Closed {len(closed)} position(s) violating $5 max loss:")
    for c in closed:
        print(f"  • {c['symbol']} {c['side'].upper()}: ${c['pnl']:.2f}")
else:
    print("No positions exceeded $5 loss limit.")

# Get final balance
balance = exchange.fetch_balance()
total = balance.get('USDT', {}).get('total', 0)
free = balance.get('USDT', {}).get('free', 0)
print(f"\nFinal Balance: ${total:.2f} USDT")
print(f"Available: ${free:.2f} USDT")
print("=" * 70)
