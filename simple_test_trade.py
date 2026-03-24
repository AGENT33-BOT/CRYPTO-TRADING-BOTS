"""
Polymarket Simple Test Trade
Place a small trade directly without the complex bot
"""

import json
import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs

# Load config
with open('polymarket_config.json', 'r') as f:
    config = json.load(f)

pm_config = config.get('polymarket', {})
API_KEY = pm_config.get('api_key')
API_SECRET = pm_config.get('api_secret')  # This is the private key
PASSPHRASE = pm_config.get('passphrase')

print("="*60)
print("POLYMARKET TEST TRADE")
print("="*60)
print()

# Initialize client
print("Connecting to Polymarket CLOB...")
client = ClobClient(
    host="https://clob.polymarket.com",
    key=API_SECRET,  # Private key
    chain_id=137,  # Polygon
    creds=ApiCreds(
        api_key=API_KEY,
        api_secret=API_SECRET,
        api_passphrase=PASSPHRASE
    )
)

print("[OK] Connected")
print()

# Get balance
print("Checking USDC balance...")
try:
    balance = client.get_balance()
    print(f"[OK] Balance: ${float(balance):.2f} USDC")
except Exception as e:
    print(f"[INFO] Could not get balance: {e}")
    print("      Will assume sufficient balance for test")

print()

# List available markets
print("Fetching markets...")
print()

# Known working token IDs for testing
# These are from active markets
test_markets = [
    {
        "name": "Will bitcoin hit $1m before GTA VI?",
        "token_id": "71321070678245294690549078392707895680824517671538256303036618815514648059606",  # YES token
        "price": 0.001
    },
    {
        "name": "Will ETH hit $10k in 2025?", 
        "token_id": "0",  # Placeholder - would need real ID
        "price": 0.05
    }
]

# Show the bitcoin market
market = test_markets[0]
print(f"Market: {market['name']}")
print(f"Token ID: {market['token_id'][:20]}...")
print(f"Current Price: ~${market['price']:.3f}")
print()

# Ask for trade size
trade_size = input("Enter trade size in USD (suggest $5-10 for test): ").strip()
if not trade_size:
    trade_size = "5"

try:
    size = float(trade_size)
    if size < 1:
        print("Minimum trade is $1")
        size = 5
except:
    size = 5

print()
print("="*60)
print("TRADE DETAILS")
print("="*60)
print(f"Market: {market['name']}")
print(f"Side: BUY YES")
print(f"Size: ${size:.2f}")
print(f"Price: ${market['price']:.3f}")
print()

confirm = input("Place this trade? (yes/no): ").strip().lower()

if confirm == "yes":
    try:
        print()
        print("Creating order...")
        
        # Create order
        order_args = OrderArgs(
            price=market['price'],
            size=size,
            side="buy",
            token_id=market['token_id']
        )
        
        print(f"[OK] Order args created")
        print("  Token: YES on Bitcoin $1M market")
        print("  Size: ${:.2f}".format(size))
        print()
        
        # Try to create the signed order
        print("Signing order...")
        signed_order = client.create_order(order_args)
        print("[OK] Order signed")
        print()
        
        # Post the order
        print("Submitting to Polymarket...")
        result = client.post_order(signed_order)
        
        print()
        print("="*60)
        print("✅ TRADE SUBMITTED!")
        print("="*60)
        print(f"Order ID: {result.get('orderID', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print()
        print("Check your Polymarket portfolio:")
        print("https://polymarket.com/portfolio")
        
    except Exception as e:
        print()
        print("="*60)
        print("❌ TRADE FAILED")
        print("="*60)
        print(f"Error: {e}")
        print()
        print("Possible issues:")
        print("- Insufficient USDC balance")
        print("- Token ID invalid or expired")
        print("- Market already resolved")
        print("- Price moved")
        print()
        import traceback
        traceback.print_exc()
else:
    print("Cancelled.")
