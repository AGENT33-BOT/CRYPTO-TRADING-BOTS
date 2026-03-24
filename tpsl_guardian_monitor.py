#!/usr/bin/env python3
"""
TP/SL Guardian Monitor - 5 Minute Check System
Checks all positions every 5 minutes and adds TP/SL if missing
"""
import ccxt
import time
import json
import os
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

LOG_FILE = 'guardian_monitor.log'
REPORT_FILE = 'guardian_report.json'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def send_alert(symbol, action, details):
    """Send alert via available channels"""
    try:
        # Try Telegram
        import requests
        token = '7594239785:AAG6YjJ4LDK0vMQT5Cq2LHS5-9q-OWJb8oI'
        chat_id = '5804173449'
        message = f"🛡️ GUARDIAN ALERT\n\n{symbol}\nAction: {action}\n{details}"
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': message},
            timeout=5
        )
    except:
        pass

def get_exchange():
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    exchange.set_sandbox_mode(False)
    return exchange

def check_and_fix_tpsl(exchange, symbol, position):
    """Check if position has TP/SL, add if missing"""
    side = position['side']
    entry = float(position['entryPrice'])
    size = abs(float(position['contracts']))
    
    # Calculate TP/SL prices (2.5% TP, 1.5% SL)
    if side == 'long':
        tp_price = entry * 1.025
        sl_price = entry * 0.985
    else:
        tp_price = entry * 0.975
        sl_price = entry * 1.015
    
    # Round prices
    tp_price = round(tp_price, 4 if 'USDT' in symbol else 2)
    sl_price = round(sl_price, 4 if 'USDT' in symbol else 2)
    
    # Check existing orders
    has_tp = False
    has_sl = False
    
    try:
        orders = exchange.fetch_open_orders(symbol)
        for order in orders:
            if order.get('reduceOnly'):
                if order['side'] == ('sell' if side == 'long' else 'buy'):
                    if order.get('stopPrice'):
                        has_sl = True
                    else:
                        has_tp = True
    except:
        pass
    
    results = {'symbol': symbol, 'has_tp': has_tp, 'has_sl': has_sl, 'action': []}
    
    # Add missing TP
    if not has_tp:
        try:
            order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side='sell' if side == 'long' else 'buy',
                amount=size,
                price=tp_price,
                params={'reduceOnly': True}
            )
            results['action'].append(f'ADDED TP: {tp_price}')
            log(f"  [FIXED] Added TP for {symbol} at {tp_price}")
            send_alert(symbol, 'TP ADDED', f'Take Profit set at {tp_price}')
        except Exception as e:
            results['action'].append(f'TP ERROR: {e}')
            log(f"  [ERROR] Failed to add TP for {symbol}: {e}")
    
    # Add missing SL
    if not has_sl:
        try:
            order = exchange.create_order(
                symbol=symbol,
                type='stop',
                side='sell' if side == 'long' else 'buy',
                amount=size,
                price=None,
                params={'stopPrice': sl_price, 'reduceOnly': True}
            )
            results['action'].append(f'ADDED SL: {sl_price}')
            log(f"  [FIXED] Added SL for {symbol} at {sl_price}")
            send_alert(symbol, 'SL ADDED', f'Stop Loss set at {sl_price}')
        except Exception as e:
            results['action'].append(f'SL ERROR: {e}')
            log(f"  [ERROR] Failed to add SL for {symbol}: {e}")
    
    return results

def guardian_check():
    """Main guardian check function"""
    log("=" * 60)
    log("🛡️ TP/SL GUARDIAN - 5 MINUTE CHECK")
    log("=" * 60)
    
    try:
        exchange = get_exchange()
        positions = exchange.fetch_positions()
        
        active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        log(f"[>>] Found {len(active_positions)} open position(s)")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_positions': len(active_positions),
            'protected': 0,
            'fixed': 0,
            'errors': 0,
            'positions': []
        }
        
        for pos in active_positions:
            symbol = pos['symbol']
            side = pos['side']
            entry = float(pos['entryPrice'])
            size = abs(float(pos['contracts']))
            
            log(f"\n  [POS] {symbol} {side.upper()}")
            log(f"     Entry: {entry} | Size: {size}")
            
            # Check and fix TP/SL
            result = check_and_fix_tpsl(exchange, symbol, pos)
            
            if result['has_tp'] and result['has_sl']:
                log(f"     [OK] Already protected")
                report['protected'] += 1
            elif result['action']:
                log(f"     [FIXED] {' | '.join(result['action'])}")
                report['fixed'] += 1
            else:
                log(f"     [ERROR] Could not fix")
                report['errors'] += 1
            
            report['positions'].append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'entry': entry,
                'has_tp': result['has_tp'],
                'has_sl': result['has_sl'],
                'actions': result['action']
            })
        
        # Save report
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        
        log(f"\n[SUMMARY]")
        log(f"  Total: {report['total_positions']}")
        log(f"  Protected: {report['protected']}")
        log(f"  Fixed: {report['fixed']}")
        log(f"  Errors: {report['errors']}")
        log("=" * 60)
        
        # Return True if all protected
        return report['errors'] == 0 and (report['protected'] + report['fixed']) == report['total_positions']
        
    except Exception as e:
        log(f"[CRITICAL ERROR] {e}")
        return False

def main():
    """Run continuous monitoring"""
    log("\n" + "=" * 60)
    log("🛡️ TP/SL GUARDIAN MONITOR STARTED")
    log("Checking every 5 minutes...")
    log("Press Ctrl+C to stop")
    log("=" * 60 + "\n")
    
    try:
        while True:
            guardian_check()
            log("\n[>>] Sleeping 5 minutes...\n")
            time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        log("\n[>>] Guardian stopped by user")

if __name__ == '__main__':
    main()
