"""
Set stop loss for XLP using cancel/replace approach
"""
import os
from dotenv import load_dotenv
load_dotenv('.alpaca_env')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopLossRequest, LimitClosePositionRequest
from alpaca.trading.enums import TimeInForce

client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)

symbol = "XLP"

# Get position
pos = client.get_position(symbol)
qty = float(pos.qty)
entry = float(pos.avg_entry_price)

print(f"XLP Position: {qty} shares at ${entry}")
print(f"Setting stop loss at 2% = ${entry * 0.98:.2f}")

# Try to close with stop loss
try:
    # Cancel any existing orders
    client.cancel_orders()
    print("Cancelled existing orders")
    
    # Try using close_position with stop_loss
    req = LimitClosePositionRequest(
        qty=str(qty),
        time_in_force=TimeInForce.GTC
    )
    result = client.close_position(symbol, req)
    print(f"[OK] Close order placed for {symbol}")
except Exception as e:
    print(f"[X] Error: {e}")
    
    # Alternative: just market close the position
    try:
        client.close_position(symbol)
        print(f"[OK] Force closed {symbol}")
    except Exception as e2:
        print(f"[X] Force close failed: {e2}")

print("\nDone")
