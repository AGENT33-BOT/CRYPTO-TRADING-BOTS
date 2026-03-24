"""
Dollar Profit Taker - Closes position when $1-2 profit reached
Runs continuously to monitor all positions
"""

import ccxt
import time
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# All trading pairs
SYMBOLS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT', 'MATIC/USDT:USDT',
    'SHIB1000/USDT:USDT', 'TRX/USDT:USDT', 'FIL/USDT:USDT', 'ALGO/USDT:USDT',
    'VET/USDT:USDT', 'AAVE/USDT:USDT', 'SUSHI/USDT:USDT', 'INJ/USDT:USDT',
    'TIA/USDT:USDT', 'SEI/USDT:USDT', 'STX/USDT:USDT', 'ORDI/USDT:USDT',
    'WLD/USDT:USDT', 'BEAM/USDT:USDT', 'IMX/USDT:USDT', 'RNDR/USDT:USDT',
    'AR/USDT:USDT', 'BLUR/USDT:USDT', 'PEPE1000/USDT:USDT', 'WIF/USDT:USDT',
    'BONK/USDT:USDT', 'FET/USDT:USDT', 'AGIX/USDT:USDT', 'GRT/USDT:USDT'
]

# CONFIGURATION
MIN_PROFIT_USD = 1.0      # Close when $1 profit reached
MAX_PROFIT_USD = 2.0      # Or when $2 profit reached (take the profit!)
CHECK_INTERVAL = 10       # Check every 10 seconds

# Track which positions we've notified about
profit_notified = {}

print("=" * 70)
print("DOLLAR PROFIT TAKER - Close at $1-2 Profit")
print(f"Monitoring {len(SYMBOLS)} pairs every {CHECK_INTERVAL}s")
print("=" * 70)

try:
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        for symbol in SYMBOLS:
            try:
                positions = exchange.fetch_positions([symbol])
                if not positions or len(positions) == 0:
                    # Position closed, remove from tracking
                    if symbol in profit_notified:
                        del profit_notified[symbol]
                    continue
                
                pos = positions[0]
                contracts = float(pos.get('contracts', 0))
                
                if contracts <= 0:
                    if symbol in profit_notified:
                        del profit_notified[symbol]
                    continue
                
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                side = pos['side'].upper()
                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                
                if entry <= 0:
                    continue
                
                # Calculate PnL %
                if side == 'LONG':
                    pnl_pct = ((mark - entry) / entry) * 100
                else:
                    pnl_pct = ((entry - mark) / entry) * 100
                
                # Check if $1-2 profit reached
                if unrealized_pnl >= MIN_PROFIT_USD:
                    print(f"\n{'='*70}")
                    print(f"💰 PROFIT TARGET REACHED - {symbol}")
                    print(f"{'='*70}")
                    print(f"  Time: {timestamp}")
                    print(f"  Side: {side}")
                    print(f"  Entry: ${entry:.4f}")
                    print(f"  Mark: ${mark:.4f}")
                    print(f"  PnL: ${unrealized_pnl:.2f} (+{pnl_pct:.2f}%)")
                    print(f"  Size: {contracts}")
                    print(f"{'='*70}")
                    print(f"  🎯 CLOSING POSITION - Taking ${unrealized_pnl:.2f} profit!")
                    print(f"{'='*70}")
                    
                    # Close entire position
                    close_side = 'sell' if side == 'LONG' else 'buy'
                    order = exchange.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=contracts,
                        params={'reduceOnly': True}
                    )
                    
                    print(f"  ✅ POSITION CLOSED - Profit locked in!")
                    print(f"  Waiting for next opportunity...")
                    print(f"{'='*70}\n")
                    
                    # Remove from tracking
                    if symbol in profit_notified:
                        del profit_notified[symbol]
                    
                    # Small delay between closes
                    time.sleep(1)
                
                # Show progress for profitable positions (optional)
                elif unrealized_pnl > 0.5 and symbol not in profit_notified:
                    print(f"[{timestamp}] {symbol}: +${unrealized_pnl:.2f} ({pnl_pct:.2f}%) - approaching $1 target...")
                    profit_notified[symbol] = True
                
                # Reset notification if profit drops
                elif unrealized_pnl < 0.3 and symbol in profit_notified:
                    del profit_notified[symbol]
                    
            except Exception as e:
                if 'empty' not in str(e).lower():
                    pass  # Silent on empty position errors
        
        time.sleep(CHECK_INTERVAL)
        
except KeyboardInterrupt:
    print("\nDollar Profit Taker stopped")
except Exception as e:
    print(f"\nError: {e}")
    time.sleep(5)
