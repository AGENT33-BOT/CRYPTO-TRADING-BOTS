import ccxt
from datetime import datetime, timedelta
import json

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

print('=' * 80)
print('COMPLETE BYBIT TRADING ACCOUNT REPORT')
print(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 80)

# 1. Account Balance
try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    
    print('\n' + '=' * 80)
    print('ACCOUNT BALANCE')
    print('=' * 80)
    print(f'Total Balance:     ${usdt.get("total", 0):,.2f} USDT')
    print(f'Free (Available):  ${usdt.get("free", 0):,.2f} USDT')
    print(f'Used (Positions):  ${usdt.get("used", 0):,.2f} USDT')
except Exception as e:
    print(f'Error fetching balance: {e}')

# 2. Current Positions
try:
    print('\n' + '=' * 80)
    print('CURRENT OPEN POSITIONS')
    print('=' * 80)
    
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
               'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'DOT/USDT:USDT', 'BCH/USDT:USDT',
               'LINK/USDT:USDT', 'LTC/USDT:USDT', 'ATOM/USDT:USDT', 'ARB/USDT:USDT']
    
    positions_found = []
    total_unrealized = 0
    
    for symbol in symbols:
        try:
            positions = exchange.fetch_positions([symbol])
            if positions and len(positions) > 0:
                pos = positions[0]
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    entry = float(pos.get('entryPrice', 0))
                    mark = float(pos.get('markPrice', 0))
                    pnl = float(pos.get('unrealizedPnl', 0))
                    side = pos['side'].upper()
                    margin = float(pos.get('initialMargin', 0))
                    
                    positions_found.append({
                        'symbol': symbol.replace('/USDT:USDT', ''),
                        'side': side,
                        'size': contracts,
                        'entry': entry,
                        'mark': mark,
                        'pnl': pnl,
                        'margin': margin
                    })
                    total_unrealized += pnl
        except:
            pass
    
    if positions_found:
        for pos in positions_found:
            status = "PROFIT" if pos['pnl'] >= 0 else "LOSS"
            print(f"\n{pos['symbol']} {pos['side']}")
            print(f"  Size:     {pos['size']}")
            print(f"  Entry:    ${pos['entry']:.4f}")
            print(f"  Mark:     ${pos['mark']:.4f}")
            print(f"  PnL:      ${pos['pnl']:+.2f} ({status})")
            print(f"  Margin:   ${pos['margin']:.2f}")
        
        print(f"\nTotal Unrealized PnL: ${total_unrealized:+.2f}")
        print(f"Active Positions: {len(positions_found)}/5")
    else:
        print("No open positions")
        
except Exception as e:
    print(f'Error fetching positions: {e}')

# 3. Trading History
try:
    print('\n' + '=' * 80)
    print('TRADING HISTORY (Last 7 Days)')
    print('=' * 80)
    
    # Get trades from multiple symbols
    all_trades = []
    
    for symbol in symbols[:5]:  # Check top 5 symbols
        try:
            trades = exchange.fetch_my_trades(symbol, since=int((datetime.now() - timedelta(days=7)).timestamp() * 1000))
            all_trades.extend(trades)
        except:
            pass
    
    if all_trades:
        all_trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0
        total_fees = 0
        
        print(f"{'Time':<20} {'Symbol':<10} {'Side':<6} {'Amount':<12} {'Price':<12} {'PnL':<12} {'Fee':<10}")
        print('-' * 80)
        
        for trade in all_trades[:20]:  # Show last 20 trades
            time_str = datetime.fromtimestamp(trade['timestamp'] / 1000).strftime('%m-%d %H:%M')
            symbol = trade['symbol'].replace('/USDT:USDT', '')
            side = trade['side'].upper()
            amount = float(trade.get('amount', 0))
            price = float(trade.get('price', 0))
            fee = float(trade.get('fee', {}).get('cost', 0))
            
            # Try to get realized PnL
            pnl = 0
            if 'info' in trade and 'closedPnl' in trade['info']:
                pnl = float(trade['info']['closedPnl'])
            
            total_fees += fee
            
            if pnl > 0:
                wins += 1
                total_profit += pnl
            elif pnl < 0:
                losses += 1
                total_loss += abs(pnl)
            
            print(f"{time_str:<20} {symbol:<10} {side:<6} {amount:<12.4f} ${price:<11.2f} ${pnl:<11.2f} ${fee:<9.4f}")
        
        print('\n' + '=' * 80)
        print('TRADING STATISTICS')
        print('=' * 80)
        print(f'Total Trades (7d): {len(all_trades)}')
        print(f'Winning Trades:    {wins}')
        print(f'Losing Trades:     {losses}')
        print(f'Win Rate:          {(wins/max(1,wins+losses)*100):.1f}%')
        print(f'Total Profit:      +${total_profit:.2f}')
        print(f'Total Loss:        -${total_loss:.2f}')
        print(f'Net PnL:           ${(total_profit - total_loss):+.2f}')
        print(f'Total Fees:        ${total_fees:.4f}')
    else:
        print("No trades found in last 7 days")
        
except Exception as e:
    print(f'Error fetching trades: {e}')

# 4. Open Orders
try:
    print('\n' + '=' * 80)
    print('OPEN ORDERS')
    print('=' * 80)
    
    total_orders = 0
    for symbol in symbols:
        try:
            orders = exchange.fetch_open_orders(symbol)
            if orders:
                total_orders += len(orders)
                print(f"\n{symbol}: {len(orders)} orders")
                for o in orders:
                    print(f"  {o['type']} {o['side']} | Qty: {o['amount']} | Price: {o.get('price', 'MARKET')}")
        except:
            pass
    
    if total_orders == 0:
        print("No open orders")
    else:
        print(f"\nTotal Open Orders: {total_orders}")
        
except Exception as e:
    print(f'Error fetching orders: {e}')

# 5. Summary
print('\n' + '=' * 80)
print('ACCOUNT SUMMARY')
print('=' * 80)
print(f"Current Balance:     ${usdt.get('total', 0):,.2f} USDT")
print(f"Active Positions:    {len(positions_found) if 'positions_found' in locals() else 'N/A'}")
print(f"Unrealized PnL:      ${total_unrealized if 'total_unrealized' in locals() else 0:+.2f}")
print(f"7-Day Net PnL:       ${(total_profit - total_loss) if 'total_profit' in locals() else 0:+.2f}")
print(f"Total Fees (7d):     ${total_fees if 'total_fees' in locals() else 0:.4f}")
print('=' * 80)
