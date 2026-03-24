from pybit.unified_trading import HTTP

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

print("EMERGENCY: CLOSING ALL SHORTS IN BULL MARKET")
print("=" * 55)

resp = session.get_positions(category='linear', settleCoin='USDT')

closed = 0
total_pnl = 0

for pos in resp['result']['list']:
    symbol = pos['symbol']
    size = float(pos['size'])
    side = pos['side']
    
    if size > 0 and side == 'Sell':  # Close all SHORTS
        pnl = float(pos.get('unrealizedPnl', 0))
        total_pnl += pnl
        
        print(f"Closing {symbol} SHORT ({size} units, PnL: ${pnl:.2f})...")
        
        try:
            order = session.place_order(
                category='linear',
                symbol=symbol,
                side='Buy',
                orderType='Market',
                qty=str(size),
                reduceOnly=True
            )
            print(f"  [CLOSED]")
            closed += 1
        except Exception as e:
            print(f"  Error: {str(e)[:30]}")

print(f"\n✓ Closed {closed} SHORT positions")
print(f"Total PnL from closes: ${total_pnl:.2f}")
print("\nBOTS MUST BE STOPPED - They're shorting into a pump!")
