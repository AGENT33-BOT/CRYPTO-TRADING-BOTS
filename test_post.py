import requests
import json
from datetime import datetime

TELEGRAM_BOT_TOKEN = '8651591619:AAGulpeOt66s4TKXEsnDuL-lI2PWkM1G6Ao'
CHANNEL_ID = '@cryptoalphaalerts1'

url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
message = f"""📰 <b>CRYPTO NEWS</b>

<b>Bitcoin Holds Above $66K as Market Consolidates</b>

BTC continues to trade in a tight range above $66,000 following the recent rebound. Analysts are watching key resistance at $68,000 with support holding at $65,000. Trading volume remains elevated.

<i>Source: Market Analysis</i>

#Crypto #News #Bitcoin #Ethereum

<i>Posted: {datetime.now().strftime('%Y-%m-%d %H:%M')} EST</i>"""

payload = {'chat_id': CHANNEL_ID, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
response = requests.post(url, json=payload, timeout=30)
result = response.json()
print(f"Success: {result.get('ok', False)}")
if not result.get('ok'):
    print(f"Error: {result}")
else:
    print("News posted successfully!")
