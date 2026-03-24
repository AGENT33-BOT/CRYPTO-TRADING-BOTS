import ccxt
import json
from datetime import datetime

# Initialize exchange with correct credentials
exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'adjustForTimeDifference': True,
    }
})
exchange.set_sandbox_mode(False)

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

try:
    # Load markets
    exchange.load_markets()
    
    # Get positions
    positions = exchange.fetch_positions()
    open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
    
    log(f"Found {len(open_positions)} open positions")
    
    # Check LTC position
    ltc_pos = None
    for p in open_positions:
        symbol = p['symbol']
        side = p['side']
        size = float(p.get('contracts', 0))
        entry = float(p.get('entryPrice', 0))
        
        log(f"{symbol} {side.upper()}: {size} contracts @ ${entry:.4f}")
        
        if 'LTC' in symbol:
            ltc_pos = p
    
    # Set TP/SL for LTC
    if ltc_pos:
        symbol = ltc_pos['symbol']
        side = ltc_pos['side']
        size = float(ltc_pos.get('contracts', 0))
        entry = float(ltc_pos.get('entryPrice', 0))
        
        log(f"Setting TP/SL for {symbol} {side.upper()}")
        
        # Calculate TP/SL prices
        if side == 'long':
            tp_price = entry * 1.025  # 2.5% TP
            sl_price = entry * 0.985  # 1.5% SL
        else:
            tp_price = entry * 0.975  # 2.5% TP
            sl_price = entry * 1.015  # 1.5% SL
        
        log(f"Entry: ${entry:.4f}")
        log(f"TP: ${tp_price:.4f} (+2.5%)")
        log(f"SL: ${sl_price:.4f} (-1.5%)")
        
        # Set TP/SL using Bybit's trading-stop endpoint
        try:
            response = exchange.private_post_v5_position_trading_stop({
                'category': 'linear',
                'symbol': symbol.replace('/', '').replace(':USDT', ''),
                'takeProfit': str(round(tp_price, 2)),
                'stopLoss': str(round(sl_price, 2)),
                'tpTriggerBy': 'MarkPrice',
                'slTriggerBy': 'MarkPrice',
                'tpslMode': 'Full',
            })
            
            if response.get('retCode') == 0:
                log(f"SUCCESS: TP/SL set for {symbol}")
                log(f"  TP: ${tp_price:.2f}")
                log(f"  SL: ${sl_price:.2f}")
            else:
                log(f"ERROR: {response.get('retMsg')}")
                    
        except Exception as e2:
            log(f"ERROR setting TP/SL: {e2}")
            import traceback
            traceback.print_exc()
    else:
        log("No LTC position found")
        
except Exception as e:
    log(f"Error: {e}")
    import traceback
    traceback.print_exc()
