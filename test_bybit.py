# Test Bybit connection
import ccxt

API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

print("="*60)
print("TESTING BYBIT CONNECTION")
print("="*60)

try:
    # Initialize Bybit
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        }
    })
    
    # Load markets
    exchange.load_markets()
    print("[OK] Connected to Bybit successfully")
    
    # Get balance
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    free = usdt.get('free', 0)
    total = usdt.get('total', 0)
    
    print(f"\n[OK] Balance fetched successfully")
    print(f"   USDT Total: ${total:.2f}")
    print(f"   USDT Free:  ${free:.2f}")
    
    if total > 0:
        print(f"\n[OK] Ready to trade with ${total:.2f}")
    else:
        print("\n[!] No USDT balance found")
        print("   Please deposit USDT to start trading")
    
    # Get BTC price
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"\n[OK] BTC Price: ${ticker['last']:.2f}")
    
    # Test order book
    orderbook = exchange.fetch_order_book('BTC/USDT', limit=5)
    print(f"[OK] Order book fetched")
    print(f"   Best Ask: ${orderbook['asks'][0][0]:.2f}")
    print(f"   Best Bid: ${orderbook['bids'][0][0]:.2f}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - READY TO TRADE!")
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    print("\n[!] Connection failed")
    print("   Please check API credentials")
