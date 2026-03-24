# -*- coding: utf-8 -*-
"""
SOL Dip Monitor - Alerts when SOL drops 5%+
"""

import json
import os
import subprocess
from datetime import datetime

# Config
DIP_THRESHOLD = -5.0  # Buy when down 5% or more
BUY_AMOUNT = 100  # USD to buy
CREDS_FILE = 'C:/Users/digim/clawd/crypto_trader/crypto_com_credentials.json'

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

def get_sol_price():
    """Get current SOL price and 24h change from Crypto.com"""
    try:
        # Use the skill to check balance (includes price data)
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE, 'r') as f:
                creds = json.load(f)
            
            env = os.environ.copy()
            env['CDC_API_KEY'] = creds.get('api_key', '')
            env['CDC_API_SECRET'] = creds.get('api_secret', '')
            
            skill_path = os.path.expanduser('~/.agents/skills/crypto-agent-trading')
            cmd = f'npx tsx {skill_path}/scripts/account.ts balance SOL'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            # Parse response
            lines = result.stdout.strip().split('\n')
            for line in reversed(lines):
                if line.strip().startswith('{'):
                    data = json.loads(line)
                    if data.get('ok'):
                        return data.get('data', {})
        return None
    except Exception as e:
        log(f"Error: {e}")
        return None

def main():
    log("="*60)
    log("SOL DIP MONITOR STARTED")
    log(f"Buy Trigger: {DIP_THRESHOLD}% or lower")
    log(f"Buy Amount: ${BUY_AMOUNT} USD")
    log("="*60)
    
    sol_data = get_sol_price()
    
    if sol_data:
        change_pct = float(sol_data.get('percentage_change', 0))
        price_usd = float(sol_data.get('native_balance', {}).get('amount', 0)) / float(sol_data.get('balance', {}).get('amount', 1))
        balance_sol = float(sol_data.get('balance', {}).get('amount', 0))
        
        log(f"\nCurrent SOL Price: ${price_usd:.2f}")
        log(f"24h Change: {change_pct:.2f}%")
        log(f"Your Holdings: {balance_sol:.2f} SOL")
        
        if change_pct <= DIP_THRESHOLD:
            log(f"\n🚨 DIP ALERT! SOL is down {change_pct:.2f}%!")
            log(f"💰 BUY ${BUY_AMOUNT} OF SOL NOW!")
            log(f"\nRun this command:")
            log(f"cd ~/.agents/skills/crypto-agent-trading")
            log(f"npx tsx scripts/trade.ts quote purchase '{{\"from_currency\":\"USD\",\"to_currency\":\"SOL\",\"from_amount\":\"100\"}}'")
        else:
            log(f"\n⏳ Not yet at dip threshold.")
            log(f"Current: {change_pct:.2f}% | Need: {DIP_THRESHOLD}% or lower")
            log(f"Distance to trigger: {abs(change_pct - DIP_THRESHOLD):.2f}% more drop needed")
    else:
        log("❌ Could not fetch SOL price")

if __name__ == '__main__':
    main()
