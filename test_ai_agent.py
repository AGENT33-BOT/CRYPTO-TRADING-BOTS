# -*- coding: utf-8 -*-
"""
Test Crypto.com AI Agent SDK Connection
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
import hmac
import hashlib
import os

print("="*60)
print("🧪 CRYPTO.COM AI AGENT SDK TEST")
print("="*60)

# Load credentials
CREDS_FILE = 'crypto_com_credentials.json'
api_key = ''
api_secret = ''

if os.path.exists(CREDS_FILE):
    with open(CREDS_FILE, 'r') as f:
        creds = json.load(f)
        api_key = creds.get('api_key', '')
        api_secret = creds.get('api_secret', '')

if not api_key or not api_secret:
    print("❌ No credentials found!")
    sys.exit(1)

print(f"\n🔑 API Key: {api_key[:30]}...")
print(f"🔑 Secret: {api_secret[:20]}...")

# AI Agent SDK endpoint
BASE_URL = 'https://agent-api.crypto.com'

def generate_signature(secret, timestamp, method, path, body=''):
    message = f"{timestamp}{method.upper()}{path}{body}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def make_request(method, path, body=None):
    timestamp = str(int(time.time() * 1000))
    body_str = json.dumps(body) if body else ''
    signature = generate_signature(api_secret, timestamp, method, path, body_str)
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
        'X-Signature': signature,
        'X-Timestamp': timestamp,
    }
    
    url = f"{BASE_URL}{path}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, data=body_str, timeout=30)
        
        return response
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

print("\n1️⃣ Testing GET /v1/account/balance...")
response = make_request('GET', '/v1/account/balance')
if response:
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)[:500]}")
        if data.get('code') == 0:
            print("   ✅ SUCCESS!")
        else:
            print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
    except:
        print(f"   Response text: {response.text[:200]}")
else:
    print("   ❌ No response")

print("\n2️⃣ Testing GET /v1/positions...")
response = make_request('GET', '/v1/positions')
if response:
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        if data.get('code') == 0:
            positions = data.get('data', {}).get('positions', [])
            print(f"   ✅ SUCCESS! Open positions: {len(positions)}")
        else:
            print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   Error parsing: {e}")

print("\n3️⃣ Testing GET /v1/mark-price/BTCUSD-PERP...")
response = make_request('GET', '/v1/mark-price/BTCUSD-PERP')
if response:
    print(f"   Status: {response.status_code}")
    try:
        data = response.json()
        if data.get('code') == 0:
            price = data.get('data', {}).get('markPrice', 0)
            print(f"   ✅ SUCCESS! BTC Mark Price: ${price}")
        else:
            print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   Error parsing: {e}")

print("\n" + "="*60)
print("💡 If all tests show ✅, the AI Agent bot is ready to run!")
print("="*60)
