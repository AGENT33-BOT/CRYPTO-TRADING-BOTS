"""
TP/SL Monitor - Fixed check logic
"""
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

def check_positions():
    exchange = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY', 'KfmiIdWd16hG18v2O7'),
        'secret': os.getenv('BYBIT_API_SECRET', 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'),
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    positions = exchange.fetch_positions()
    
    print("=== POSITIONS CHECK ===")
    for p in positions:
        size = float(p.get('contracts', 0))
        if size > 0:
            symbol = p['symbol']
            side = p['side']
            entry = float(p.get('entryPrice', 0))
            
            # Get TP/SL from info dict (Bybit returns them here)
            info = p.get('info', {})
            tp = info.get('takeProfit', '0')
            sl = info.get('stopLoss', '0')
            trail = info.get('trailingStop', '0')
            
            print(f"{symbol} {side} @ ${entry:.4f}")
            print(f"  TP: {tp} | SL: {sl} | Trail: {trail}")
            
            if tp == '0' or sl == '0':
                print(f"  WARNING: Missing TP/SL!")
            else:
                print(f"  Status: OK")
            print()

if __name__ == "__main__":
    check_positions()