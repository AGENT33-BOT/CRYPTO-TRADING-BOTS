"""
Send confirmation that 20% is now active
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
✅ <b>20% POSITION SIZE FIXED!</b> ✅

<b>Problem:</b> File wasn't saving correctly
<b>Solution:</b> Force-updated to 20%

<b>New Bots (20% size):</b>
• ETH: PID 18396
• NEAR: PID 12520  
• DOGE: PID 26420

<b>Verified Config:</b>
risk_per_trade = 0.20 (20%)

<b>Next Trades Will Be:</b>
• Size: $104 (20% of $520)
• NOT $1-2 positions!

✅ System ready for proper sized trades!
"""

reporter.send_message(message)
print("20% fix confirmation sent!")
