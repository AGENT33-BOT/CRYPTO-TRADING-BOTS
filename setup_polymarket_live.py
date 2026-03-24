"""
Polymarket Live Trading Setup Helper
Guides you through enabling live trading
"""

import json
import os

def setup_live_trading():
    print("=" * 60)
    print("POLYMARKET LIVE TRADING SETUP")
    print("=" * 60)
    print()
    print("To enable LIVE trading, you need your Ethereum private key.")
    print()
    print("SECURITY WARNING:")
    print("   - Never share your private key with anyone")
    print("   - Store it securely")
    print("   - This script saves it locally in config file")
    print()
    print("How to get your Polymarket private key:")
    print("1. Go to https://polymarket.com/settings")
    print("2. Click 'Export Private Key'")
    print("3. Copy the key (starts with 0x...)")
    print()
    
    # Load existing config
    config_path = 'polymarket_config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        config = {"polymarket": {}}
    
    # Check if private key already exists
    existing_key = config.get('polymarket', {}).get('private_key', '')
    if existing_key:
        print(f"Private key already configured: {existing_key[:10]}...{existing_key[-6:]}")
        update = input("Update private key? (y/n): ").lower()
        if update != 'y':
            print("Keeping existing key.")
            return
    
    # Get private key from user
    print()
    print("Enter your Polymarket private key:")
    print("(Format: 0x followed by 64 hex characters)")
    private_key = input("Private key: ").strip()
    
    # Validate key format
    if not private_key.startswith('0x') or len(private_key) != 66:
        print("ERROR: Invalid private key format!")
        print("   Should be 0x + 64 hex characters = 66 total")
        return
    
    # Update config
    if 'polymarket' not in config:
        config['polymarket'] = {}
    
    config['polymarket']['private_key'] = private_key
    
    # Save config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print()
    print("=" * 60)
    print("SUCCESS: Private key saved!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart the Polymarket trading bot")
    print("2. It will now place REAL trades!")
    print()
    print("Risk settings:")
    print("   Max position: $50")
    print("   Max exposure: $200")
    print("   Min edge: 15%")
    print()
    print("WARNING: Only trade what you can afford to lose!")

if __name__ == "__main__":
    setup_live_trading()
