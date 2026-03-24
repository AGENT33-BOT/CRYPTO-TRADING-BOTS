from bybit_api import BybitAPI
import json

b = BybitAPI()
bal = b.get_balance()
pos = b.get_positions()

total_pnl = sum(float(p.get('unrealisedPnl', 0)) for p in pos)

print(f"Balance: {bal:.2f} USDT")
print(f"Positions: {len(pos)}")
print(f"Total Unrealized PnL: {total_pnl:.2f} USDT")
for p in pos:
    print(f"  {p['symbol']}: {p['side']} @ {float(p['entryPrice']):.4f} | PnL: {float(p.get('unrealisedPnl', 0)):.2f}")
