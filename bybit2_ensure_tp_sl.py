"""
Bybit2 TP/SL Guardian
Checks all Bybit2 positions every minute and ensures TP/SL is set.
"""

import ccxt
import json
import os
import sys
from datetime import datetime
import requests

# Telegram notification
TELEGRAM_BOT_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

LOG_FILE = 'bybit2_ensure_tp_sl.log'
FIXED_POSITIONS_FILE = 'bybit2_tp_sl_fixed.json'

# Default risk parameters
DEFAULT_TP_PCT = 0.010  # 1.0%
DEFAULT_SL_PCT = 0.005  # 0.5%

# BYBIT2 API CREDENTIALS
BYBIT2_API_KEY = 'aLz3ySrF9kMZubmqDR'
BYBIT2_API_SECRET = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[BYBIT2-TP/SL] {timestamp} - {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def get_exchange():
    """Initialize Bybit2 exchange"""
    try:
        exchange = ccxt.bybit({
            'apiKey': BYBIT2_API_KEY,
            'secret': BYBIT2_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': True,
            }
        })
        exchange.set_sandbox_mode(False)
        exchange.load_markets()
        return exchange
    except Exception as e:
        log(f"[ERR] Exchange init error: {e}")
        return None

def send_telegram_alert(message):
    """Send alert to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        log(f"[WARN] Telegram send failed: {e}")

def load_fixed_positions():
    """Load positions we've already fixed"""
    try:
        if os.path.exists(FIXED_POSITIONS_FILE):
            with open(FIXED_POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_fixed_positions(fixed):
    """Save fixed positions record"""
    try:
        with open(FIXED_POSITIONS_FILE, 'w') as f:
            json.dump(fixed, f, indent=2)
    except Exception as e:
        log(f"[WARN] Error saving: {e}")

def set_position_tp_sl(exchange, position):
    """Set TP/SL for a position"""
    try:
        symbol = position['symbol']
        side = position['side']
        
        entry_price = float(position.get('entryPrice', 0))
        if entry_price == 0:
            entry_price = float(position.get('markPrice', 0))
        
        if entry_price == 0:
            log(f"[ERR] No entry price for {symbol}")
            return False
        
        # Get market precision
        market = exchange.market(symbol)
        price_precision = market.get('precision', {}).get('price', 4)
        if isinstance(price_precision, float):
            price_precision = len(str(price_precision).split('.')[-1]) if '.' in str(price_precision) else 4
        price_precision = max(2, min(price_precision, 8))  # Clamp between 2-8 decimals
        
        # Calculate TP/SL
        if side == 'long':
            tp_price = round(entry_price * 1.010, price_precision)
            sl_price = round(entry_price * 0.995, price_precision)
        else:
            tp_price = round(entry_price * 0.990, price_precision)
            sl_price = round(entry_price * 1.005, price_precision)
        
        log(f"[INFO] Setting TP/SL for {symbol} {side.upper()}")
        log(f"       Entry: ${entry_price:.2f} | TP: ${tp_price} | SL: ${sl_price}")
        
        params = {
            'category': 'linear',
            'symbol': market['id'],
            'takeProfit': str(tp_price),
            'stopLoss': str(sl_price),
            'tpTriggerBy': 'LastPrice',
            'slTriggerBy': 'LastPrice',
        }
        
        response = exchange.private_post_v5_position_trading_stop(params)
        
        ret_code = response.get('retCode')
        ret_msg = response.get('retMsg', '')
        
        # retCode 0 means success, even if retMsg is "OK"
        if ret_code == 0:
            log(f"[OK] TP/SL set for {symbol}")
            return {
                'symbol': symbol,
                'side': side.upper(),
                'entry_price': entry_price,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'fixed_at': datetime.now().isoformat()
            }
        else:
            log(f"[ERR] API error {ret_code}: {ret_msg}")
            return False
        
    except Exception as e:
        log(f"[ERR] Failed to set TP/SL: {e}")
        return False

def check_and_fix_positions():
    """Main function"""
    log("=" * 50)
    log("BYBIT2 TP/SL Guardian Check")
    
    exchange = get_exchange()
    if not exchange:
        log("[ERR] Could not connect")
        return False
    
    try:
        positions = exchange.fetch_positions()
        log(f"[INFO] Found {len(positions)} total positions")
        
        fixed_positions = load_fixed_positions()
        positions_fixed = []
        positions_checked = 0
        
        for pos in positions:
            size = float(pos.get('contracts', 0))
            if size == 0:
                continue
            
            positions_checked += 1
            symbol = pos['symbol']
            side = pos['side']
            
            # Check existing TP/SL
            has_tp = pos.get('takeProfitPrice') and float(pos.get('takeProfitPrice', 0)) > 0
            has_sl = pos.get('stopLossPrice') and float(pos.get('stopLossPrice', 0)) > 0
            
            position_key = f"{symbol}_{side}_{size}"
            already_fixed = position_key in fixed_positions
            
            log(f"[CHECK] {symbol} {side.upper()} | Has TP: {has_tp} | Has SL: {has_sl}")
            
            if has_tp and has_sl:
                log(f"  [OK] Already set")
                continue
            
            if already_fixed:
                log(f"  [INFO] Already fixed")
                continue
            
            log(f"  [ACTION] Setting TP/SL...")
            result = set_position_tp_sl(exchange, pos)
            
            if result:
                positions_fixed.append(result)
                fixed_positions[position_key] = result
        
        save_fixed_positions(fixed_positions)
        
        log(f"[SUMMARY] Checked {positions_checked}, Fixed {len(positions_fixed)}")
        
        if positions_fixed:
            alert_msg = "🚨 *BYBIT2 TP/SL ALERT* 🚨\n\n"
            alert_msg += f"Fixed {len(positions_fixed)} position(s):\n\n"
            for p in positions_fixed:
                alert_msg += f"📊 *{p['symbol']}* ({p['side']})\n"
                alert_msg += f"   TP: `${p['tp_price']:.2f}` | SL: `${p['sl_price']:.2f}`\n\n"
            send_telegram_alert(alert_msg)
        
        return True
        
    except Exception as e:
        log(f"[ERR] Error: {e}")
        return False

if __name__ == "__main__":
    try:
        check_and_fix_positions()
    except KeyboardInterrupt:
        log("[INFO] Interrupted")
