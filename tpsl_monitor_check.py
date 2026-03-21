"""
TP/SL Monitor - Checks every minute for positions without TP/SL
Automatically adds TP/SL if missing
"""
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print(f"Telegram error: {e}")

def set_tpsl(exchange, symbol, side, entry_price):
    """Set TP/SL + Trailing Stop for a position automatically"""
    try:
        # Get current price - convert NEAR/USDT:USDT to NEAR/USDT
        ticker = exchange.fetch_ticker(symbol.split(':')[0])
        current_price = ticker['last']
        
        if side == 'long':
            # For long: TP above entry, SL below entry
            tp_price = round(current_price * 1.025, 4)  # 2.5% profit
            sl_price = round(current_price * 0.975, 4)  # 2.5% loss
            trailing = round(current_price * 0.01, 4)   # 1% trailing
            active_price = round(current_price * 1.01, 4)  # Activate after 1% profit
        else:  # short
            # For short: TP below entry, SL above entry
            tp_price = round(current_price * 0.975, 4)
            sl_price = round(current_price * 1.025, 4)
            trailing = round(current_price * 0.01, 4)
            active_price = round(current_price * 0.99, 4)  # Activate after 1% profit
        
        # Get precision
        sym_for_prec = symbol.replace(':USDT', '')
        tp_str = str(exchange.price_to_precision(sym_for_prec, tp_price))
        sl_str = str(exchange.price_to_precision(sym_for_prec, sl_price))
        trail_str = str(exchange.price_to_precision(sym_for_prec, trailing))
        active_str = str(exchange.price_to_precision(sym_for_prec, active_price))
        
        # Set TP/SL with trailing stop (activates after 1% profit)
        bybit_symbol = symbol.replace('/USDT:USDT', 'USDT')
        params = {
            'symbol': bybit_symbol,
            'category': 'linear',
            'takeProfit': tp_str,
            'stopLoss': sl_str,
            'trailingStop': trail_str,
            'activePrice': active_str,  # Trailing starts after 1% profit
            'tpTriggerBy': 'LastPrice',
            'slTriggerBy': 'LastPrice',
            'tpslMode': 'Full',
        }
        
        response = exchange.privatePostV5PositionTradingStop(params)
        
        if response.get('retCode') == 0:
            return True, tp_price, sl_price, trailing
        else:
            return False, response.get('retMsg', 'Unknown error'), 0, 0
    except Exception as e:
        return False, str(e), 0, 0

def check_positions():
    exchange = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY'),
        'secret': os.getenv('BYBIT_API_SECRET'),
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    positions = exchange.fetch_positions()
    
    alert_msg = "AUTO TP/SL FIX:\n\n"
    fixed_count = 0
    
    for p in positions:
        if float(p.get('contracts', 0)) > 0:
            info = p.get('info', {})
            tp = info.get('takeProfit')
            sl = info.get('stopLoss')
            
            # Check if TP/SL is missing or zero
            if not tp or tp == '0' or not sl or sl == '0':
                symbol = p['symbol']
                side = p['side']
                entry = float(p.get('entryPrice', 0))
                
                print(f"Found {symbol} {side} without TP/SL - Auto fixing...")
                
                success, tp_price, sl_price, trailing = set_tpsl(exchange, symbol, side, entry)
                
                if success:
                    alert_msg += f"OK: {symbol} {side}\n"
                    alert_msg += f"  TP: {tp_price} | SL: {sl_price} | Trail: {trailing}\n\n"
                    fixed_count += 1
                    print(f"  Fixed: TP={tp_price}, SL={sl_price}, Trail={trailing}")
                else:
                    alert_msg += f"FAIL: {symbol} - {tp_price}\n\n"
                    print(f"  Failed: {tp_price}")
    
    if fixed_count > 0:
        send_telegram(alert_msg)
        print(f"Fixed {fixed_count} positions")
    elif "FAIL:" in alert_msg:
        send_telegram(alert_msg)
        print("Failed - Alert sent")
    else:
        print("All positions have TP/SL set - OK")

if __name__ == "__main__":
    check_positions()
