from pybit.unified_trading import HTTP
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Load credentials from environment
api_key = os.getenv('BYBIT_API_KEY', '')
api_secret = os.getenv('BYBIT_API_SECRET', '')

session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

try:
    # Fetch closed PnL data from Bybit
    response = session.get_closed_pnl(category='linear', limit=100)
    closed_trades = response['result']['list']
    print("BYBIT CLOSED POSITIONS ANALYSIS")
    print("=" * 60)
    
    trades_by_symbol = {}
    total_pnl = 0
    
    for trade in closed_trades:
        symbol = trade['symbol']
        pnl = float(trade.get('closedPnl', 0))
        
        if symbol not in trades_by_symbol:
            trades_by_symbol[symbol] = {'win': 0, 'loss': 0, 'total_pnl': 0, 'count': 0}
        
        trades_by_symbol[symbol]['count'] += 1
        trades_by_symbol[symbol]['total_pnl'] += pnl
        total_pnl += pnl
        
        if pnl > 0:
            trades_by_symbol[symbol]['win'] += 1
        else:
            trades_by_symbol[symbol]['loss'] += 1
    
    print(f"\nTotal Realized PnL: ${total_pnl:.2f}")
    print(f"\n{'Symbol':<15} {'Trades':<8} {'Wins':<6} {'Losses':<7} {'Win Rate':<10} {'Total PnL':<12}")
    print("-" * 60)
    
    winners = []
    losers = []
    
    for symbol, data in sorted(trades_by_symbol.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
        total = data['count']
        wins = data['win']
        losses = data['loss']
        wr = (wins/total*100) if total > 0 else 0
        pnl = data['total_pnl']
        
        print(f"{symbol:<15} {total:<8} {wins:<6} {losses:<7} {wr:.1f}%{'':<5} ${pnl:.2f}")
        
        if pnl > 0:
            winners.append(symbol)
        else:
            losers.append(symbol)
    
    print("\n" + "=" * 60)
    print(f"\nWINNING PAIRS ({len(winners)}): {', '.join(winners)}")
    print(f"LOSING PAIRS ({len(losers)}): {', '.join(losers)}")
    print(f"\nRECOMMENDATION: Trade ONLY: {', '.join(winners[:5])}")
    print(f"AVOID: {', '.join(losers[:5])}")
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
