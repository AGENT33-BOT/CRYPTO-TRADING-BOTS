"""
Close profitable Alpaca positions and set TP/SL protection
"""
import os
from dotenv import load_dotenv
load_dotenv('.alpaca_env')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import ClosePositionRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce

client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)

# Get positions
positions = client.get_all_positions()

print("=" * 50)
print("ALPACA POSITIONS - ACTION PLAN")
print("=" * 50)

for pos in positions:
    symbol = pos.symbol
    qty = float(pos.qty)
    side = pos.side  # 'long' or 'short'
    entry = float(pos.avg_entry_price)
    current = float(pos.current_price)
    unrealized = float(pos.unrealized_pl)
    pct = float(pos.unrealized_plpc) * 100
    
    print(f"\n{symbol} | {side.upper()} | Qty: {qty}")
    print(f"  Entry: ${entry:.2f} | Current: ${current:.2f}")
    print(f"  P&L: ${unrealized:.2f} ({pct:.2f}%)")
    
    # Decision: Close if profit, set stop if loss
    if unrealized > 0:
        # Close profitable position
        print(f"  >> CLOSING (profit)")
        try:
            client.close_position(symbol)
            print(f"  [OK] CLOSED {symbol}")
        except Exception as e:
            print(f"  [X] Error closing {symbol}: {e}")
    else:
        # Set stop loss for losing position
        print(f"  >> Setting STOP LOSS")
        try:
            # Set stop loss at 2% below entry for long
            stop_price = entry * 0.98
            request = StopLossRequest(stop_price=str(stop_price), time_in_force=TimeInForce.GTC)
            client.set_stop_loss(symbol, request)
            print(f"  [OK] SL set at ${stop_price:.2f}")
        except Exception as e:
            print(f"  [X] Error setting SL for {symbol}: {e}")

print("\n" + "=" * 50)
print("COMPLETE")
print("=" * 50)
