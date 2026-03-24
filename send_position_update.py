"""
Send position size update notification
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
⚙️ <b>POSITION SIZE UPDATED</b> ⚙️

📊 Old: 2% of balance per trade
📈 New: <b>20% of balance per trade</b>

💵 With $526 balance:
   • Old: ~$10 per trade
   • New: <b>~$105 per trade</b>

⚠️ Higher risk/reward!

All 3 ML bots restarted with new settings:
✅ ETH/USDT (PID: 25008)
✅ NEAR/USDT (PID: 1424)
✅ DOGE/USDT (PID: 23796)

Next trades will use 20% position size.
"""

reporter.send_message(message)
print("Position size update sent!")
