import ccxt
import os

exchange = ccxt.bybit({
    'apiKey': os.environ['BYBIT_API_KEY'],
    'secret': os.environ['BYBIT_API_SECRET'],
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print("=== RECENT TRADES ===")
try:
    trades = exchange.fetch_my_trades(limit=50)
    for t in trades[-20:]:
        side = 'BUY ' if t['side']=='buy' else 'SELL'
        print(f"{t['datetime'][:19]} | {t['symbol']:15} | {side} | {t['amount']:8.4f} @ ${t['price']:.4f}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== CLOSED PNL ===")
try:
    closed_pnl = exchange.fetch_closed_orders(limit=20)
    for o in closed_pnl[-10:]:
        if o.get('status') == 'closed':
            pnl = o.get('info', {}).get('closedPnl', 'N/A')
            print(f"{o['symbol']} | {o['side']} | PnL: {pnl}")
except Exception as e:
    print(f"Error: {e}")
