#!/usr/bin/env python3
"""
STRICT $5 MAX LOSS ENFORCER
Kills positions immediately if they exceed $5 loss
"""
import ccxt
import time
import os
from datetime import datetime

LOG_FILE = 'strict_enforcer.log'
MAX_LOSS = 5.0  # HARDCODED - NO EXCEPTIONS

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def get_exchange():
    return ccxt.bybit({
        'apiKey': 'bsK06QDhsagOWwFsXQ',
        'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })

def enforce_limits():
    log("=" * 60)
    log("STRICT $5 MAX LOSS ENFORCER - CHECKING")
    log("=" * 60)
    
    try:
        exchange = get_exchange()
        positions = exchange.fetch_positions()
        active = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        log(f"Active positions: {len(active)}")
        
        violations = []
        for pos in active:
            symbol = pos['symbol']
            side = pos['side']
            size = abs(float(pos['contracts']))
            pnl = float(pos.get('unrealizedPnl', 0))
            
            log(f"{symbol} {side.upper()}: Size={size}, PnL=${pnl:.2f}")
            
            # STRICT: Close if loss exceeds $5
            if pnl < -MAX_LOSS:
                log(f"  VIOLATION! Loss ${pnl:.2f} exceeds -${MAX_LOSS}")
                log(f"  CLOSING IMMEDIATELY...")
                
                try:
                    if side == 'long':
                        order = exchange.create_market_sell_order(symbol, size)
                    else:
                        order = exchange.create_market_buy_order(symbol, size)
                    
                    violations.append({
                        'symbol': symbol,
                        'pnl': pnl,
                        'order_id': order['id']
                    })
                    log(f"  CLOSED! Order: {order['id']}")
                    time.sleep(1)
                except Exception as e:
                    log(f"  ERROR closing: {e}")
        
        if violations:
            log("=" * 60)
            log(f"CLOSED {len(violations)} VIOLATION(S):")
            for v in violations:
                log(f"  {v['symbol']}: ${v['pnl']:.2f}")
        else:
            log("No violations found. All positions within $5 limit.")
        
        log("=" * 60)
        
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")

def main():
    log("\n" + "=" * 60)
    log("STRICT $5 MAX LOSS ENFORCER STARTED")
    log("Checking every 30 seconds...")
    log("=" * 60 + "\n")
    
    while True:
        enforce_limits()
        time.sleep(30)  # Check every 30 seconds

if __name__ == '__main__':
    main()
