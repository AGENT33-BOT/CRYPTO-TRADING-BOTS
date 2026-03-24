"""
Crypto.com AI Agent Trading Bot
Uses Crypto.com AI Agent Service APIs
"""

import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime
import os

# ============ CONFIGURATION ============
CONFIG = {
    'base_url': 'https://agent-api.crypto.com',  # AI Agent API endpoint
    'symbols': [
        'BTCUSD-PERP',
        'ETHUSD-PERP', 
        'SOLUSD-PERP',
        'XRPUSD-PERP',
        'LINKUSD-PERP',
        'AVAXUSD-PERP',
        'DOGEUSD-PERP',
        'MATICUSD-PERP',
    ],
    'position_size': 50,         # USD per trade
    'max_positions': 3,
    'leverage': 3,
    'profit_target': 0.008,      # 0.8%
    'stop_loss': 0.005,          # 0.5%
}

LOG_FILE = 'crypto_com_ai_agent.log'
POSITIONS_FILE = 'crypto_com_ai_positions.json'
CREDS_FILE = 'crypto_com_credentials.json'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    except:
        pass

def load_credentials():
    """Load AI Agent SDK credentials"""
    try:
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"[ERR] Could not load credentials: {e}")
    
    # Fallback to environment
    return {
        'api_key': os.environ.get('CRYPTOCOM_API_KEY', ''),
        'api_secret': os.environ.get('CRYPTOCOM_API_SECRET', ''),
    }

def generate_signature(secret, timestamp, method, path, body=''):
    """Generate HMAC signature for AI Agent API"""
    message = f"{timestamp}{method.upper()}{path}{body}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def make_request(method, path, body=None):
    """Make authenticated request to AI Agent API"""
    creds = load_credentials()
    api_key = creds.get('api_key', '')
    api_secret = creds.get('api_secret', '')
    
    if not api_key or not api_secret:
        log("[ERR] API credentials not configured")
        return None
    
    timestamp = str(int(time.time() * 1000))
    body_str = json.dumps(body) if body else ''
    
    signature = generate_signature(api_secret, timestamp, method, path, body_str)
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
        'X-Signature': signature,
        'X-Timestamp': timestamp,
    }
    
    url = f"{CONFIG['base_url']}{path}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=body_str, timeout=30)
        else:
            log(f"[ERR] Unsupported method: {method}")
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            log(f"[ERR] API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        log(f"[ERR] Request failed: {e}")
        return None

def get_account_balance():
    """Get account balance"""
    result = make_request('GET', '/v1/account/balance')
    if result and result.get('code') == 0:
        return result.get('data', {})
    return None

def get_positions():
    """Get open positions"""
    result = make_request('GET', '/v1/positions')
    if result and result.get('code') == 0:
        return result.get('data', {}).get('positions', [])
    return []

def get_mark_price(symbol):
    """Get current mark price"""
    result = make_request('GET', f'/v1/mark-price/{symbol}')
    if result and result.get('code') == 0:
        return result.get('data', {}).get('markPrice', 0)
    return 0

def place_order(symbol, side, size, order_type='MARKET', price=None, stop_price=None):
    """Place an order"""
    body = {
        'symbol': symbol,
        'side': side.upper(),  # BUY or SELL
        'type': order_type.upper(),
        'size': str(size),
        'leverage': CONFIG['leverage'],
    }
    
    if price and order_type.upper() == 'LIMIT':
        body['price'] = str(price)
    
    if stop_price:
        body['stopPrice'] = str(stop_price)
    
    result = make_request('POST', '/v1/orders', body)
    
    if result and result.get('code') == 0:
        log(f"[OK] Order placed: {side} {size} {symbol}")
        return result.get('data', {})
    else:
        log(f"[ERR] Order failed: {result}")
        return None

def close_position(symbol):
    """Close a position"""
    body = {
        'symbol': symbol,
        'type': 'MARKET',
    }
    result = make_request('POST', '/v1/positions/close', body)
    if result and result.get('code') == 0:
        log(f"[OK] Position closed: {symbol}")
        return True
    return False

def load_positions():
    """Load tracked positions from file"""
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_positions(positions):
    """Save tracked positions to file"""
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2, default=str)
    except Exception as e:
        log(f"[ERR] Could not save positions: {e}")

def calculate_signal(symbol):
    """
    Simple signal generation based on price action
    In production, you'd fetch candles and calculate indicators
    """
    # For now, placeholder - would need candle data endpoint
    return None

def main_loop():
    """Main trading loop"""
    log("="*70)
    log("🚀 CRYPTO.COM AI AGENT STARTED")
    log(f"Pairs: {', '.join(CONFIG['symbols'])}")
    log(f"Position Size: ${CONFIG['position_size']} | Leverage: {CONFIG['leverage']}x")
    log("="*70)
    
    # Test connection
    log("\n[TEST] Checking API connection...")
    balance = get_account_balance()
    if balance:
        log(f"[OK] Connected! Balance: ${balance.get('totalBalance', 0)}")
    else:
        log("[ERR] Could not connect to API")
        log("[ERR] Check credentials and try again")
        return
    
    while True:
        try:
            # Get current positions
            api_positions = get_positions()
            tracked_positions = load_positions()
            
            log(f"[STATUS] API Positions: {len(api_positions)} | Tracked: {len(tracked_positions)}")
            
            # Check existing positions for TP/SL
            for pos in api_positions:
                symbol = pos.get('symbol')
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                size = float(pos.get('size', 0))
                side = pos.get('side', '').upper()
                
                # Calculate PnL
                if side == 'LONG':
                    pnl_pct = (mark_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - mark_price) / entry_price
                
                log(f"[POS] {symbol} {side}: Entry ${entry_price:.4f} | Mark ${mark_price:.4f} | PnL: {pnl_pct*100:.2f}%")
                
                # Check TP/SL
                if pnl_pct >= CONFIG['profit_target']:
                    log(f"[TP] Take profit hit for {symbol}: {pnl_pct*100:.2f}%")
                    close_position(symbol)
                elif pnl_pct <= -CONFIG['stop_loss']:
                    log(f"[SL] Stop loss hit for {symbol}: {pnl_pct*100:.2f}%")
                    close_position(symbol)
            
            # Look for new entries
            if len(api_positions) < CONFIG['max_positions']:
                log("[SCAN] Scanning for opportunities...")
                # Signal generation would go here
                # Need candle data endpoint for proper signals
            
            log(f"[SLEEP] Sleeping 30s...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            log("[STOP] Interrupted by user")
            break
        except Exception as e:
            log(f"[ERR] Loop error: {e}")
            import traceback
            log(f"[ERR] Traceback: {traceback.format_exc()}")
            time.sleep(30)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("[STOP] AI Agent stopped")
