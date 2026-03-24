"""
Send error fix notification
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🔧 <b>BOT ERROR FIXED</b> 🔧

<b>Error:</b> "ab not enough for new order"

<b>Cause:</b> Position size below Bybit minimum

<b>Solution:</b> Updated calculation with minimum order sizes:
• ETH: min 0.01 ETH (~$38)
• NEAR: min 10 NEAR (~$13)
• DOGE: min 100 DOGE (~$9)

<b>Bots Restarted:</b>
• ETH: PID 21852
• NEAR: PID 25440
• DOGE: PID 512

<b>Next trades will calculate properly!</b> ✅
"""

reporter.send_message(message)
print("Fix notification sent!")
