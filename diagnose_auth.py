"""
Diagnose Polymarket CLOB Client Authentication Issue
"""
import json
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load config
with open('polymarket_config.json', 'r') as f:
    config = json.load(f)

pm_config = config.get('polymarket', {})
private_key = pm_config.get('private_key', '')
api_key = pm_config.get('api_key', '')
api_secret = pm_config.get('api_secret', '')
passphrase = pm_config.get('passphrase', '')

print("=" * 60)
print("CONFIGURATION CHECK")
print("=" * 60)
print(f"Private Key Present: {'Yes' if private_key else 'No'}")
print(f"Private Key Format: {'Valid (0x prefix, 66 chars)' if private_key.startswith('0x') and len(private_key) == 66 else 'INVALID'}")
print(f"API Key Present: {'Yes' if api_key else 'No'}")
print(f"API Secret Present: {'Yes' if api_secret else 'No'}")
print(f"Passphrase Present: {'Yes' if passphrase else 'No'}")
print()

# Test importing py_clob_client
try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds
    print("[OK] py_clob_client imported successfully")
    
    # Initialize client
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137,  # Polygon
        creds=ApiCreds(
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=passphrase
        )
    )
    print("[OK] ClobClient initialized")
    
    # Try to get API key details
    try:
        # Get API credentials status
        api_keys = client.get_api_keys()
        print(f"[OK] API Keys retrieved: {api_keys}")
    except Exception as e:
        print(f"[FAIL] API Keys check failed: {e}")
    
    # Try to get balance
    try:
        balance = client.get_balance()
        print(f"[OK] Balance retrieved: {balance}")
    except Exception as e:
        print(f"[FAIL] Balance check failed: {e}")
    
    # Try to get allowances
    try:
        allowances = client.get_allowances()
        print(f"[OK] Allowances retrieved: {allowances}")
    except Exception as e:
        print(f"[FAIL] Allowances check failed: {e}")
        
except ImportError as e:
    print(f"[FAIL] Failed to import py_clob_client: {e}")
    print("Run: pip install py-clob-client")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
