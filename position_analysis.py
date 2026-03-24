import ccxt
import os

# Load API credentials
api_key = os.environ.get('BYBIT_API_KEY', '')
api_secret = os.environ.get('BYBIT_API_SECRET', '')

if not api_key or not api_secret:
    try:
        from config import API_KEY, API_SECRET
        api_key = API_KEY
        api_secret = API_SECRET
    except:
        pass

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'adjustForTimeDifference': True,
    }
})

positions = exchange.fetch_positions()
active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]

print("=" * 60)
print("POSITION ANALYSIS - POTENTIAL CUTS")
print("=" * 60)

total_pnl = 0
for pos in active_positions:
    symbol = pos['symbol']
    side = 'LONG' if pos['side'] == 'long' else 'SHORT'
    contracts = float(pos.get('contracts', 0))
    pnl = float(pos.get('unrealizedPnl', 0))
    entry = float(pos.get('entryPrice', 0))
    mark = float(pos.get('markPrice', 0))
    
    total_pnl += pnl
    
    # Calculate percent from entry
    if entry > 0:
        pct_change = ((mark - entry) / entry) * 100
        if side == 'SHORT':
            pct_change = -pct_change
    else:
        pct_change = 0
    
    status = ""
    if pnl < -3:
        status = "[CUT NOW]"
    elif pnl < -1:
        status = "[WATCH]"
    
    print(f"{symbol} {side}: {contracts} @ ${entry:.2f}")
    print(f"  Mark: ${mark:.2f} | P&L: ${pnl:.2f} ({pct_change:.2f}%) {status}")
    print()

print("=" * 60)
print(f"Total Unrealized P&L: ${total_pnl:.2f}")
print("=" * 60)
