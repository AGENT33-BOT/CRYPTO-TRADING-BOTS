#!/usr/bin/env python3
"""Close losing Alpaca positions - keep winners only"""
import sys
import os
from pathlib import Path

# Load environment
def load_env(filepath):
    if Path(filepath).exists():
        with open(filepath) as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 2:
                os.environ['APCA_API_KEY_ID'] = lines[0].strip()
                os.environ['APCA_API_SECRET_KEY'] = lines[1].strip()

# Try multiple locations for .alpaca_env
env_paths = [
    Path.cwd() / ".alpaca_env",
    Path(__file__).parent / ".alpaca_env",
    Path(__file__).parent.parent / ".alpaca_env",
]

for env_path in env_paths:
    if env_path.exists():
        load_env(env_path)
        break

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except ImportError:
    print("[ERROR] alpaca-py not installed")
    sys.exit(1)

api_key = os.getenv('APCA_API_KEY_ID')
secret_key = os.getenv('APCA_API_SECRET_KEY')

if not api_key or not secret_key:
    print("[ERROR] API keys not found")
    sys.exit(1)

# Connect to Alpaca
client = TradingClient(api_key, secret_key, paper=True)

# Positions to CLOSE (the 7 losers)
LOSERS = ['SPY', 'VTI', 'DBC', 'QQQ', 'IWM', 'GLD', 'XLI']

print("=" * 60)
print("CLOSING LOSING POSITIONS - Agent Alpaca")
print("=" * 60)

# Get all positions
positions = client.get_all_positions()

closed = []
kept = []

for pos in positions:
    symbol = pos.symbol
    qty = float(pos.qty)
    side = "LONG" if qty > 0 else "SHORT"
    pnl = float(pos.unrealized_pl)
    
    if symbol in LOSERS:
        # Close this position
        try:
            order_side = OrderSide.SELL if qty > 0 else OrderSide.BUY
            order = MarketOrderRequest(
                symbol=symbol,
                qty=abs(qty),
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            client.submit_order(order)
            closed.append({
                'symbol': symbol,
                'side': side,
                'qty': abs(qty),
                'pnl': pnl
            })
            print(f"[CLOSED] {symbol} | {side} {abs(qty):.2f} | P&L: ${pnl:+.2f}")
        except Exception as e:
            print(f"[ERROR] closing {symbol}: {e}")
    else:
        kept.append({
            'symbol': symbol,
            'side': side,
            'qty': abs(qty),
            'pnl': pnl
        })
        print(f"[KEEPING] {symbol} | {side} {abs(qty):.2f} | P&L: ${pnl:+.2f}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\nClosed: {len(closed)} positions")
total_closed_pnl = sum(p['pnl'] for p in closed)
print(f"Total P&L from closed: ${total_closed_pnl:,.2f}")

print(f"\nKept: {len(kept)} positions")
total_kept_pnl = sum(p['pnl'] for p in kept)
print(f"Total P&L from kept: ${total_kept_pnl:,.2f}")

print("\nDone. Losers closed, winners preserved.")
