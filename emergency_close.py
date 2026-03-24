import ccxt
import os
import sys
import io
from dotenv import load_dotenv
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'
load_dotenv(ENV_PATH)

API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
    }
})

# Fetch current positions
positions = exchange.fetch_positions()
active_positions = [p for p in positions if p['contracts'] and float(p['contracts']) != 0]

print(f"Found {len(active_positions)} active positions")

# Parse command line arguments
SYMBOLS_TO_CLOSE = None  # None = close all
if len(sys.argv) > 1:
    # Get symbol from command line (e.g., "NEARUSDT")
    target_symbol = sys.argv[1].upper()
    # Handle both "NEARUSDT" and "NEAR/USDT:USDT" formats
    SYMBOLS_TO_CLOSE = [target_symbol]
    if '/' not in target_symbol:
        # Convert "NEARUSDT" to "NEAR/USDT:USDT" format
        base = target_symbol.replace('USDT', '').replace('USD', '')
        SYMBOLS_TO_CLOSE.append(f"{base}/USDT:USDT")
    print(f"Target: Closing only {SYMBOLS_TO_CLOSE}")
else:
    print("WARNING: Closing ALL positions (no symbol specified)")

for pos in active_positions:
    symbol = pos['symbol']
    
    if SYMBOLS_TO_CLOSE and symbol not in SYMBOLS_TO_CLOSE:
        print(f"\n{symbol}: Keeping (not in close list)")
        continue
    
    side = pos['side']  # 'long' or 'short'
    contracts = float(pos['contracts'])
    
    print(f"\n{symbol}: {side.upper()} {contracts} - CLOSING")
    
    # Close by creating opposite market order
    close_side = 'sell' if side == 'long' else 'buy'
    
    try:
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=close_side,
            amount=contracts,
            params={'reduceOnly': True}
        )
        print(f"  [OK] Closed: {order['id']}")
    except Exception as e:
        print(f"  [ERR] Error: {e}")
