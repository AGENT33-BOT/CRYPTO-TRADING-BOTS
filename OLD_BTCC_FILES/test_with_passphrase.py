import requests
import hmac
import hashlib
import base64
import json
from datetime import datetime, timezone

# BTCC API Credentials
API_KEY = "0c9622dc-3f87-43e4-ac6e-244486c45fb7"
API_SECRET = "08d64f86-682c-4def-849b-ec3b28913d6b"
PASSPHRASE = "Lagina123#$"

# BTCC API endpoint
BASE_URL = "https://api.btcc.com"

def get_timestamp():
    """Get current timestamp in milliseconds"""
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))

def create_signature(timestamp, method, request_path, body=""):
    """Create HMAC SHA256 signature"""
    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(API_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode('utf-8')

def test_connection():
    """Test BTCC API connection"""
    print("="*60)
    print("TESTING BTCC CONNECTION")
    print("="*60)
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Passphrase: {'*' * len(PASSPHRASE)}")
    print()
    
    timestamp = get_timestamp()
    request_path = "/v1/account"
    method = "GET"
    
    signature = create_signature(timestamp, method, request_path)
    
    headers = {
        'Content-Type': 'application/json',
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': PASSPHRASE
    }
    
    try:
        url = f"{BASE_URL}{request_path}"
        print(f"Connecting to: {url}")
        print(f"Headers: {headers}")
        print()
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] Connected successfully!")
            print(f"\nAccount Info:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"\n[ERROR] {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return False

def test_market_data():
    """Test public market data endpoint"""
    print("\n" + "="*60)
    print("TESTING MARKET DATA (Public)")
    print("="*60)
    
    try:
        # Try to get ticker
        response = requests.get(f"{BASE_URL}/v1/tickers", timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] Market data accessible!")
            if 'data' in data:
                print(f"\nAvailable pairs: {len(data['data'])}")
                for pair in data['data'][:5]:
                    symbol = pair.get('symbol', 'N/A')
                    last = pair.get('last', 'N/A')
                    print(f"  {symbol}: ${last}")
            return True
        else:
            print(f"Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Test private API (account)
    private_ok = test_connection()
    
    # Test public API (market data)
    public_ok = test_market_data()
    
    print("\n" + "="*60)
    if private_ok:
        print("✅ PRIVATE API: WORKING")
    else:
        print("❌ PRIVATE API: FAILED")
    
    if public_ok:
        print("✅ PUBLIC API: WORKING")
    else:
        print("❌ PUBLIC API: FAILED")
    print("="*60)
