"""
Trade Notification Module for Telegram
Sends notifications when trades are executed
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"  # Agent33 Trading Bot
TELEGRAM_CHAT_ID = "5804173449"  # Your Telegram ID

def load_config():
    """Load Telegram config from file"""
    try:
        with open('telegram_config.json', 'r') as f:
            return json.load(f)
    except:
        return {'token': TELEGRAM_BOT_TOKEN, 'chat_id': TELEGRAM_CHAT_ID}

def send_telegram_notification(message, parse_mode='HTML'):
    """Send notification to Telegram"""
    try:
        config = load_config()
        token = config.get('token', TELEGRAM_BOT_TOKEN)
        chat_id = config.get('chat_id', TELEGRAM_CHAT_ID)
        
        if token == "YOUR_BOT_TOKEN":
            logger.warning("Telegram token not configured, skipping notification")
            return False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send Telegram notification: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return False

def notify_trade_opened(symbol, side, amount, entry, stop_loss, take_profit, bot_name="Trendline Bot"):
    """Notify when a position is opened"""
    emoji_side = "🟢 LONG" if side in ['LONG', 'Buy'] else "🔴 SHORT"
    emoji_bot = "📊" if "Trendline" in bot_name else "💱"
    
    message = f"""{emoji_bot} <b>Trade Opened - {bot_name}</b>

<b>{emoji_side}</b> {symbol}

💰 <b>Entry:</b> ${entry:.4f}
📦 <b>Amount:</b> {amount:.2f}
🛑 <b>Stop Loss:</b> ${stop_loss:.4f}
🎯 <b>Take Profit:</b> ${take_profit:.4f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    return send_telegram_notification(message)

def notify_trade_closed(symbol, side, entry, exit_price, pnl, reason, win_rate, bot_name="Trendline Bot"):
    """Notify when a position is closed"""
    emoji_pnl = "🟢" if pnl > 0 else "🔴"
    emoji_reason = "🎯" if "PROFIT" in reason else "🛑"
    emoji_bot = "📊" if "Trendline" in bot_name else "💱"
    
    message = f"""{emoji_bot} <b>Trade Closed - {bot_name}</b>

<b>{symbol}</b> ({side})

💰 <b>Entry:</b> ${entry:.4f}
💵 <b>Exit:</b> ${exit_price:.4f}
{emoji_pnl} <b>PnL:</b> ${pnl:.2f}
{emoji_reason} <b>Reason:</b> {reason}
📈 <b>Win Rate:</b> {win_rate:.1f}%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    return send_telegram_notification(message)

def notify_error(error_message, bot_name="Bot"):
    """Notify of errors"""
    message = f"""⚠️ <b>Error - {bot_name}</b>

<pre>{error_message}</pre>

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    return send_telegram_notification(message)

from datetime import datetime

if __name__ == "__main__":
    # Test notification
    notify_trade_opened(
        symbol="DOGEUSDT",
        side="LONG",
        amount=160.0,
        entry=0.103,
        stop_loss=0.0989,
        take_profit=0.1112,
        bot_name="Trendline Bot"
    )
