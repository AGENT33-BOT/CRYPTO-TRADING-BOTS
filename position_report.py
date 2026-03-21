"""
Position Report - Sends position report to Telegram every 30 mins
"""
import ccxt
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured")
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def get_report():
    exchange = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY'),
        'secret': os.getenv('BYBIT_API_SECRET'),
        'enableRateLimit': True,
    })
    
    # Get balance
    try:
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0)
    except:
        usdt_balance = "N/A"
    
    # Get closed PnL for today
    try:
        from datetime import datetime, timedelta
        start_ts = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
        pnl_response = exchange.privateGetV5PositionClosedPnl({'category': 'linear', 'limit': 50, 'startTime': start_ts})
        closed_list = pnl_response.get('result', {}).get('list', [])
        daily_pnl = sum(float(p.get('closedPnl', 0)) for p in closed_list)
    except:
        daily_pnl = 0
    
    # Get positions
    positions = exchange.fetch_positions()
    
    msg = f"POSITION REPORT - {datetime.now().strftime('%H:%M')}\n"
    msg += f"Balance: {usdt_balance} USDT\n"
    msg += f"Daily PnL: {daily_pnl:+.2f} USDT\n\n"
    
    total_pnl = 0
    open_count = 0
    
    for p in positions:
        if float(p.get('contracts', 0)) > 0:
            open_count += 1
            info = p.get('info', {})
            symbol = p['symbol'].replace('/USDT:USDT', '').replace('/USDT', '')
            side = p['side']
            size = p['contracts']
            entry = p.get('entryPrice')
            pnl_raw = p.get('unrealizedPnl')
            pnl = float(pnl_raw) if pnl_raw is not None else 0.0
            tp = info.get('takeProfit', 'N/A')
            sl = info.get('stopLoss', 'N/A')
            total_pnl += pnl
            
            emoji = "+" if pnl >= 0 else "-"
            msg += f"{symbol} {side.upper()}\n"
            msg += f"  Size: {size} | Entry: {entry}\n"
            msg += f"  P&L: {pnl:+.2f} | TP: {tp} | SL: {sl}\n\n"
    
    if open_count == 0:
        msg += "No open positions\n"
    
    msg += "="*30 + "\n"
    msg += f"Total Open P&L: {total_pnl:+.2f} USDT"
    
    return msg

if __name__ == "__main__":
    report = get_report()
    print("Position report sent")
    send_telegram(report)
