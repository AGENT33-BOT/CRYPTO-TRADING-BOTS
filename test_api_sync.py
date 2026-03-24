#!/usr/bin/env python3
"""
API TIME SYNC FIX for Bybit
Adds proper timestamp handling to prevent InvalidNonce errors
"""
import ccxt
import time
import os

def get_exchange_with_sync():
    """Initialize Bybit exchange with timestamp sync"""
    # Sync local time first
    print("Syncing system time...")
    os.system('w32tm /resync /force 2>nul')
    time.sleep(2)
    
    # Initialize exchange with larger recv_window
    exchange = ccxt.bybit({
        'apiKey': 'bsK06QDhsagOWwFsXQ',
        'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
            'recvWindow': 10000,  # Increase from 5000 to 10000ms
            'adjustForTimeDifference': True,  # Auto-adjust for time drift
        }
    })
    
    # Set timestamp adjustment
    try:
        exchange.load_markets()
        server_time = exchange.fetch_time()
        local_time = int(time.time() * 1000)
        time_diff = server_time - local_time
        print(f"Time difference: {time_diff}ms")
        
        if abs(time_diff) > 5000:
            print(f"WARNING: Time drift detected ({time_diff}ms)")
            print("Please run fix_system_time.bat as Administrator")
            
    except Exception as e:
        print(f"Time sync warning: {e}")
    
    return exchange

if __name__ == '__main__':
    print("=" * 60)
    print("API TIME SYNC TEST")
    print("=" * 60)
    
    try:
        ex = get_exchange_with_sync()
        balance = ex.fetch_balance()
        usdt = balance.get('USDT', {})
        print(f"\n✅ SUCCESS! Connected to Bybit")
        print(f"Balance: {usdt.get('total', 0):.2f} USDT")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPlease:")
        print("1. Run fix_system_time.bat as Administrator")
        print("2. Restart your computer")
        print("3. Try again")
