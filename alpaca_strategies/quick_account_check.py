#!/usr/bin/env python3
"""Quick Alpaca account status check"""
import sys
import os

# Load environment
from pathlib import Path
def load_env(filepath):
    if Path(filepath).exists():
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env('.alpaca_env')

try:
    from alpaca.trading.client import TradingClient
except ImportError:
    print("[ERROR] alpaca-py not installed")
    print("Run: pip install alpaca-py")
    sys.exit(1)

api_key = os.getenv('APCA_API_KEY_ID')
secret_key = os.getenv('APCA_API_SECRET_KEY')

if not api_key or not secret_key:
    print("[ERROR] API keys not found in .alpaca_env")
    sys.exit(1)

# Connect to Alpaca
client = TradingClient(api_key, secret_key, paper=True)

# Get account info
account = client.get_account()
print("=" * 60)
print("ALPACA PAPER TRADING ACCOUNT - Agent Alpaca")
print("=" * 60)
print(f"Account ID: {account.id}")
print(f"Status: {account.status}")
print(f"Currency: {account.currency}")
print()
print("PORTFOLIO VALUE")
print("-" * 40)
print(f"  Equity:        ${float(account.equity):,.2f}")
print(f"  Cash:          ${float(account.cash):,.2f}")
print(f"  Buying Power:  ${float(account.buying_power):,.2f}")
print(f"  Long Value:    ${float(account.long_market_value):,.2f}")
print(f"  Short Value:   ${float(account.short_market_value):,.2f}")
print()
print("TODAY'S P&L")
print("-" * 40)
day_pl = float(account.equity) - float(account.last_equity)
print(f"  Day P&L:       ${day_pl:,.2f}")
day_return = (day_pl / float(account.last_equity) * 100) if float(account.last_equity) > 0 else 0
print(f"  Day Return:    {day_return:+.2f}%")
print()

# Get positions
positions = client.get_all_positions()
print(f"OPEN POSITIONS ({len(positions)})")
print("-" * 40)
if positions:
    total_pnl = 0
    for pos in positions:
        pnl = float(pos.unrealized_pl)
        total_pnl += pnl
        pnl_pct = float(pos.unrealized_plpc) * 100
        side = "LONG" if float(pos.qty) > 0 else "SHORT"
        print(f"  {pos.symbol:6} | {side:5} | Qty: {abs(float(pos.qty)):,.2f} | P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
    print("-" * 40)
    print(f"  Total Unrealized P&L: ${total_pnl:,.2f}")
else:
    print("  No open positions")
print()

# Get recent orders
print("RECENT ORDERS (Last 5)")
print("-" * 40)
try:
    orders = client.get_orders()
    if orders:
        for order in orders[:5]:
            price = order.filled_avg_price or order.limit_price or "MKT"
            print(f"  {order.symbol:6} | {order.side:4} | {order.qty} @ {price} | {order.status}")
    else:
        print("  No recent orders")
except:
    print("  Could not fetch orders")

print("=" * 60)
