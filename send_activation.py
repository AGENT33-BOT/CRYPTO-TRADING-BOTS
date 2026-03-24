"""
Send test message to user's Telegram
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🤖 <b>ML Trading System Activated!</b> 🤖

✅ Telegram alerts connected
✅ Chat ID confirmed: 5804173449

<b>Active Bots:</b>
• ETH/USDT (90.72% accuracy)
• NEAR/USDT (84.28% accuracy)
• DOGE/USDT (91.35% accuracy)

<b>You will receive alerts for:</b>
🟢 Trade entries (BUY/SELL)
🔴 Trade exits
🧠 ML predictions
📊 Daily reports
🚨 Errors/issues

<b>Monitoring:</b> Every 15 minutes
<b>Risk:</b> 2% per trade, 3x leverage

System is LIVE and ready! 🚀
"""

reporter.send_message(message)
print("Activation message sent to Telegram!")
