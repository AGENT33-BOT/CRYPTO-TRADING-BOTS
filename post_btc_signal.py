from crypto_signals_poster import CryptoChannelPoster
from datetime import datetime

p = CryptoChannelPoster()

# Check if already posted today
symbol = 'BTC/USDT'
side = 'LONG'
post_id = f"signal_{symbol}_{side}_{datetime.now().strftime('%Y%m%d')}"
print(f"Post ID: {post_id}")
print(f"Already posted: {post_id in p.posted_items}")

# Post the signal
result = p.post_crypto_signal(
    symbol='BTC/USDT',
    side='LONG',
    entry=66000,
    target=68000,
    stop=65000,
    reason='Bitcoin showing support at $66k with bullish momentum building. Target $68k resistance.'
)
print(f"Posted successfully: {result}")
