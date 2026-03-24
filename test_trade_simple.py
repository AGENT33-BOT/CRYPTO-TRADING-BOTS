"""
Polymarket Simple Test Trade
Uses real token IDs from active markets
"""

import json
import sys
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs

# Load config
with open('polymarket_config.json', 'r') as f:
    config = json.load(f)

pm_config = config.get('polymarket', {})
API_KEY = pm_config.get('api_key')
PRIVATE_KEY = pm_config.get('private_key')  # Use private_key, not api_secret
API_SECRET = pm_config.get('api_secret')
PASSPHRASE = pm_config.get('passphrase')

print("="*60)
print("POLYMARKET TEST TRADE")
print("="*60)
print()

# Use first market for testing
MARKET = {
    "name": "Will Trump deport less than 250,000?",
    "yes_token": "101676997363687199724245607342877036148401850938023978421879460310389391082353",
    "no_token": "4153292802911610701832309484716814274802943278345248636922528170020319407796",
    "price": 0.032  # Best bid from market
}

print("Market:", MARKET['name'])
print("YES Price: ~$0.032 (3.2%)")
print()

# Initialize client
print("Connecting to Polymarket...")
try:
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=PRIVATE_KEY,  # Use the Ethereum private key
        chain_id=137,
        creds=ApiCreds(
            api_key=API_KEY,
            api_secret=API_SECRET,
            api_passphrase=PASSPHRASE
        )
    )
    print("[OK] Connected\n")
except Exception as e:
    print(f"[FAIL] Connection error: {e}")
    sys.exit(1)

# Get balance
print("Checking balance...")
try:
    # Try to get API key details first
    api_info = client.get_api_key_details()
    print(f"[OK] API Key valid")
    print(f"   Account: {api_info.get('account', 'N/A')}")
except Exception as e:
    print(f"[INFO] Could not get API details: {e}")

# Ask for trade size
print()
trade_size = input("Enter trade size USD (min $5, suggest $10 for test): ").strip()
if not trade_size:
    trade_size = "10"

try:
    size = float(trade_size)
    if size < 5:
        print("Minimum $5, using $10")
        size = 10
except:
    size = 10

print()
print("="*60)
print("TRADE DETAILS")
print("="*60)
print(f"Market: {MARKET['name']}")
print(f"Side: BUY YES")
print(f"Size: ${size:.2f}")
print(f"Price: ${MARKET['price']:.3f}")
print()

confirm = input("Place this trade? (yes/no): ").strip().lower()

if confirm == "yes":
    try:
        print()
        print("Creating order...")
        
        # Create order
        order_args = OrderArgs(
            price=MARKET['price'],
            size=size,
            side="buy",
            token_id=MARKET['yes_token']
        )
        
        print("[OK] Order args created")
        print(f"  Token: YES")
        print(f"  Size: ${size:.2f}")
        print()
        
        # Create signed order
        print("Signing order...")
        signed_order = client.create_order(order_args)
        print("[OK] Order signed")
        print()
        
        # Post order
        print("Submitting to Polymarket...")
        result = client.post_order(signed_order)
        
        print()
        print("="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"Order ID: {result.get('orderID', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print()
        print("Check your portfolio:")
        print("https://polymarket.com/portfolio")
        
    except Exception as e:
        print()
        print("="*60)
        print("FAILED")
        print("="*60)
        print(f"Error: {e}")
        print()
        print("Possible issues:")
        print("- Insufficient USDC balance")
        print("- Price moved (try current market price)")
        print("- API credentials issue")
        import traceback
        traceback.print_exc()
else:
    print("Cancelled.")
