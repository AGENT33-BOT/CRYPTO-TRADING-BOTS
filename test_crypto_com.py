# -*- coding: utf-8 -*-
"""
Crypto.com API Connection Test
Run this to verify exact error details
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ccxt
import json
import traceback

print("="*60)
print("🧪 CRYPTO.COM API VERIFICATION TEST")
print("="*60)

# Load credentials
with open('crypto_com_credentials.json', 'r') as f:
    creds = json.load(f)

print(f"\n🔑 API Key: {creds['api_key'][:25]}...")
print(f"🔑 Secret: {creds['api_secret'][:20]}...")

# Initialize exchange
exchange = ccxt.cryptocom({
    'apiKey': creds['api_key'],
    'secret': creds['api_secret'],
    'enableRateLimit': True,
})

print("\n1️⃣ Testing PUBLIC endpoint (markets)...")
try:
    markets = exchange.load_markets()
    print(f"   ✅ SUCCESS - Loaded {len(markets)} markets")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    traceback.print_exc()

print("\n2️⃣ Testing PRIVATE endpoint (balance)...")
try:
    balance = exchange.fetch_balance()
    usd = balance.get('USD', {})
    print(f"   ✅ SUCCESS!")
    print(f"   💰 Total: ${usd.get('total', 0):.2f}")
    print(f"   💰 Free: ${usd.get('free', 0):.2f}")
    print(f"   💰 Used: ${usd.get('used', 0):.2f}")
    print("\n🎉 API IS WORKING - Ready to trade!")
except ccxt.AuthenticationError as e:
    print(f"   ❌ AUTHENTICATION ERROR")
    print(f"   Code: 40101")
    print(f"   Message: Authentication failure")
    print(f"\n   🔴 CAUSE: IP not whitelisted or wrong credentials")
    print(f"\n   FIX:")
    print(f"   1. Go to https://crypto.com/exchange/settings/api")
    print(f"   2. Whitelist your IP: 91.148.244.234")
    print(f"   3. Wait 2-3 minutes, then run this test again")
except ccxt.PermissionDenied as e:
    print(f"   ❌ PERMISSION DENIED: {e}")
    print(f"   FIX: Enable Account Balance (Read) permission")
except ccxt.NetworkError as e:
    print(f"   ❌ NETWORK ERROR: {e}")
    print(f"   FIX: Check internet connection")
except Exception as e:
    print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}")
    print(f"   {e}")
    traceback.print_exc()

print("\n" + "="*60)
