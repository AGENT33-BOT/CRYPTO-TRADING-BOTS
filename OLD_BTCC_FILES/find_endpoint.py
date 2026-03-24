import requests

# Try different BTCC endpoints
endpoints = [
    "https://api.btcc.com",
    "https://www.btcc.com/api",
    "https://api-pro.btcc.com",
    "https://api.btcc.pro",
]

print("Testing BTCC API endpoints...")
print("="*60)

for url in endpoints:
    print(f"\nTrying: {url}")
    try:
        response = requests.get(f"{url}/v1/tickers", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  [OK] Working!")
            print(f"  Response: {response.text[:200]}")
            break
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")

print("\n" + "="*60)
