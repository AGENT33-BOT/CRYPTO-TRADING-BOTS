"""
Correlation Detector - BTC & Market Correlation Analysis
Ensures trades align with market direction
"""

import requests
from typing import Dict, List


class CorrelationDetector:
    """
    Analyzes correlation with BTC and market direction
    - BTC as market leader
    - USDT as neutral
    - Altcoins follow BTC trends
    """
    
    def __init__(self):
        self.btc_symbols = ['BTCUSDT', 'BTC/USD', 'BTC-USDT']
        self.correlation_threshold = 0.6  # Minimum correlation required
    
    async def get_direction(self, symbol: str) -> Dict:
        """
        Check if trade aligns with market direction
        """
        # Get BTC direction
        btc_direction = await self._get_btc_direction()
        
        # Check if symbol is BTC
        is_btc = any(btc in symbol.upper() for btc in ['BTC'])
        
        if is_btc:
            return {
                'aligned': True,
                'btc_direction': btc_direction,
                'symbol_direction': btc_direction,
                'correlation': 1.0
            }
        
        # For altcoins, check correlation
        symbol_direction = await self._get_symbol_direction(symbol)
        
        # Determine alignment
        aligned = (btc_direction == symbol_direction) or (symbol_direction == 'SIDEWAYS')
        
        # Calculate correlation strength
        if btc_direction == symbol_direction:
            correlation = 0.8
        elif symbol_direction == 'SIDEWAYS':
            correlation = 0.5
        else:
            correlation = 0.2
        
        return {
            'aligned': aligned,
            'btc_direction': btc_direction,
            'symbol_direction': symbol_direction,
            'correlation': correlation,
            'recommendation': 'TRADE' if aligned else 'WAIT'
        }
    
    async def _get_btc_direction(self) -> str:
        """
        Determine BTC direction from recent candles
        """
        try:
            # Use public API
            r = requests.get(
                'https://api.bybit.com/v5/market/kline',
                params={
                    'category': 'linear',
                    'symbol': 'BTCUSDT',
                    'interval': '15',  # 15 min candles
                    'limit': 20
                },
                timeout=5
            )
            
            data = r.json().get('result', {}).get('list', [])
            
            if not data:
                return 'SIDEWAYS'
            
            # Calculate direction from last 20 candles
            closes = [float(c[4]) for c in data]
            
            # Simple trend: compare recent to older
            recent_avg = sum(closes[-10:]) / 10
            older_avg = sum(closes[:10]) / 10
            
            change = (recent_avg - older_avg) / older_avg * 100
            
            if change > 0.5:
                return 'UP'
            elif change < -0.5:
                return 'DOWN'
            else:
                return 'SIDEWAYS'
                
        except:
            return 'SIDEWAYS'
    
    async def _get_symbol_direction(self, symbol: str) -> str:
        """
        Determine individual symbol direction
        """
        try:
            # Clean symbol
            clean_symbol = symbol.replace('/', '').replace('-', '').upper()
            if not clean_symbol.endswith('USDT'):
                clean_symbol += 'USDT'
            
            r = requests.get(
                'https://api.bybit.com/v5/market/kline',
                params={
                    'category': 'linear',
                    'symbol': clean_symbol,
                    'interval': '15',
                    'limit': 20
                },
                timeout=5
            )
            
            data = r.json().get('result', {}).get('list', [])
            
            if not data:
                return 'SIDEWAYS'
            
            closes = [float(c[4]) for c in data]
            
            recent_avg = sum(closes[-10:]) / 10
            older_avg = sum(closes[:10]) / 10
            
            change = (recent_avg - older_avg) / older_avg * 100
            
            if change > 0.5:
                return 'UP'
            elif change < -0.5:
                return 'DOWN'
            else:
                return 'SIDEWAYS'
                
        except:
            return 'SIDEWAYS'
    
    async def get_market_overview(self) -> Dict:
        """
        Get overview of market correlation
        """
        btc = await self._get_btc_direction()
        
        # Major coins to check
        coins = ['ETH', 'SOL', 'BNB']
        directions = {}
        
        for coin in coins:
            directions[coin] = await self._get_symbol_direction(coin)
        
        # Calculate market sentiment
        up_count = sum(1 for d in directions.values() if d == 'UP')
        down_count = sum(1 for d in directions.values() if d == 'DOWN')
        
        if up_count >= 2:
            sentiment = 'BULLISH'
        elif down_count >= 2:
            sentiment = 'BEARISH'
        else:
            sentiment = 'MIXED'
        
        return {
            'btc_direction': btc,
            'coin_directions': directions,
            'market_sentiment': sentiment,
            'up_coins': up_count,
            'down_coins': down_count
        }
    
    def should_follow_btc(self, symbol: str) -> bool:
        """
        Determine if symbol typically follows BTC
        """
        # Most altcoins follow BTC
        # Exceptions: stablecoins, asset-backed tokens
        stablecoins = ['USDC', 'DAI', 'BUSD', 'USDT']
        
        return not any(s in symbol.upper() for s in stablecoins)
