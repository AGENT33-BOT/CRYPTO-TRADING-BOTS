#!/usr/bin/env python3
"""
Public Channel Alert Cron Job
Posts best opportunities to public Telegram channel
"""

import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, 'C:\\Users\\digim\\clawd\\crypto_trader')

from public_channel_alerts import PublicChannelAlerts
from polymarket_channel_poster import post_to_public_channel

def run_polymarket_alerts():
    """Scan Polymarket and post top opportunities"""
    
    try:
        # Import and run polymarket scanner
        from polymarket_trader_enhanced import PolymarketTrader
        
        print("Scanning Polymarket for opportunities...")
        trader = PolymarketTrader(paper_trading=True)
        opportunities = trader.find_opportunities()
        
        if not opportunities:
            print("No opportunities found")
            # Still post scan results (shows activity)
            post_to_public_channel(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M ET"),
                markets_scanned=100,
                opportunities=[],
                trades_executed=0
            )
            return 0
        
        print(f"Found {len(opportunities)} opportunities")
        
        # Initialize public alerts for individual opportunities
        alerts = PublicChannelAlerts()
        
        # Post top opportunities individually (max 3)
        posted = 0
        for opp in opportunities[:3]:
            signal = opp.get('signal', '')
            if signal not in ['BUY_YES', 'SELL_YES']:
                continue
            
            success = alerts.alert_polymarket(
                market=opp.get('question', 'Unknown'),
                signal=signal,
                price=opp.get('yes_price', 0),
                edge=opp.get('edge', 0),
                category=opp.get('category', 'Unknown')
            )
            
            if success:
                posted += 1
        
        # ALSO post summary to channel
        post_to_public_channel(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M ET"),
            markets_scanned=100,
            opportunities=opportunities[:5],
            trades_executed=posted
        )
        
        print(f"Posted {posted} opportunities to public channel")
        return posted
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
        return 0

def run_portfolio_update():
    """Post portfolio status"""
    
    try:
        # Import Bybit checker
        import ccxt
        
        print("Fetching portfolio data...")
        
        # Connect to Bybit
        exchange = ccxt.bybit({
            'apiKey': 'YF5PhwXd6IGqsI1z8i',
            'secret': 'BtR1IWP32Sz01G3hHqjU1l68z5gi9dYB5rKC',
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        
        balance = exchange.fetch_balance()
        positions = exchange.fetch_positions()
        
        total_balance = balance['USDT']['free'] + balance['USDT']['used']
        
        # Calculate PnL
        total_pnl = 0
        open_positions = []
        
        for pos in positions:
            if pos['contracts'] != 0:
                pnl = float(pos.get('unrealizedPnl', 0))
                total_pnl += pnl
                open_positions.append({
                    'symbol': pos['symbol'],
                    'pnl': pnl
                })
        
        # Post to channel
        alerts = PublicChannelAlerts()
        success = alerts.send_portfolio_update(
            balance=total_balance,
            pnl=total_pnl,
            positions=open_positions
        )
        
        if success:
            print(f"Portfolio update posted: ${total_pnl:+.2f} P&L")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main entry point"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Public Channel Alerts')
    parser.add_argument('--mode', choices=['polymarket', 'portfolio', 'all'], 
                        default='polymarket',
                        help='What to post')
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"PUBLIC CHANNEL ALERTS - {datetime.now().strftime('%H:%M')}")
    print("=" * 60)
    
    if args.mode == 'polymarket':
        run_polymarket_alerts()
    elif args.mode == 'portfolio':
        run_portfolio_update()
    elif args.mode == 'all':
        run_polymarket_alerts()
        print()
        run_portfolio_update()
    
    print("=" * 60)

if __name__ == "__main__":
    main()
