import requests
import sys
sys.path.insert(0, 'alpaca_strategies')
from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

print("=== AGENT ALPACA - CREDENTIAL VERIFICATION ===")
print(f"Base URL: {ALPACA_BASE_URL}")
if ALPACA_API_KEY:
    print(f"API Key: {ALPACA_API_KEY[:8]}...{ALPACA_API_KEY[-4:]}")
else:
    print("API Key: NOT SET")

if ALPACA_SECRET_KEY:
    print(f"API Secret: {ALPACA_SECRET_KEY[:8]}...{ALPACA_SECRET_KEY[-4:]}")
else:
    print("API Secret: NOT SET")
print()

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    print("[FAIL] CREDENTIALS MISSING - Check .alpaca_env file")
    sys.exit(1)

headers = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
}

try:
    resp = requests.get(f'{ALPACA_BASE_URL}/v2/account', headers=headers, timeout=10)
    if resp.status_code == 200:
        account = resp.json()
        print("[OK] CREDENTIALS VALID - API Connection Successful")
        print(f"Account ID: {account.get('id', 'N/A')}")
        print(f"Status: {account.get('status', 'N/A')}")
        print(f"Account Type: {account.get('account_type', 'N/A')}")
        print()
        print("--- BALANCE ---")
        print(f"Portfolio Value: ${float(account.get('portfolio_value', 0)):.2f}")
        print(f"Cash: ${float(account.get('cash', 0)):.2f}")
        print(f"Buying Power: ${float(account.get('buying_power', 0)):.2f}")
        print(f"Equity: ${float(account.get('equity', 0)):.2f}")
    else:
        print(f"[FAIL] API ERROR - Status: {resp.status_code}")
        print(f"Response: {resp.text}")
except Exception as e:
    print(f"[FAIL] CONNECTION ERROR: {e}")
