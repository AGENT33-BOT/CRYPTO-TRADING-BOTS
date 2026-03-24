import os
from pathlib import Path

from dotenv import load_dotenv
from pybit.unified_trading import HTTP

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'

if not ENV_PATH.exists():
    raise SystemExit(f"Missing credentials file: {ENV_PATH}")

load_dotenv(ENV_PATH)
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

if not API_KEY or not API_SECRET:
    raise SystemExit("BYBIT_API_KEY or BYBIT_API_SECRET not set in .env.bybit")

session = HTTP(api_key=API_KEY, api_secret=API_SECRET, testnet=False)


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def close_position(symbol):
    """Close a position by placing a market order in the opposite direction"""
    try:
        # Get position info
        positions = session.get_positions(category='linear', symbol=symbol)
        if positions.get('retCode') != 0:
            return f"Error getting position: {positions.get('retMsg')}"
        
        pos_list = positions['result']['list']
        if not pos_list or safe_float(pos_list[0].get('size')) == 0:
            return f"No open position for {symbol}"
        
        pos = pos_list[0]
        side = pos.get('side')  # Buy or Sell
        size = pos.get('size')
        
        # Determine close side (opposite of current position)
        close_side = "Sell" if side == "Buy" else "Buy"
        
        print(f"  Closing {symbol} {side} position ({size} units) with {close_side} market order...")
        
        # Place market order to close
        order = session.place_order(
            category='linear',
            symbol=symbol,
            side=close_side,
            orderType='Market',
            qty=size,
            reduceOnly=True
        )
        
        if order.get('retCode') == 0:
            return f"[OK] Closed {symbol} {side} position"
        else:
            return f"[FAIL] Failed: {order.get('retMsg')}"
            
    except Exception as exc:
        return f"[ERROR] Exception: {exc}"


def main():
    print("=" * 50)
    print("CLOSING WRONG-DIRECTION SHORTS")
    print("Fear & Greed: 12/100 (Extreme Fear) = LONG Bias")
    print("=" * 50)
    
    # Close ALL SHORTS (wrong direction during Extreme Fear = LONG bias only)
    wrong_shorts = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
    
    for symbol in wrong_shorts:
        print(f"\n[ACTION] Closing {symbol.replace('USDT', '')} SHORT - wrong direction for LONG bias")
        result = close_position(symbol)
        print(f"  {result}")
    
    print("\n" + "=" * 50)
    print("Remaining positions should be LONG only")
    print("=" * 50)


if __name__ == '__main__':
    main()
