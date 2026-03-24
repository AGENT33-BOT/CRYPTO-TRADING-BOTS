"""
Send minimum size fix notification
"""

from telegram_reporter import TelegramReporter

BOT_TOKEN = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
CHAT_ID = "5804173449"

reporter = TelegramReporter(BOT_TOKEN, chat_id=CHAT_ID)

message = """
🔧 <b>MINIMUM SIZE FIX APPLIED</b> 🔧

<b>Problem:</b>
Bot calculated 20% but it was below Bybit minimum

<b>Solution:</b>
Now uses MAX of:
• 20% of balance (~$104)
• OR minimum required (~$35 for ETH)

<b>Example for ETH:</b>
• 20% of $520 = $104
• Minimum = $35
• Using: $104 (the larger)

<b>No more "ab not enough" errors!</b> ✅

Bots restarted with fix.
"""

reporter.send_message(message)
print("Fix notification sent!")
