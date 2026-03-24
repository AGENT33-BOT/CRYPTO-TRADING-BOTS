import ccxt

# Initialize exchange with hardcoded credentials (matching other bots)
exchange = ccxt.bybit({
    'apiKey': 'bsK06QDhsagOWwFsXQ',
    'secret': 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'adjustForTimeDifference': True,
    }
})
exchange.set_sandbox_mode(False)

# Load markets
exchange.load_markets()

# Check positions
positions = exchange.fetch_positions()

# Filter only non-zero positions
open_positions = []
for p in positions:
    contracts = float(p.get('contracts', 0) or 0)
    size = float(p.get('size', 0) or 0)
    if contracts != 0 or size != 0:
        open_positions.append(p)

if not open_positions:
    print("[OK] No open positions found")
else:
    print("[WARNING] Found {} open position(s):\n".format(len(open_positions)))
    for p in open_positions:
        symbol = p.get('symbol', 'Unknown')
        side = p.get('side', 'Unknown')
        contracts = p.get('contracts', '0')
        entry_price = p.get('entryPrice', 'Unknown')
        notional = p.get('notional', 'Unknown')
        print("Symbol: {}".format(symbol))
        print("Side: {}".format(side.upper()))
        print("Size: {} contracts".format(contracts))
        print("Entry Price: {}".format(entry_price))
        print("Notional: {}".format(notional))
        print("-" * 40)
