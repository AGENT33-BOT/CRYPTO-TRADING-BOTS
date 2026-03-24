import requests
import hmac
import hashlib
import base64
import json
from datetime import datetime, timezone

API_KEY = "0c9622dc-3f87-43e4-ac6e-244486c45fb7"
API_SECRET = "08d64f86-682c-4def-849b-ec3b28913d6b"

BASE_URL = "https://api.btcc.com"

def get_timestamp():
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))

def sign(message, secret):
    mac = hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode('utf-8')

def test_connection():
    print("Testing BTCC Connection")
    print("="*50)
    
    timestamp = get_timestamp()
    
    # Try to get account info
    message = timestamp + "GET" + "/api/v1/account"
    signature = sign(message, API_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/account", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] Connected successfully!")
            print(f"\nAccount Data:")
            print(json.dumps(data, indent=2)[:500])
        else:
            print(f"\nError: {response.text}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTrying alternative endpoint...")
        
        # Try markets endpoint
        try:
            response = requests.get(f"{BASE_URL}/api/v1/market/tickers", timeout=10)
            if response.status_code == 200:
                print("\n[OK] Public API working!")
                data = response.json()
                if 'data' in data:
                    print(f"\nAvailable pairs: {len(data['data'])}")
                    for pair in data['data'][:3]:
                        print(f"  {pair.get('symbol')}: ${pair.get('last')}")
            else:
                print(f"Error: {response.status_code}")
        except Exception as e2:
            print(f"Alternative also failed: {str(e2)}")

if __name__ == "__main__":
    test_connection()
