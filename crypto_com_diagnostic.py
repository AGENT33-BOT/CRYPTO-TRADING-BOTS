# -*- coding: utf-8 -*-
"""
Crypto.com API Diagnostic Tool
Checks configuration and identifies connection issues
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import ccxt
import json
import os
import socket
import requests

print("="*60)
print("🔍 CRYPTO.COM API DIAGNOSTIC")
print("="*60)

# 1. Load credentials
print("\n📋 STEP 1: Loading credentials...")
creds_file = 'crypto_com_credentials.json'
api_key = ''
api_secret = ''

if os.path.exists(creds_file):
    with open(creds_file, 'r') as f:
        creds = json.load(f)
        api_key = creds.get('api_key', '')
        api_secret = creds.get('api_secret', '')
    print(f"   ✅ Credentials file found")
    print(f"   API Key: {api_key[:20]}... (length: {len(api_key)})")
    print(f"   Secret: {'*' * 10} (length: {len(api_secret)})")
else:
    print("   ❌ Credentials file not found!")
    api_key = os.environ.get('CRYPTOCOM_API_KEY', '')
    api_secret = os.environ.get('CRYPTOCOM_API_SECRET', '')

if not api_key or not api_secret:
    print("   ❌ No API credentials found!")
    sys.exit(1)

# 2. Check network connectivity
print("\n🌐 STEP 2: Network connectivity...")
try:
    response = requests.get('https://api.crypto.com/exchange/v1/public/time', timeout=10)
    print(f"   ✅ API endpoint reachable (HTTP {response.status_code})")
except Exception as e:
    print(f"   ❌ Cannot reach API: {e}")

# 3. Get public IP
print("\n📍 STEP 3: Your public IP address...")
try:
    ip = requests.get('https://api.ipify.org', timeout=5).text
    print(f"   Your IP: {ip}")
    print(f"   ⚠️  Make sure this IP is whitelisted in Crypto.com settings!")
except:
    print("   Could not determine public IP")

# 4. Initialize exchange
print("\n🔌 STEP 4: Initializing exchange connection...")
try:
    exchange = ccxt.cryptocom({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'verbose': False,
    })
    print("   ✅ Exchange object created")
except Exception as e:
    print(f"   ❌ Failed to create exchange: {e}")
    sys.exit(1)

# 5. Load markets (public endpoint)
print("\n📊 STEP 5: Loading markets (public)...")
try:
    markets = exchange.load_markets()
    print(f"   ✅ Markets loaded: {len(markets)} pairs")
    
    # Check for USD perpetuals
    usd_perps = [s for s in markets if '/USD' in s and markets[s].get('swap')]
    print(f"   USD Perpetuals available: {len(usd_perps)}")
    if usd_perps:
        print(f"   Examples: {', '.join(usd_perps[:3])}")
except Exception as e:
    print(f"   ❌ Failed to load markets: {e}")

# 6. Test private endpoint (balance)
print("\n🔐 STEP 6: Testing private API (balance fetch)...")
print("   This requires proper API key permissions and IP whitelisting...")
try:
    balance = exchange.fetch_balance()
    usd = balance.get('USD', {})
    print(f"   ✅ SUCCESS! Balance fetched")
    print(f"   USD Total: ${usd.get('total', 0):.2f}")
    print(f"   USD Free: ${usd.get('free', 0):.2f}")
    print(f"   USD Used: ${usd.get('used', 0):.2f}")
except ccxt.AuthenticationError as e:
    print(f"   ❌ AUTHENTICATION FAILED")
    print(f"   Error: {e}")
    print("\n   🔧 COMMON FIXES:")
    print("   1. Go to https://crypto.com/exchange/settings/api")
    print("   2. Add your IP to whitelist (see Step 3 above)")
    print("   3. Ensure 'Account Balance (Read)' permission is enabled")
    print("   4. Make sure you're using EXCHANGE API (not App API)")
    print("   5. Try regenerating API keys")
except ccxt.PermissionDenied as e:
    print(f"   ❌ PERMISSION DENIED")
    print(f"   Error: {e}")
    print("\n   🔧 FIX: Enable required permissions in API settings")
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")

# 7. Recommendations
print("\n💡 RECOMMENDATIONS:")
print("   • Verify API keys are from https://crypto.com/exchange (not mobile app)")
print("   • Whitelist your IP address in API settings")
print("   • Enable these permissions:")
print("     - Account Balance (Read)")
print("     - Spot Trading")
print("     - Derivatives Trading (for futures)")
print("   • Regenerate keys if problems persist")

print("\n" + "="*60)
