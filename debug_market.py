"""Debug script to check Polymarket API structure"""
import requests
import json

gamma_url = "https://gamma-api.polymarket.com"

# Fetch markets
url = f"{gamma_url}/markets"
params = {"active": "true", "closed": "false", "limit": 5}

response = requests.get(url, params=params, timeout=30)
data = response.json()

markets = data if isinstance(data, list) else data.get('markets', [])

print("=" * 60)
print("MARKET STRUCTURE DEBUG")
print("=" * 60)

for market in markets[:3]:
    print("\nQuestion:", market.get('question', 'N/A')[:60])
    print("conditionId:", market.get('conditionId'))
    print("clobTokenIds:", market.get('clobTokenIds'))
    print("outcomes:", market.get('outcomes'))
    print("outcomePrices:", market.get('outcomePrices'))
    print("bestBid:", market.get('bestBid'))
    print("bestAsk:", market.get('bestAsk'))
    print("lastTradePrice:", market.get('lastTradePrice'))
    print("-" * 60)
