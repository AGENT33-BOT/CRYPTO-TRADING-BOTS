from crypto_signals_poster import CryptoChannelPoster, TELEGRAM_BOT_TOKEN, CHANNEL_ID
import requests
import json
from datetime import datetime

# Test the API directly
base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
url = f"{base_url}/sendMessage"

symbol = 'BTC/USDT'
side = 'LONG'
entry = 66000
target = 68000
stop = 65000
reason = 'Bitcoin showing support at $66k with bullish momentum building. Target $68k resistance.'

emoji = "🚀"
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

#Crypto #Trading #{symbol.replace('/', '')} #{side}"""

payload = {
    'chat_id': CHANNEL_ID,
    'text': message,
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    result = response.json()
    print(f"OK: {result.get('ok', False)}")
    if not result.get('ok'):
        print(f"Error: {result.get('description', 'Unknown error')}")
except Exception as e:
    print(f"Exception: {e}")
