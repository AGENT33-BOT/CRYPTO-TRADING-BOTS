"""
Place Polymarket trade with $10 from available balance
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
PRIVATE_KEY = pm_config.get('private_key')
API_SECRET = pm_config.get('api_secret')
PASSPHRASE = pm_config.get('passphrase')

print("="*60)
print("POLYMARKET TRADE - AUTO EXECUTE")
print("="*60)
print()

# Market details
MARKET = {
    "name": "Will Trump deport less than 250,000?",
    "yes_token": "101676997363687199724245607342877036148401850938023978421879460310389391082353",
    "no_token": "4153292802911610701832309484716814274802943278345248636922528170020319407796",
    "price": 0.032
}

TRADE_SIZE = 10.00  # $10 USD

print(f"Balance Available: $49.72 USDT")
print(f"Trade Size: ${TRADE_SIZE:.2f}")
print()
print(f"Market: {MARKET['name']}")
print(f"Side: BUY YES")
print(f"Price: ${MARKET['price']:.3f}")
print(f"Potential Return: ${TRADE_SIZE / MARKET['price']:.2f} shares")
print()

# Initialize client
print("Connecting to Polymarket CLOB...")
try:
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=PRIVATE_KEY,
        chain_id=137,
        creds=ApiCreds(
            api_key=API_KEY,
            api_secret=API_SECRET,
            api_passphrase=PASSPHRASE
        )
    )
    print("[OK] Connected to CLOB")
except Exception as e:
    print(f"[FAIL] Connection error: {e}")
    sys.exit(1)

print()
print("="*60)
print("EXECUTING TRADE NOW")
print("="*60)
print()

try:
    # Create order
    print("Step 1: Creating order...")
    order_args = OrderArgs(
        price=MARKET['price'],
        size=TRADE_SIZE,
        side="BUY",  # Must be uppercase
        token_id=MARKET['yes_token']
    )
    print(f"  [OK] Order created: ${TRADE_SIZE} @ {MARKET['price']}")
    
    # Sign order
    print("Step 2: Signing order...")
    signed_order = client.create_order(order_args)
    print("  [OK] Order signed")
    
    # Post order
    print("Step 3: Submitting to Polymarket...")
    result = client.post_order(signed_order)
    
    print()
    print("="*60)
    print("✅ TRADE SUCCESSFUL!")
    print("="*60)
    print(f"Order ID: {result.get('orderID', 'N/A')}")
    print(f"Status: {result.get('status', 'N/A')}")
    print(f"Size: ${TRADE_SIZE:.2f}")
    print(f"Side: BUY YES")
    print()
    print("Check your positions:")
    print("https://polymarket.com/portfolio")
    print()
    print("Remaining Balance: ~$39.72 USDT")
    
except Exception as e:
    print()
    print("="*60)
    print("TRADE FAILED")
    print("="*60)
    print(f"Error: {e}")
    print()
    print("Note: Polymarket requires USDC, not USDT.")
    print("You may need to convert USDT to USDC or deposit USDC.")
    print()
    print("To convert:")
    print("1. Go to https://polymarket.com")
    print("2. Click 'Deposit'")
    print("3. Convert USDT to USDC using the built-in swap")
    import traceback
    traceback.print_exc()
