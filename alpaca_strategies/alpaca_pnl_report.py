"""
Alpaca P&L Report
"""
import sys
sys.path.insert(0, '.')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
import alpaca_config as config

try:
    client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=True)
    account = client.get_account()
    
    print("=" * 50)
    print("ALPACA PAPER TRADING - P&L REPORT")
    print("=" * 50)
    print(f"Account Status: {account.status}")
    print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"Cash: ${float(account.cash):,.2f}")
    print(f"Buying Power: ${float(account.buying_power):,.2f}")
    print(f"Equity: ${float(account.equity):,.2f}")
    print(f"Last Equity: ${float(account.last_equity):,.2f}")
    
    pnl = float(account.equity) - float(account.last_equity)
    pnl_pct = (pnl / float(account.last_equity)) * 100 if float(account.last_equity) > 0 else 0
    
    emoji = "[+]" if pnl >= 0 else "[-]"
    print(f"\n{emoji} P&L Today: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
    
    # Get positions
    positions = client.get_all_positions()
    print(f"\n[Positions] Open: {len(positions)}")
    
    if positions:
        total_pnl = 0
        for pos in positions:
            pos_pnl = float(pos.unrealized_pl)
            total_pnl += pos_pnl
            emoji_pos = "[+]" if pos_pnl >= 0 else "[-]"
            print(f"  {emoji_pos} {pos.symbol}: {pos.qty} @ ${float(pos.avg_entry_price):.2f} | P&L: ${pos_pnl:+.2f}")
        print(f"\n[Total] Unrealized P&L: ${total_pnl:+.2f}")
    else:
        print("  No open positions")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
