# Telegram Alert System for Bybit Trader
import requests
import time
from datetime import datetime

# Telegram Bot Configuration
import os
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8651591619:AAGulpeOt66s4TKXEsnDuL-lI2PWkM1G6Ao')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5804173449')

def send_telegram_alert(message):
    """Send alert to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False

# Alert templates
def alert_position_opened(symbol, entry, amount, stop_loss, take_profit):
    """Alert when position opened"""
    message = f"""
🟢 <b>POSITION OPENED</b>

Pair: <code>{symbol}</code>
Entry: ${entry:.2f}
Amount: {amount:.6f}
Stop Loss: ${stop_loss:.2f}
Take Profit: ${take_profit:.2f}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    send_telegram_alert(message)

def alert_position_closed(symbol, entry, exit_price, pnl, reason):
    """Alert when position closed"""
    emoji = "✅" if pnl > 0 else "❌"
    message = f"""
{emoji} <b>POSITION CLOSED</b>

Pair: <code>{symbol}</code>
Entry: ${entry:.2f}
Exit: ${exit_price:.2f}
PnL: ${pnl:.2f}
Reason: {reason}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    send_telegram_alert(message)

def alert_daily_summary(balance, daily_pnl, total_trades, win_rate):
    """Daily performance summary"""
    emoji = "📈" if daily_pnl >= 0 else "📉"
    message = f"""
{emoji} <b>DAILY TRADING SUMMARY</b>

Balance: ${balance:.2f}
Daily PnL: ${daily_pnl:.2f}
Total Trades: {total_trades}
Win Rate: {win_rate:.1f}%

Date: {datetime.now().strftime('%Y-%m-%d')}
"""
    send_telegram_alert(message)

def alert_error(error_msg):
    """Alert on errors"""
    message = f"""
⚠️ <b>TRADING ERROR</b>

Error: {error_msg}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    send_telegram_alert(message)
