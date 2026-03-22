"""
Sentiment Analyzer - NLP-based News & Social Media Analysis
Uses news APIs and basic NLP to determine market sentiment
"""

import requests
import json
from typing import Dict, List
from datetime import datetime, timedelta
import re


class SentimentAnalyzer:
    """
    Analyzes news and social media sentiment
    Returns sentiment score from -1 (bearish) to +1 (bullish)
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Keywords for sentiment
        self.bullish_keywords = [
            'bullish', 'buy', 'upgrade', 'outperform', 'positive',
            'growth', 'profit', 'gain', 'rise', 'surge', 'rally',
            'breakout', 'support', 'breakthrough', 'partnership'
        ]
        
        self.bearish_keywords = [
            'bearish', 'sell', 'downgrade', 'underperform', 'negative',
            'loss', 'decline', 'drop', 'crash', 'fear', 'risk',
            'ban', 'lawsuit', 'fraud', 'scandal', 'bankruptcy'
        ]
    
    async def analyze(self, symbol: str) -> Dict:
        """
        Analyze sentiment for a symbol
        """
        # Check cache
        cache_key = f"{symbol}_{datetime.now().minute // 5}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_duration:
                return cached['data']
        
        # Fetch news (simulated - in production use news API)
        news = await self._fetch_news(symbol)
        
        # Analyze sentiment
        sentiment = self._analyze_text(news)
        
        # Cache result
        self.cache[cache_key] = {
            'data': sentiment,
            'timestamp': datetime.now()
        }
        
        return sentiment
    
    async def _fetch_news(self, symbol: str) -> List[str]:
        """
        Fetch recent news for symbol
        In production, integrate with:
        - CoinGecko API (free)
        - CryptoPanic API
        - NewsAPI
        - Twitter API
        """
        # Simulated news for demonstration
        # In production, make API calls
        
        news = [
            f"{symbol} announces new partnership",
            f"{symbol} reports strong quarterly earnings",
            f"Analysts upgrade {symbol} to buy rating",
            f"{symbol} sees increased trading volume"
        ]
        
        return news
    
    def _analyze_text(self, texts: List[str]) -> Dict:
        """
        Analyze text for sentiment using keyword matching
        """
        if not texts:
            return self._neutral_sentiment()
        
        bullish_count = 0
        bearish_count = 0
        
        for text in texts:
            text_lower = text.lower()
            
            for keyword in self.bullish_keywords:
                if keyword in text_lower:
                    bullish_count += 1
            
            for keyword in self.bearish_keywords:
                if keyword in text_lower:
                    bearish_count += 1
        
        total = bullish_count + bearish_count
        
        if total == 0:
            score = 0
        else:
            score = (bullish_count - bearish_count) / total
        
        # Determine sentiment
        if score > 0.3:
            label = 'BULLISH'
        elif score < -0.3:
            label = 'BEARISH'
        else:
            label = 'NEUTRAL'
        
        return {
            'score': round(score, 3),
            'label': label,
            'bullish_mentions': bullish_count,
            'bearish_mentions': bearish_count,
            'news_count': len(texts),
            'timestamp': datetime.now().isoformat()
        }
    
    def _neutral_sentiment(self) -> Dict:
        return {
            'score': 0,
            'label': 'NEUTRAL',
            'bullish_mentions': 0,
            'bearish_mentions': 0,
            'news_count': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_market_sentiment(self) -> Dict:
        """
        Get overall crypto market sentiment
        """
        # In production, analyze BTC, ETH news
        return await self.analyze('CRYPTO')
    
    def analyze_tweet(self, tweet: str) -> Dict:
        """
        Analyze a single tweet for sentiment
        """
        return self._analyze_text([tweet])
