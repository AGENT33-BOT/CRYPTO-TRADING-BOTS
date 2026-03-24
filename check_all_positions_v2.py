import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print('=' * 70)
print('FULL POSITION CHECK')
print('=' * 70)

# Method 1: Fetch all positions at once
try:
    all_positions = exchange.fetch_positions()
    print(f"\nMethod 1 - fetch_positions(): {len(all_positions)} raw entries")
    
    active_positions = []
    for pos in all_positions:
        contracts = float(pos.get('contracts', 0))
        if contracts > 0:
            active_positions.append(pos)
    
    print(f"Active positions: {len(active_positions)}")
    for pos in active_positions:
        symbol = pos['symbol']
        side = pos['side'].upper()
        entry = float(pos['entryPrice'])
        mark = float(pos['markPrice'])
        size = float(pos['contracts'])
        pnl = float(pos.get('unrealizedPnl', 0))
        print(f"  {symbol}: {side} | Size: {size} | Entry: ${entry:.4f} | Mark: ${mark:.4f} | PnL: ${pnl:+.2f}")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Check individual symbols
print('\n' + '=' * 70)
print('Method 2 - Individual Symbol Check')
print('=' * 70)

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 
           'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT']

found = 0
for symbol in symbols:
    try:
        pos_list = exchange.fetch_positions([symbol])
        for pos in pos_list:
            contracts = float(pos.get('contracts', 0))
            if contracts > 0:
                found += 1
                side = pos['side'].upper()
                entry = float(pos['entryPrice'])
                mark = float(pos['markPrice'])
                size = contracts
                pnl = float(pos.get('unrealizedPnl', 0))
                print(f"  {symbol}: {side} | Size: {size} | Entry: ${entry:.4f} | Mark: ${mark:.4f} | PnL: ${pnl:+.2f}")
    except Exception as e:
        pass

print(f"\nTotal active positions: {found}")

# Balance
print('\n' + '=' * 70)
balance = exchange.fetch_balance()
print(f"Balance: ${float(balance.get('USDT', {}).get('total', 0)):.2f} USDT")
print(f"Free: ${float(balance.get('USDT', {}).get('free', 0)):.2f} USDT")
print('=' * 70)
