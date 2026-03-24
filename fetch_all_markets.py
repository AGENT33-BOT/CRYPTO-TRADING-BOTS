"""
Fetch all active Polymarket markets
"""

import requests
import json

GAMMA_URL = "https://gamma-api.polymarket.com"

print("="*60)
print("FETCHING ACTIVE MARKETS")
print("="*60)
print()

# Get active markets
url = f"{GAMMA_URL}/markets"
params = {
    "active": "true",
    "closed": "false", 
    "limit": 50
}

response = requests.get(url, params=params)
data = response.json()

# Handle both list and dict formats
if isinstance(data, list):
    markets = data
else:
    markets = data.get('markets', [])

print(f"Found {len(markets)} markets\n")

# Show all markets with valid token IDs
valid_markets = []
for market in markets:
    question = market.get('question', '')
    
    # Parse clobTokenIds - it might be a string or list
    clob_ids_raw = market.get('clobTokenIds', '[]')
    
    # If it's a string, parse it as JSON
    if isinstance(clob_ids_raw, str):
        try:
            clob_ids = json.loads(clob_ids_raw)
        except:
            clob_ids = []
    else:
        clob_ids = clob_ids_raw
    
    if clob_ids and len(clob_ids) >= 2:
        valid_markets.append({
            'question': question,
            'condition_id': market.get('conditionId'),
            'yes_token': clob_ids[0],
            'no_token': clob_ids[1],
            'volume': market.get('volumeNum', 0),
            'liquidity': market.get('liquidityNum', 0)
        })

print(f"MARKETS WITH VALID CLOB TOKEN IDs ({len(valid_markets)}):")
print("="*60)

for i, m in enumerate(valid_markets[:10], 1):
    print(f"\n{i}. {m['question'][:60]}")
    print(f"   Volume: ${m['volume']:,.0f}")
    print(f"   YES Token: {m['yes_token']}")
    print(f"   NO Token: {m['no_token']}")

# Save to file
with open('all_market_ids.json', 'w') as f:
    json.dump(valid_markets, f, indent=2)

print("\n" + "="*60)
print("Top 3 markets for testing:")
print("="*60)

for i, m in enumerate(valid_markets[:3], 1):
    print(f"\n{i}. {m['question']}")
    print(f"   YES Token ID: {m['yes_token']}")
    print(f"   (Copy this for trading)")

print("\n" + "="*60)
print("Saved all to: all_market_ids.json")
print("="*60)
