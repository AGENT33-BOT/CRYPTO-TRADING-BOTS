"""
Send 10% update notification
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
⚙️ <b>POSITION SIZE ADJUSTED</b> ⚙️

<b>Changed:</b> 20% → 10%

<b>Why:</b> Small positions using margin
<b>New Size:</b> ~$52 per trade (10% of ~$520)

<b>Benefits:</b>
✅ Trades will execute NOW
✅ Lower risk per trade
✅ More trades possible
✅ Works with current margin

<b>Bots Restarted:</b>
• ETH: ~$52 trades
• NEAR: ~$52 trades
• DOGE: ~$52 trades

Ready to trade! 🚀
"""

reporter.send_message(message)
print("10% adjustment sent!")
