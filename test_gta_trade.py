"""
Test paper trade simulation for GTA VI opportunity
"""
from polymarket_trader import PolymarketTrader
import json

trader = PolymarketTrader(paper_trading=True)

# Simulate the GTA VI opportunity mentioned in task
gta_opportunity = {
    'market_id': '0x1234567890abcdef',  # Mock ID
    'question': 'GTA VI released before June 2026?',
    'signal': 'BUY_YES',
    'edge': 0.229,  # 22.9% edge
    'yes_price': 0.0210,  # ~0.0210 as mentioned
    'no_price': 0.979,
    'yes_token_id': '75467129615908319583031474642692685988828937753668038836944412829948447524427',
    'no_token_id': '38429637202672672869706423368621606232945267268875161785431798958426456868324',
    'volume': 150000,
    'liquidity': 25000,
    'implied_probability': 0.021,
    'end_date': '2026-06-01T00:00:00Z'
}

print("=" * 60)
print("PAPER TRADE TEST - GTA VI OPPORTUNITY")
print("=" * 60)
print(f"Market: {gta_opportunity['question']}")
print(f"Signal: {gta_opportunity['signal']}")
print(f"Edge: {gta_opportunity['edge']*100:.1f}%")
print(f"YES Price: ${gta_opportunity['yes_price']:.4f}")
print(f"Token ID: {gta_opportunity['yes_token_id'][:30]}...")
print("-" * 60)

# Test place_order in paper mode
result = trader.place_order(
    market_id=gta_opportunity['market_id'],
    side='buy',
    size=20.0,
    price=gta_opportunity['yes_price'],
    token_id=gta_opportunity['yes_token_id']
)

print("\nPaper Trade Result:")
print(json.dumps(result, indent=2))

if result.get('paper_trade'):
    print("\n[OK] Paper trade simulated successfully!")
    print(f"Order ID: {result['orderId']}")
    print(f"Status: {result['status']}")
    print("\nNote: No real money was spent. This was a simulation.")
else:
    print("\n[FAIL] Paper trade failed")
