from bybit import bybit
api = bybit()
c = api.authenticated_client()
p = c.my_position(get='linear', symbol='BTCUSDT')['result']
print('BTC Position:')
for x in p:
    print(f"  Size: {x['size']}")
    print(f"  Entry: {x['entry_price']}")
    print(f"  TP: {x.get('take_profit', 'None')}")
    print(f"  SL: {x.get('stop_loss', 'None')}")
