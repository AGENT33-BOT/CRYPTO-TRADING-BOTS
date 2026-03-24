"""
Telegram Trading Reporter
Sends ML trading reports and alerts to Telegram
"""

import requests
import json
from datetime import datetime
import os

class TelegramReporter:
    def __init__(self, bot_token, chat_id=None):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id or self._get_chat_id()
        
    def _get_chat_id(self):
        """Get chat ID from recent updates"""
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('result'):
                    # Get chat ID from first message
                    chat_id = data['result'][0]['message']['chat']['id']
                    return chat_id
        except Exception as e:
            print(f"Error getting chat ID: {e}")
        return None
    
    def send_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.chat_id:
            print("No chat ID available")
            return False
            
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"Failed to send: {response.text}")
                return False
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def send_trade_alert(self, symbol, action, price, size, confidence, pnl=None):
        """Send trade entry/exit alert"""
        emoji = "🟢" if action == "BUY" else "🔴"
        pnl_text = f"\n💰 P&L: <b>${pnl:.2f}</b>" if pnl else ""
        
        message = f"""
{emoji} <b>ML TRADE ALERT</b> {emoji}

📊 Symbol: <b>{symbol}</b>
🎯 Action: <b>{action}</b>
💵 Price: <b>${price:.2f}</b>
📈 Size: <b>{size} contracts</b>
🧠 Confidence: <b>{confidence:.1%}</b>{pnl_text}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        return self.send_message(message)
    
    def send_daily_report(self, trades, total_pnl, win_rate):
        """Send daily trading summary"""
        emoji = "🟢" if total_pnl >= 0 else "🔴"
        
        message = f"""
📊 <b>DAILY ML TRADING REPORT</b> 📊

📅 Date: {datetime.now().strftime('%Y-%m-%d')}
📈 Total Trades: <b>{trades}</b>
{emoji} Total P&L: <b>${total_pnl:.2f}</b>
🎯 Win Rate: <b>{win_rate:.1%}</b>

🤖 Active Bots:
• ETH/USDT (90.72% acc)
• NEAR/USDT (84.28% acc)
• DOGE/USDT (91.35% acc)

⏰ Report Time: {datetime.now().strftime('%H:%M:%S')} UTC
"""
        return self.send_message(message)
    
    def send_position_update(self, symbol, side, entry_price, current_price, size, unrealized_pnl):
        """Send position status update"""
        emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
        
        message = f"""
📍 <b>POSITION UPDATE</b> 📍

📊 Symbol: <b>{symbol}</b>
📌 Side: <b>{side}</b>
💵 Entry: <b>${entry_price:.2f}</b>
📊 Current: <b>${current_price:.2f}</b>
📈 Size: <b>{size} contracts</b>
{emoji} Unrealized P&L: <b>${unrealized_pnl:.2f}</b>

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        return self.send_message(message)
    
    def send_ml_signal(self, symbol, signal, confidence, prob_up, prob_down):
        """Send ML prediction signal"""
        emoji = "📈" if signal == "UP" else "📉"
        
        message = f"""
🧠 <b>ML PREDICTION</b> 🧠

📊 Symbol: <b>{symbol}</b>
{emoji} Signal: <b>{signal}</b>
🎯 Confidence: <b>{confidence:.1%}</b>

Probabilities:
📈 UP: <b>{prob_up:.1%}</b>
📉 DOWN: <b>{prob_down:.1%}</b>

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        return self.send_message(message)
    
    def send_error_alert(self, symbol, error_message):
        """Send error notification"""
        message = f"""
🚨 <b>BOT ERROR ALERT</b> 🚨

📊 Symbol: <b>{symbol}</b>
❌ Error: <code>{error_message}</code>

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
        return self.send_message(message)


# Test the bot
if __name__ == "__main__":
    BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
    
    print("Testing Telegram bot...")
    reporter = TelegramReporter(BOT_TOKEN)
    
    if reporter.chat_id:
        print(f"Chat ID: {reporter.chat_id}")
        reporter.send_message("""
🤖 <b>ML Trading Bot Connected</b> 🤖

✅ Telegram alerts activated
✅ Will receive trade signals & reports

Active pairs:
• ETH/USDT (90.72% accuracy)
• NEAR/USDT (84.28% accuracy)
• DOGE/USDT (91.35% accuracy)
""")
        print("Test message sent!")
    else:
        print("Failed to get chat ID. Send a message to the bot first.")
        print("Bot link: https://t.me/ml_trading_reporter_bot")
