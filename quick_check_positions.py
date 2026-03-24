import ccxt

exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
exchange.load_markets()
positions = exchange.fetch_positions()
print('\n=== BYBIT MAIN ACCOUNT POSITIONS ===')
for p in positions:
    size = float(p.get('contracts') or 0)
    if size != 0:
        side = p['side'].upper()
        entry = float(p.get('entryPrice') or 0)
        mark = float(p.get('markPrice') or 0)
        pnl = float(p.get('unrealizedPnl') or 0)
        tp = p.get('takeProfit') or 'None'
        sl = p.get('stopLoss') or 'None'
        print(f"{p['symbol']}: {side} {size} @ {entry:.4f} | Mark: {mark:.4f} | PnL: ${pnl:.2f} | TP: {tp} | SL: {sl}")
