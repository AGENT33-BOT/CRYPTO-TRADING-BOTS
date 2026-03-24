"""
Crypto Signals and News Poster for Public Channel
Posts crypto trading setups and news to @cryptoalphaalerts1
"""

import requests
import json
from datetime import datetime
from typing import Optional, List, Dict

# Configuration
TELEGRAM_BOT_TOKEN = "8651591619:AAGulpeOt66s4TKXEsnDuL-lI2PWkM1G6Ao"
CHANNEL_ID = "@cryptoalphaalerts1"

class CryptoChannelPoster:
    """Posts crypto signals and news to public Telegram channel"""
    
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self.posted_items = set()
        self.load_history()
    
    def load_history(self):
        """Load posted items to prevent duplicates"""
        try:
            with open('crypto_channel_posts.json', 'r') as f:
                data = json.load(f)
                self.posted_items = set(data.get('posts', []))
        except:
            self.posted_items = set()
    
    def save_history(self):
        """Save posted items"""
        try:
            with open('crypto_channel_posts.json', 'w') as f:
                json.dump({'posts': list(self.posted_items)}, f)
        except:
            pass
    
    def send_message(self, message: str, parse_mode='HTML') -> bool:
        """Send message to Telegram channel"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': CHANNEL_ID,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.json().get('ok', False)
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def post_crypto_signal(self, symbol: str, side: str, entry: float, 
                           target: float, stop: float, reason: str = "") -> bool:
        """Post a crypto trading signal"""
        
        # Create unique ID
        post_id = f"signal_{symbol}_{side}_{datetime.now().strftime('%Y%m%d')}"
        if post_id in self.posted_items:
            print(f"Signal already posted today: {symbol}")
            return False
        
        emoji = "🚀" if side == "LONG" else "🩳"
        
        # Calculate risk/reward
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
        
        if self.send_message(message):
            self.posted_items.add(post_id)
            self.save_history()
            print(f"Signal posted: {symbol} {side}")
            return True
        return False
    
    def post_crypto_news(self, headline: str, summary: str, 
                         source: str = "", url: str = "") -> bool:
        """Post crypto news to channel"""
        
        post_id = f"news_{headline[:50]}_{datetime.now().strftime('%Y%m%d')}"
        if post_id in self.posted_items:
            print(f"News already posted: {headline[:50]}")
            return False
        
        message = f"""📰 <b>CRYPTO NEWS</b>

<b>{headline[:200]}</b>

{summary[:400]}

{f"<i>Source: {source}</i>" if source else ""}
{f"<a href='{url}'>Read more →</a>" if url else ""}

#Crypto #News #Bitcoin #Ethereum"""
        
        if self.send_message(message):
            self.posted_items.add(post_id)
            self.save_history()
            print(f"News posted: {headline[:60]}")
            return True
        return False
    
    def post_market_update(self, btc_price: float, eth_price: float, 
                          market_sentiment: str = "neutral") -> bool:
        """Post market update"""
        
        emoji = "🟢" if market_sentiment == "bullish" else "🔴" if market_sentiment == "bearish" else "⚪"
        
        message = f"""{emoji} <b>MARKET UPDATE</b>

<b>Bitcoin:</b> ${btc_price:,.2f}
<b>Ethereum:</b> ${eth_price:,.2f}
<b>Sentiment:</b> {market_sentiment.title()}

<i>Markets showing {market_sentiment} momentum
Stay positioned with proper risk management</i>

#Bitcoin #Ethereum #MarketUpdate"""
        
        return self.send_message(message)
    
    def post_daily_summary(self, signals_posted: int, news_posted: int) -> bool:
        """Post daily activity summary"""
        
        message = f"""📊 <b>DAILY CRYPTO ALPHA SUMMARY</b>
<i>{datetime.now().strftime('%B %d, %Y')}</i>

<b>Today's Activity:</b>
• Trading Signals: {signals_posted}
• News Updates: {news_posted}
• Markets Scanned: 100+

<b>Status:</b> All systems operational ✅

Join our community for real-time alerts!

#DailySummary #CryptoAlpha"""
        
        return self.send_message(message)


def main():
    """Test posting"""
    poster = CryptoChannelPoster()
    
    # Test crypto signal
    poster.post_crypto_signal(
        symbol="ETH/USDT",
        side="SHORT",
        entry=2042.00,
        target=1950.00,
        stop=2080.00,
        reason="Resistance at $2050, bearish divergence on 4H, funding rates turning negative. Shorting with tight stop above recent high."
    )
    
    # Test news
    poster.post_crypto_news(
        headline="Bitcoin Rebounds Above $66,800 as Majors Recover War-Driven Losses",
        summary="Bitcoin climbed back above $66,800 after a strong rebound from weekend lows near $63,000. Ethereum reclaimed $2,000 despite record staking of 37.1M ETH. Solana led with a 10.8% bounce.",
        source="CoinDesk / Coinpedia",
        url="https://coinpedia.org/news/crypto-news-today-live-updates-on-march-2-2026/"
    )
    
    # Test market update
    poster.post_market_update(
        btc_price=66780,
        eth_price=2000,
        market_sentiment="cautiously bullish"
    )


if __name__ == "__main__":
    main()
