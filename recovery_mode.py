from pybit.unified_trading import HTTP

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

print("AGENT33 RECOVERY MODE — OPENING LONG POSITIONS")
print("=" * 55)

# Get prices
tickers = session.get_tickers(category='linear', symbols='SOLUSDT,ETHUSDT,XRPUSDT')
prices = {}
for t in tickers['result']['list']:
    prices[t['symbol']] = float(t['lastPrice'])

print(f"SOL: ${prices['SOLUSDT']}")
print(f"ETH: ${prices['ETHUSDT']}")
print(f"XRP: ${prices['XRPUSDT']}")

# Deploy $40 each on top 3 performers
positions = [
    ('SOLUSDT', prices['SOLUSDT'], 0.5),  # $43 position
    ('ETHUSDT', prices['ETHUSDT'], 0.02), # ~$42 position
    ('XRPUSDT', prices['XRPUSDT'], 30),   # ~$44 position
]

for symbol, price, qty in positions:
    print(f"\n--- {symbol} ---")
    print(f"Entry: ${price} | Qty: {qty}")
    
    # Open LONG
    order = session.place_order(
        category='linear',
        symbol=symbol,
        side='Buy',
        orderType='Market',
        qty=str(qty)
    )
    print(f"Order: {order['result']['orderId'][:12]}...")
    
    # Set TP/SL
    tp = round(price * 1.08, 2)  # +8%
    sl = round(price * 0.95, 2)  # -5%
    
    session.set_trading_stop(
        category='linear',
        symbol=symbol,
        positionIdx=0,
        takeProfit=str(tp),
        stopLoss=str(sl),
        tpslMode='Full'
    )
    print(f"TP: ${tp} (+8%) | SL: ${sl} (-5%)")

print("\n✓ 3 LONG positions opened")
print("Recovery mode: ACTIVE")
