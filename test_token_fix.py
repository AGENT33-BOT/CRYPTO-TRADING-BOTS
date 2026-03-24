#!/usr/bin/env python3
"""
POLYMARKET TOKEN ID FIX - TEST SCRIPT
Tests the updated token ID extraction logic
"""

import sys
sys.path.insert(0, 'C:\\Users\\digim\\clawd\\crypto_trader')

from polymarket_trader import PolymarketTrader
import json

print("=" * 70)
print("POLYMARKET TOKEN ID FIX - TESTING")
print("=" * 70)

# Initialize trader
trader = PolymarketTrader()

print("\n[1/3] Fetching active markets...")
markets = trader.get_active_markets(limit=10)
print(f"Found {len(markets)} markets")

print("\n[2/3] Testing token ID extraction...")
token_success = 0
token_fail = 0

for i, market in enumerate(markets[:5], 1):
    print(f"\n--- Market {i} ---")
    question = market.get('question', 'Unknown')[:50]
    print(f"Question: {question}...")
    
    # Check raw clobTokenIds
    clob_ids = market.get('clobTokenIds', [])
    print(f"Raw clobTokenIds: {clob_ids}")
    print(f"Type: {type(clob_ids)}")
    
    # Run analysis
    analysis = trader.analyze_market(market)
    
    yes_id = analysis.get('yes_token_id')
    no_id = analysis.get('no_token_id')
    
    if yes_id and no_id:
        print(f"[OK] YES Token: {yes_id[:20]}...")
        print(f"[OK] NO Token: {no_id[:20]}...")
        token_success += 1
    else:
        print(f"[FAIL] Failed to extract tokens")
        print(f"   YES: {yes_id}")
        print(f"   NO: {no_id}")
        token_fail += 1

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
print(f"Successful token extraction: {token_success}/{token_success + token_fail}")
print(f"Failed: {token_fail}")

if token_success > 0:
    print("\n[SUCCESS] FIX WORKING - Token IDs can be extracted")
else:
    print("\n[FAILED] Still failing - Need to investigate further")

print("\n[3/3] Checking if live trading is configured...")
if trader.api_key and trader.api_secret:
    print("✅ API credentials found")
else:
    print("⚠️  API credentials not configured")
    print("   Add to polymarket_config.json:")
    print('   {"polymarket": {"api_key": "...", "api_secret": "...", "passphrase": "...", "private_key": "..."}}')

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("1. If tokens extract successfully, test with live trading")
print("2. Run: python polymarket_trader.py")
print("3. Monitor logs for successful trades")
