from bybit import BybitAPI
import os

# Main Bybit (bybit1)
api1 = BybitAPI(
    api_key=os.getenv("BYBIT_API_KEY", "XXXXXXXXXX"),
    api_secret=os.getenv("BYBIT_API_SECRET", "XXXXXXXXXX"),
    testnet=False
)

# Bybit2 
api2 = BybitAPI(
    api_key="aLz3ySrF9kMZubmqDR",
    api_secret="8SlpKyX7vleDu1loJiFePGWfnynJRXZXaD2z",
    testnet=False
)

print("=" * 50)
print("MAIN BYBIT ACCOUNT")
print("=" * 50)
try:
    bal1 = api1.get_wallet_balance()
    print(f"Balance: ${float(bal1.get('result', {}).get('list', [{}])[0].get('totalAvailableBalance', 0))}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 50)
print("BYBIT2 ACCOUNT")
print("=" * 50)
try:
    bal2 = api2.get_wallet_balance()
    print(f"Balance: ${float(bal2.get('result', {}).get('list', [{}])[0].get('totalAvailableBalance', 0))}")
except Exception as e:
    print(f"Error: {e}")
