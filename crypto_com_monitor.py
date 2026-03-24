# -*- coding: utf-8 -*-
"""
Crypto.com Price Monitor & Alert System
Monitors portfolio for buy/sell opportunities
"""

import json
import os
import sys
import io
import subprocess
from datetime import datetime

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

LOG_FILE = 'crypto_monitor.log'
ALERTS_FILE = 'crypto_alerts.json'
CREDS_FILE = 'crypto_com_credentials.json'

# Alert thresholds
BUY_DIP_THRESHOLD = -5.0      # Alert when coin drops 5%+
SELL_PROFIT_THRESHOLD = 5.0   # Alert when coin gains 5%+

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    except:
        pass

def run_skill_command(command):
    """Run a crypto.com skill command and return JSON result"""
    env = os.environ.copy()
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE, 'r') as f:
            creds = json.load(f)
            env['CDC_API_KEY'] = creds.get('api_key', '')
            env['CDC_API_SECRET'] = creds.get('api_secret', '')
    
    skill_path = os.path.expanduser('~/.agents/skills/crypto-agent-trading')
    full_cmd = f'npx tsx {skill_path}/{command}'
    
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        # Parse JSON from output (skip npm warnings)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and line.startswith('{'):
                return json.loads(line)
        return None
    except Exception as e:
        log(f'[ERR] Command failed: {e}')
        return None

def get_portfolio():
    """Get current portfolio with balances and 24h changes"""
    result = run_skill_command('scripts/account.ts balances all')
    if result and result.get('ok'):
        return result.get('data', {})
    return None

def check_opportunities():
    """Check for buy/sell opportunities based on 24h price changes"""
    portfolio = get_portfolio()
    if not portfolio:
        log('[ERR] Could not fetch portfolio')
        return []
    
    alerts = []
    crypto_balances = portfolio.get('crypto', [])
    
    log(f'[SCAN] Checking {len(crypto_balances)} coins for opportunities...')
    
    for coin in crypto_balances:
        currency = coin.get('currency')
        balance = float(coin.get('native_balance', {}).get('amount', 0))
        change_pct = float(coin.get('percentage_change', 0))
        
        if balance < 5:  # Skip coins worth less than $5
            continue
        
        # Check for buying opportunity (dips)
        if change_pct <= BUY_DIP_THRESHOLD:
            alert = {
                'type': 'BUY_OPPORTUNITY',
                'coin': currency,
                'change_24h': change_pct,
                'usd_value': balance,
                'message': f'BUY ALERT: {currency} down {abs(change_pct):.2f}%! Dip opportunity. Value: ${balance:.2f}',
                'timestamp': datetime.now().isoformat()
            }
            alerts.append(alert)
            log(f'[ALERT] {alert["message"]}')
        
        # Check for selling opportunity (gains)
        elif change_pct >= SELL_PROFIT_THRESHOLD:
            alert = {
                'type': 'SELL_OPPORTUNITY',
                'coin': currency,
                'change_24h': change_pct,
                'usd_value': balance,
                'message': f'SELL ALERT: {currency} up {change_pct:.2f}%! Profit taking opportunity. Value: ${balance:.2f}',
                'timestamp': datetime.now().isoformat()
            }
            alerts.append(alert)
            log(f'[ALERT] {alert["message"]}')
    
    return alerts

def save_alerts(alerts):
    """Save alerts to file"""
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)
    except Exception as e:
        log(f'[ERR] Could not save alerts: {e}')

def main_monitor():
    """Main monitoring loop"""
    log('='*60)
    log('CRYPTO.COM PRICE MONITOR STARTED')
    log(f'Buy Threshold: {BUY_DIP_THRESHOLD}% | Sell Threshold: {SELL_PROFIT_THRESHOLD}%')
    log('='*60)
    
    alerts = check_opportunities()
    
    if alerts:
        log(f'\nFOUND {len(alerts)} OPPORTUNITIES:')
        for alert in alerts:
            log(f'  {alert["message"]}')
    else:
        log('\nNo major opportunities found. Portfolio stable.')
    
    save_alerts(alerts)
    
    # Summary
    portfolio = get_portfolio()
    if portfolio:
        crypto = portfolio.get('crypto', [])
        total_usd = sum(float(c.get('native_balance', {}).get('amount', 0)) for c in crypto)
        
        log(f'\nPORTFOLIO SUMMARY:')
        log(f'  Total Crypto Value: ${total_usd:,.2f}')
        log(f'  Coins Monitored: {len(crypto)}')
        
        # Top movers
        movers = sorted(crypto, key=lambda x: float(x.get('percentage_change', 0)), reverse=True)
        log(f'\nTOP GAINERS (24h):')
        for coin in movers[:5]:
            change = float(coin.get('percentage_change', 0))
            if change > 0:
                log(f'  {coin["currency"]}: +{change:.2f}% (${float(coin.get("native_balance", {}).get("amount", 0)):.2f})')
        
        log(f'\nTOP LOSERS (24h):')
        for coin in reversed(movers[-5:]):
            change = float(coin.get('percentage_change', 0))
            if change < 0:
                log(f'  {coin["currency"]}: {change:.2f}% (${float(coin.get("native_balance", {}).get("amount", 0)):.2f})')
    
    log('\n' + '='*60)
    log('Monitor complete. Run again or schedule with cron.')
    log('='*60)

if __name__ == '__main__':
    main_monitor()
