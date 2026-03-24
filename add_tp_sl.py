"""
Add TP/SL to existing Bybit positions
"""
import ccxt
import sys

TP_PCT = 0.02  # 2% take profit
SL_PCT = 0.015  # 1.5% stop loss

def add_tp_sl():
    exchange = ccxt.bybit({
        'apiKey': 'bsK06QDhsagOWwFsXQ',
        'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    try:
        positions = exchange.fetch_positions()
        
        for p in positions:
            contracts = float(p.get('contracts', 0))
            if contracts == 0:
                continue
                
            symbol = p['symbol']
            side = p['side']
            entry = float(p['entryPrice'])
            
            # Calculate TP/SL
            if side == 'short':
                tp_price = round(entry * (1 - TP_PCT), 4)
                sl_price = round(entry * (1 + SL_PCT), 4)
                sl_trigger_dir = 'ascending'  # Price going up triggers SL for shorts
            else:
                tp_price = round(entry * (1 + TP_PCT), 4)
                sl_price = round(entry * (1 - SL_PCT), 4)
                sl_trigger_dir = 'descending'  # Price going down triggers SL for longs
            
            print(f"\n{symbol} {side.upper()}")
            print(f"  Entry: ${entry}")
            print(f"  TP: ${tp_price} ({TP_PCT*100:.1f}%)")
            print(f"  SL: ${sl_price} ({SL_PCT*100:.1f}%)")
            
            try:
                # Use implicit API
                params = {
                    'category': 'linear',
                    'symbol': symbol.replace('/', '').replace(':USDT', ''),
                    'takeProfit': str(tp_price),
                    'stopLoss': str(sl_price),
                    'tpTriggerBy': 'LastPrice',
                    'slTriggerBy': 'LastPrice',
                    'tpslMode': 'Full',
                }
                result = exchange.private_post_v5_position_trading_stop(params)
                print(f"  [OK] TP/SL set: {result}")
            except Exception as e:
                print(f"  [ERR API] {e}")
        
        print("\n=== Done ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    add_tp_sl()
