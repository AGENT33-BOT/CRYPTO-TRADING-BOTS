"""
Send debug mode notification
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🔍 <b>DEBUG MODE ACTIVATED</b> 🔍

Running ML Trader v3 with FULL DEBUG output

<b>Watching:</b>
• Balance amount
• Position size calculation
• Contract math
• Actual USD value

<b>ETH Bot (Debug):</b> PID 19048

Will show every calculation step!
Check console window for live output.

Other bots (NEAR/DOGE) temporarily stopped.
"""

try:
    reporter.send_message(message)
    print("Debug notification sent!")
except:
    print("Could not send Telegram message")
