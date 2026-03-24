"""
Send restart confirmation
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🔄 <b>ML BOTS RESTARTED</b> 🔄

❌ Killed old bots (using 2% size)
✅ Started new bots (using 20% size)

<b>New Bot PIDs:</b>
• ETH/USDT: 22640 (20% size)
• NEAR/USDT: 19360 (20% size)
• DOGE/USDT: 23824 (20% size)

<b>Next trades will be:</b>
• Size: ~$104 (20% of balance)
• NOT the tiny $1 positions!

⚠️ <b>Close any small positions manually</b>
Then wait for proper 20% sized trades.

System ready! 🚀
"""

reporter.send_message(message)
print("Restart notification sent!")
