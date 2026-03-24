from bybit_api import get_client
client = get_client()
acc = client.get_wallet_balance(accountType='UNIFIED')
print('Balance:', acc['result']['list'][0]['totalAvailableBalance'])
print('Wallet Balance:', acc['result']['list'][0]['walletBalance'])
pos = client.get_positions(category='linear', settleCoin='USDT')
print('Positions:', len(pos['result']['list']))
for p in pos['result']['list']:
    if float(p['size']) > 0:
        print(f"  {p['symbol']}: {p['side']} {p['size']} @ {p['avgPrice']} PnL: {p['unrealizedPnl']}")
