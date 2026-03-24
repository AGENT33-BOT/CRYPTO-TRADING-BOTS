#!/usr/bin/env python3
"""Check which bots are running and identify spot order sources"""
import psutil
import sys

def check_running_bots():
    """Check all running Python processes"""
    print("="*70)
    print("CHECKING RUNNING TRADING BOTS")
    print("="*70)
    
    spot_bots = []
    futures_bots = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1:
                    script = cmdline[1] if len(cmdline) > 1 else ""
                    
                    # Check for spot trading bots
                    if 'funding_arbitrage.py' in script:
                        print(f"\n[ALERT] OLD FUNDING ARBITRAGE BOT RUNNING!")
                        print(f"  PID: {proc.info['pid']}")
                        print(f"  Script: {script}")
                        print(f"  Status: PLACES SPOT ORDERS!")
                        spot_bots.append((proc.info['pid'], script))
                    
                    elif 'funding_futures_only.py' in script:
                        print(f"\n[OK] NEW Futures-Only Funding Bot")
                        print(f"  PID: {proc.info['pid']}")
                        print(f"  Script: {script}")
                        print(f"  Status: FUTURES ONLY (no spot)")
                        futures_bots.append((proc.info['pid'], script))
                    
                    elif any(x in script for x in ['mean_reversion', 'momentum', 'scalping', 'grid']):
                        print(f"\n[OK] Strategy Bot")
                        print(f"  PID: {proc.info['pid']}")
                        print(f"  Script: {script}")
                        futures_bots.append((proc.info['pid'], script))
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if spot_bots:
        print(f"\n[CRITICAL] {len(spot_bots)} SPOT-TRADING BOT(S) RUNNING:")
        for pid, script in spot_bots:
            print(f"  - PID {pid}: {script}")
        print("\nThese bots are placing SPOT orders!")
    else:
        print("\n[GOOD] No spot-trading bots currently running")
    
    if futures_bots:
        print(f"\n[OK] {len(futures_bots)} FUTURES-ONLY BOT(S) RUNNING")
    
    print("\n" + "="*70)
    print("SPOT POSITIONS SOURCE IDENTIFIED:")
    print("="*70)
    print("""
The OLD funding_arbitrage.py bot creates SPOT positions by:
1. Buying SPOT (e.g., BTC/USDT spot market)
2. Shorting PERPETUAL (e.g., BTC/USDT:USDT futures)

This was replaced with funding_futures_only.py which ONLY shorts
perpetuals when funding is positive (no spot buying).

ACTION NEEDED:
1. Kill any running funding_arbitrage.py processes
2. Sell all spot holdings using sell_all_spot.py
3. Only run funding_futures_only.py (not the old one)
""")

check_running_bots()
