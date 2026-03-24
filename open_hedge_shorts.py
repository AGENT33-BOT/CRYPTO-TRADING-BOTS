import ccxt
import json
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Best 80% confidence SHORTs from scan
shorts_to_open = [
    {'symbol': 'ETH/USDT:USDT', 'confidence': 80, 'entry': 1933.39},
    {'symbol': 'DOGE/USDT:USDT', 'confidence': 80, 'entry': 0.0914},
    {'symbol': 'LINK/USDT:USDT', 'confidence': 80, 'entry': 8.279}
]

print('=' * 60)
print('OPENING 80% CONFIDENCE SHORT POSITIONS')
print('=' * 60)

# Risk settings
RISK_PER_TRADE = 0.015  # 1.5%
STOP_LOSS_PCT = 0.02    # 2%
TAKE_PROFIT_PCT = 0.04  # 4%

# Get balance
balance = exchange.fetch_balance()
total_usdt = float(balance.get('USDT', {}).get('total', 0))
free_usdt = float(balance.get('USDT', {}).get('free', 0))

print(f"\nBalance: ${total_usdt:.2f} USDT")
print(f"Free: ${free_usdt:.2f} USDT")
print(f"Risk per trade: {RISK_PER_TRADE*100}%")
print()

opened_positions = []

for trade in shorts_to_open:
    symbol = trade['symbol']
    entry = trade['entry']
    
    try:
        # Calculate position size
        risk_amount = total_usdt * RISK_PER_TRADE
        stop_loss = entry * (1 + STOP_LOSS_PCT)
        stop_distance = abs(entry - stop_loss) / entry
        position_value = risk_amount / stop_distance
        
        # Get market info
        market = exchange.market(symbol)
        min_amount = market['limits']['amount']['min'] or 0.001
        
        # Calculate contracts
        contracts = position_value / entry
        if contracts < min_amount:
            contracts = min_amount * 2  # Use minimum + buffer
        
        # Round to precision
        amount_precision = market['precision']['amount']
        if amount_precision is None:
            amount_precision = 3
        contracts = round(contracts, int(amount_precision))
        
        print(f"Opening SHORT on {symbol}")
        print(f"  Entry: ${entry:.4f}")
        print(f"  Stop: ${stop_loss:.4f}")
        print(f"  Target: ${entry * (1 - TAKE_PROFIT_PCT):.4f}")
        print(f"  Size: {contracts}")
        print(f"  Confidence: {trade['confidence']}%")
        
        # Open position
        order = exchange.create_market_order(
            symbol=symbol,
            side='sell',
            amount=contracts
        )
        
        # Set TP/SL
        try:
            take_profit = entry * (1 - TAKE_PROFIT_PCT)
            exchange.create_order(
                symbol=symbol,
                type='limit',
                side='buy',
                amount=contracts,
                price=round(take_profit, 2),
                params={'reduceOnly': True}
            )
            
            # SL trigger
            exchange.create_order(
                symbol=symbol,
                type='market',
                side='buy',
                amount=contracts,
                price=None,
                params={
                    'triggerPrice': round(stop_loss, 2),
                    'triggerDirection': 'ascending',
                    'reduceOnly': True
                }
            )
        except Exception as e:
            print(f"  Warning: Could not set TP/SL: {e}")
        
        opened_positions.append({
            'symbol': symbol,
            'side': 'SHORT',
            'entry': entry,
            'size': contracts,
            'confidence': trade['confidence'],
            'order_id': order['id']
        })
        
        print(f"  [OK] Position opened: {order['id']}")
        print()
        
    except Exception as e:
        print(f"  [ERROR] {symbol}: {e}")
        print()

# Summary
print('=' * 60)
print('SUMMARY')
print('=' * 60)
print(f"Opened: {len(opened_positions)} SHORT positions")
for pos in opened_positions:
    print(f"  {pos['symbol']} | SHORT | {pos['confidence']}% conf | Size: {pos['size']}")

# Save to file
with open('hedge_positions.json', 'w') as f:
    json.dump({
        'time': datetime.now().isoformat(),
        'type': 'hedge_shorts_80pct',
        'positions': opened_positions
    }, f, indent=2)

print("\nSaved to: hedge_positions.json")
