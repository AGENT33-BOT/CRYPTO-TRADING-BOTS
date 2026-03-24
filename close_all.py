import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'
load_dotenv(ENV_PATH)

session = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'), testnet=False)

symbol = sys.argv[1] if len(sys.argv) > 1 else None

if not symbol:
    print("Usage: python close_all.py [SYMBOL] or python close_all.py ALL")
    sys.exit(1)

# Get positions
positions = session.get_positions(category='linear', settleCoin='USDT')
open_positions = [p for p in positions['result']['list'] if float(p.get('size', 0)) > 0]

if symbol == "ALL":
    for pos in open_positions:
        sym = pos.get('symbol')
        side = pos.get('side')
        size = float(pos.get('size'))
        
        # Close opposite direction
        close_side = "Sell" if side == "Buy" else "Buy"
        
        print(f"Closing {sym}: {side} {size}...")
        try:
            result = session.place_order(
                category="linear",
                symbol=sym,
                side=close_side,
                order_type="Market",
                qty=size,
                reduceOnly=True
            )
            print(f"  Result: {result.get('retMsg', result)}")
        except Exception as e:
            print(f"  Error: {e}")
else:
    # Close specific symbol
    for pos in open_positions:
        if pos.get('symbol') == symbol:
            side = pos.get('side')
            size = float(pos.get('size'))
            close_side = "Sell" if side == "Buy" else "Buy"
            
            print(f"Closing {symbol}: {side} {size}...")
            try:
                result = session.place_order(
                    category="linear",
                    symbol=symbol,
                    side=close_side,
                    order_type="Market",
                    qty=size,
                    reduceOnly=True
                )
                print(f"Result: {result.get('retMsg', result)}")
            except Exception as e:
                print(f"Error: {e}")
            break
    else:
        print(f"No position found for {symbol}")
