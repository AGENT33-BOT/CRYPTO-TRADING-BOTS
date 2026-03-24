import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

balance = exchange.fetch_balance({'type': 'unified'})
usdt = balance.get('USDT', {})
print(f"USDT: {usdt.get('total', 0):.2f} total, {usdt.get('free', 0):.2f} free")

positions = exchange.fetch_positions()
active = [p for p in positions if float(p.get('contracts', 0)) != 0]
print(f"Positions: {len(active)} open")
total_pnl = 0
for pos in active:
    pnl = float(pos.get('unrealizedPnl', 0))
    total_pnl += pnl
    print(f"  {pos['symbol']} {pos['side']}: {pos['contracts']} @ {float(pos.get('entryPrice', 0)):.4f}, PnL: ${pnl:.2f}")
print(f"Total Unrealized PnL: ${total_pnl:.2f}")
