"""
Quick status check for Agent Bybit2
"""

import ccxt
import json
import os
from datetime import datetime

API_KEY = 'aLz3ySrF9kMZubmqDR'
API_SECRET = '8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z'

def main():
    print("="*60)
    print("AGENT BYBIT2 - STATUS CHECK")
    print("="*60)
    
    try:
        exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        exchange.set_sandbox_mode(False)
        
        # Check balance
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {})
        total = usdt.get('total', 0)
        free = usdt.get('free', 0)
        used = usdt.get('used', 0)
        
        print(f"\n💰 BALANCE")
        print(f"   Total:  ${total:.2f} USDT")
        print(f"   Free:   ${free:.2f} USDT")
        print(f"   Used:   ${used:.2f} USDT")
        
        # Check positions
        print(f"\n📊 POSITIONS")
        positions = exchange.fetch_positions(['SOL/USDT:USDT'])
        open_pos = [p for p in positions if float(p.get('contracts', 0)) != 0]
        
        if open_pos:
            for p in open_pos:
                side = 'LONG' if p['side'] == 'long' else 'SHORT'
                entry = float(p.get('entryPrice', 0))
                mark = float(p.get('markPrice', 0))
                size = float(p.get('contracts', 0))
                pnl = float(p.get('unrealizedPnl', 0))
                print(f"   {side} SOL: {size} @ {entry:.2f} | Mark: {mark:.2f} | PnL: ${pnl:+.2f}")
        else:
            print("   No open positions")
        
        # Check saved positions
        pos_file = 'crypto_trader/agent_bybit2/agent_bybit2_positions.json'
        if os.path.exists(pos_file):
            with open(pos_file) as f:
                saved = json.load(f)
            print(f"\n📝 Saved Positions: {len(saved)}")
            for pid, p in saved.items():
                print(f"   {p['side']} {p['symbol']} @ {p['entry']:.2f}")
        
        # Check log
        log_file = 'crypto_trader/agent_bybit2/agent_bybit2.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
            if lines:
                print(f"\n🕐 Last Activity:")
                for line in lines[-5:]:
                    print(f"   {line.strip()}")
        
        print("\n" + "="*60)
        print("Status check complete")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
