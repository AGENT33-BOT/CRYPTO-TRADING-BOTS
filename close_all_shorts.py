from pybit.unified_trading import HTTP

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

print("CLOSING ALL SHORTS — MARKET PUMPING")
print("=" * 50)

resp = session.get_positions(category='linear', settleCoin='USDT')

closed = 0
for pos in resp['result']['list']:
    symbol = pos['symbol']
    size = float(pos['size'])
    
    if size > 0:
        side = 'Sell' if pos['side'] == 'Buy' else 'Buy'
        print(f"Closing {symbol} {pos['side']} ({size} units)...")
        
        try:
            order = session.place_order(
                category='linear',
                symbol=symbol,
                side=side,
                orderType='Market',
                qty=str(size),
                reduceOnly=True
            )
            print(f"  [OK] CLOSED")
            closed += 1
        except Exception as e:
            print(f"  [ERR] Error: {str(e)[:40]}")

print(f"\n✓ Closed {closed} positions")
print("All shorts cut. Bots stopped until trend reverses.")
