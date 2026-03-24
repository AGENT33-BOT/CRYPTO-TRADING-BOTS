"""
Fetch real Polymarket token IDs for active markets
"""

import requests
import json

GAMMA_URL = "https://gamma-api.polymarket.com"

print("="*60)
print("FETCHING ACTIVE POLYMARKET MARKETS")
print("="*60)
print()

# Get active markets
url = f"{GAMMA_URL}/markets"
params = {
    "active": "true",
    "closed": "false", 
    "limit": 20
}

response = requests.get(url, params=params)
markets = response.json() if isinstance(response.json(), list) else response.json().get('markets', [])

print(f"Found {len(markets)} markets\n")

# Filter for markets with valid clobTokenIds
crypto_markets = []
for market in markets:
    question = market.get('question', '')
    clob_ids = market.get('clobTokenIds', [])
    
    # Look for crypto markets
    if any(keyword in question.lower() for keyword in ['bitcoin', 'btc', 'crypto', 'ethereum', 'eth']):
        if clob_ids and len(clob_ids) >= 2:
            crypto_markets.append({
                'question': question,
                'condition_id': market.get('conditionId'),
                'yes_token': clob_ids[0],
                'no_token': clob_ids[1],
                'volume': market.get('volumeNum', 0),
                'liquidity': market.get('liquidityNum', 0)
            })

print("CRYPTO MARKETS WITH VALID TOKEN IDs:")
print("="*60)

for i, m in enumerate(crypto_markets[:5], 1):
    print(f"\n{i}. {m['question'][:60]}...")
    print(f"   Volume: ${m['volume']:,.0f}")
    print(f"   Liquidity: ${m['liquidity']:,.0f}")
    print(f"   YES Token: {m['yes_token']}")
    print(f"   NO Token: {m['no_token']}")

# Save to file
with open('market_token_ids.json', 'w') as f:
    json.dump(crypto_markets, f, indent=2)

print("\n" + "="*60)
print("Saved to: market_token_ids.json")
print("="*60)
