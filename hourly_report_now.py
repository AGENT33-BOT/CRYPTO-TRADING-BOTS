import ccxt

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print("="*60)
print("BYBIT HOURLY TRADING REPORT")
print("Monday, February 9th, 2026 - 5:15 PM ET")
print("="*60)
print()

# Get balance
try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    total = float(usdt.get('total', 0))
    free = float(usdt.get('free', 0))
    used = float(usdt.get('used', 0))
    
    print("💰 ACCOUNT BALANCE")
    print(f"   Total:     ${total:.2f} USDT")
    print(f"   Available: ${free:.2f} USDT")
    print(f"   In Positions: ${used:.2f} USDT")
    print()
except Exception as e:
    print(f"Error fetching balance: {e}")
    total = 0

# Get positions
print("📊 OPEN POSITIONS")
print("-"*60)

try:
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 
               'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'NEAR/USDT:USDT', 'LINK/USDT:USDT',
               'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT',
               'ETC/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT']
    
    total_pnl = 0
    position_count = 0
    positions_data = []
    
    for symbol in symbols:
        try:
            positions = exchange.fetch_positions([symbol])
            for pos in positions:
                contracts = float(pos.get('contracts', 0))
                if contracts != 0:
                    position_count += 1
                    side = pos['side'].upper()
                    entry = float(pos.get('entryPrice', 0))
                    mark = float(pos.get('markPrice', 0))
                    pnl = float(pos.get('unrealizedPnl', 0))
                    pnl_pct = float(pos.get('percentage', 0))
                    total_pnl += pnl
                    positions_data.append({
                        'symbol': symbol.replace('/USDT:USDT', ''),
                        'side': side,
                        'entry': entry,
                        'mark': mark,
                        'size': contracts,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
        except:
            pass
    
    if positions_data:
        for p in positions_data:
            emoji = "🟢" if p['pnl'] >= 0 else "🔴"
            print(f"   {emoji} {p['symbol']} {p['side']}")
            print(f"      Size: {p['size']} | Entry: ${p['entry']:.4f} | Mark: ${p['mark']:.4f}")
            print(f"      PnL: ${p['pnl']:+.2f} ({p['pnl_pct']:+.2f}%)")
            print()
    else:
        print("   No open positions")
        print()
    
    pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
    print("-"*60)
    print(f"📈 Total Positions: {position_count}")
    print(f"📈 Total Unrealized PnL: {pnl_emoji} ${total_pnl:+.2f} USDT")
    
except Exception as e:
    print(f"Error fetching positions: {e}")

# Account Value
print()
print("="*60)
print("📋 SUMMARY")
print("="*60)
account_value = total + total_pnl
print(f"   Account Value: ~${account_value:.2f} USDT")
print(f"   Open Positions: {position_count}")
print(f"   Unrealized PnL: ${total_pnl:+.2f} USDT")
print()
print("🤖 Bot Status: Check process logs for detailed status")
print("="*60)
