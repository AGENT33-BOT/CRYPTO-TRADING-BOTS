"""
Send position closure notification
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🗑️ <b>SMALL POSITIONS CLOSED</b> 🗑️

Closed tiny positions:
• DOGE SHORT: 1 contract (~$1)
• NEAR SHORT: 1 contract (~$1)

<b>20% POSITION SIZE ACTIVE:</b>
• Balance: $520.69
• 20% per trade: <b>$104.14</b>
• With 3x leverage: ~$312

<b>Next Trades Will Be:</b>
• Proper $104 position size
• ~$312 total with leverage
• Much bigger than before!

ML bots ready with 20% sizing 🚀
"""

reporter.send_message(message)
print("Notification sent!")
