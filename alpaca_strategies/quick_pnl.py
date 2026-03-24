from alpaca_api import AlpacaAPI
import os
api = AlpacaAPI(
    api_key=os.getenv('ALPACA_API_KEY'),
    api_secret=os.getenv('ALPACA_API_SECRET'),
    paper=True
)
account = api.get_account()
print(f"Account Value: ${float(account.get('portfolio_value', 0)):,.2f}")
print(f"Cash: ${float(account.get('cash', 0)):,.2f}")
print(f"Buying Power: ${float(account.get('buying_power', 0)):,.2f}")

positions = api.get_positions()
print(f"\nPositions: {len(positions)}")
if positions:
    print('-' * 50)
    total_pnl = 0
    for pos in positions:
        sym = pos.get('symbol', 'N/A')
        qty = pos.get('qty', 0)
        avg = float(pos.get('avg_entry_price', 0))
        cur = float(pos.get('current_price', 0))
        pnl = float(pos.get('unrealized_pl', 0))
        pnl_pct = float(pos.get('unrealized_plpc', 0)) * 100
        total_pnl += pnl
        print(f"{sym}: {qty} shares | Avg: ${avg:.2f} | Cur: ${cur:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
    print('-' * 50)
    print(f"TOTAL UNREALIZED PnL: ${total_pnl:,.2f}")
else:
    print("No open positions yet - orders pending market open")
