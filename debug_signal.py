from crypto_signals_poster import CryptoChannelPoster
import requests
from datetime import datetime

TELEGRAM_BOT_TOKEN = "8651591619:AAGulpeOt66sTKXEsnDuL-lI2PWkM1G6Ao"
CHANNEL_ID = "@cryptoalphaalerts1"

# Test API connection first
base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
print(f"Testing bot API...")

try:
    response = requests.get(f"{base_url}/getMe", timeout=30)
    print(f"Bot info response: {response.json()}")
except Exception as e:
    print(f"Error connecting to bot API: {e}")

# Now try posting
p = CryptoChannelPoster()

symbol = 'BTC/USDT'
side = 'LONG'
post_id = f"signal_{symbol}_{side}_{datetime.now().strftime('%Y%m%d')}"
print(f"\nPost ID: {post_id}")
print(f"Already posted: {post_id in p.posted_items}")

# Build message manually to debug
emoji = "🚀"
entry = 66000
target = 68000
stop = 65000
reason = "Bitcoin showing support at $66k with bullish momentum building. Target $68k resistance."

risk = abs(entry - stop)
reward = abs(target - entry)
rr_ratio = reward / risk if risk > 0 else 0

message = f"""{emoji} <b>CRYPTO SIGNAL</b>

<b>Symbol:</b> {symbol}
<b>Side:</b> {side}
<b>Entry:</b> ${entry:.4f}
<b>Target:</b> ${target:.4f} (+{(reward/entry)*100:.2f}%)
<b>Stop Loss:</b> ${stop:.4f} ({(risk/entry)*100:.2f}%)
<b>R:R Ratio:</b> 1:{rr_ratio:.1f}

<b>Analysis:</b>
{reason[:250]}

⚠️ <i>Always use stop losses
Not financial advice - DYOR</i>

#Crypto #Trading #BTCUSDT #LONG"""

print(f"\nSending message to {CHANNEL_ID}...")
try:
    url = f"{base_url}/sendMessage"
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    response = requests.post(url, json=payload, timeout=30)
    result = response.json()
    print(f"Response: {result}")
    if result.get('ok'):
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Failed: {result.get('description', 'Unknown error')}")
except Exception as e:
    print(f"❌ Error: {e}")
