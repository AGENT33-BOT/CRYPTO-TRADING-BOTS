import ccxt
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
    exchange.load_markets()
    
    # Get positions
    positions = exchange.fetch_positions()
    open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
    
    for p in open_positions:
        symbol = p['symbol']
        side = p['side']
        size = float(p.get('contracts', 0))
        entry = float(p.get('entryPrice', 0))
        
        # Check TP/SL
        tp = p.get('takeProfitPrice') or p.get('takeProfit')
        sl = p.get('stopLossPrice') or p.get('stopLoss')
        
        has_tp = tp and float(tp) > 0
        has_sl = sl and float(sl) > 0
        
        # Set TP/SL for positions missing them
        if not (has_tp and has_sl):
            log(f"Setting TP/SL for {symbol} {side.upper()}...")
            
            # Calculate TP/SL prices
            if side == 'long':
                tp_price = entry * 1.025  # 2.5% TP
                sl_price = entry * 0.985  # 1.5% SL
            else:
                tp_price = entry * 0.975  # 2.5% TP
                sl_price = entry * 1.015  # 1.5% SL
            
            try:
                response = exchange.private_post_v5_position_trading_stop({
                    'category': 'linear',
                    'symbol': symbol.replace('/', '').replace(':USDT', ''),
                    'takeProfit': str(round(tp_price, 4 if tp_price < 1 else 2)),
                    'stopLoss': str(round(sl_price, 4 if sl_price < 1 else 2)),
                    'tpTriggerBy': 'MarkPrice',
                    'slTriggerBy': 'MarkPrice',
                    'tpslMode': 'Full',
                })
                
                if response.get('retCode') == 0:
                    log(f"SUCCESS: {symbol} TP/SL set | TP: ${tp_price:.4f} | SL: ${sl_price:.4f}")
                else:
                    log(f"ERROR: {response.get('retMsg')}")
                        
            except Exception as e:
                log(f"ERROR: {e}")
        else:
            log(f"{symbol}: Already has TP/SL - SKIPPING")
    
    log("All positions checked!")
        
except Exception as e:
    log(f"Error: {e}")
    import traceback
    traceback.print_exc()
