# Test BTCC connection
import ccxt

API_KEY = "0c9622dc-3f87-43e4-ac6e-244486c45fb7"
API_SECRET = "08d64f86-682c-4def-849b-ec3b28913d6b"

print("Testing BTCC connection...")
print("="*50)

try:
    exchange = ccxt.btcc({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
    })
    
    # Load markets
    exchange.load_markets()
    print("✅ Markets loaded successfully")
    
    # Get balance
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = usdt.get('total', 0)
    free = usdt.get('free', 0)
    
    print(f"\n💰 USDT Balance:")
    print(f"   Total: ${total:.2f}")
    print(f"   Free:  ${free:.2f}")
    
    if total >= 70:
        print("\n✅ Balance check PASSED - Ready to trade!")
    else:
        print(f"\n⚠️  Balance is ${total}, expected $75")
        print("   Please deposit more USDT")
    
    # Get BTC price
    ticker = exchange.fetch_ticker('BTC/USDT')
    print(f"\n📊 BTC Price: ${ticker['last']:.2f}")
    
    print("\n" + "="*50)
    print("✅ CONNECTION SUCCESSFUL")
    print("Ready to start trading!")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPlease check:")
    print("- API credentials are correct")
    print("- BTCC account is active")
    print("- API permissions include 'Trade'")
