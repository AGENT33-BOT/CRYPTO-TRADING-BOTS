"""
Send v2 bot confirmation
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🆕 <b>ML TRADER v2 DEPLOYED</b> 🆕

<b>What Changed:</b>
• Completely rewrote trading bot
• Hardcoded 20% position size
• Added debug output
• Fixed calculation logic

<b>New Bot PIDs:</b>
• ETH: 15132
• NEAR: 15008
• DOGE: 18080

<b>Next Trade Will Show:</b>
✅ Balance: $XXX
✅ 20% target: $XXX
✅ Contracts: XXX
✅ Total USD: $XXX

Watch for trades with debug info!
"""

reporter.send_message(message)
print("v2 deployment confirmed!")
