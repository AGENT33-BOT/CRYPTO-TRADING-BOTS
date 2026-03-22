"""
Signal Aggregator - Combines Multiple Technical Indicators
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Moving Averages
- Volume Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class SignalAggregator:
    """Aggregates signals from multiple technical indicators"""
    
    def __init__(self):
        self.indicators = {
            'rsi': self._rsi,
            'macd': self._macd,
            'bollinger': self._bollinger_bands,
            'ma': self._moving_average,
            'volume': self._volume_analysis,
        }
    
    def analyze(self, data: Dict) -> Dict:
        """
        Analyze price data and generate combined signal
        """
        if not data or 'closes' not in data:
            return self._neutral_signal()
        
        closes = data['closes']
        volumes = data.get('volumes', [1] * len(closes))
        highs = data.get('highs', closes)
        lows = data.get('lows', closes)
        
        results = {}
        
        # Run all indicators
        results['rsi'] = self._rsi(closes)
        results['macd'] = self._macd(closes)
        results['bollinger'] = self._bollinger_bands(closes)
        results['ma'] = self._moving_average(closes)
        results['volume'] = self._volume_analysis(closes, volumes)
        
        # Aggregate signals
        buy_signals = 0
        sell_signals = 0
        
        for indicator, result in results.items():
            if result['signal'] == 'BUY':
                buy_signals += 1
            elif result['signal'] == 'SELL':
                sell_signals += 1
        
        # Determine overall signal
        total = buy_signals + sell_signals
        if total == 0:
            overall = 'NEUTRAL'
        elif buy_signals >= 3:
            overall = 'STRONG_BUY' if buy_signals >= 4 else 'BUY'
        elif sell_signals >= 3:
            overall = 'STRONG_SELL' if sell_signals >= 4 else 'SELL'
        else:
            overall = 'NEUTRAL'
        
        return {
            'indicator_scores': results,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'overall': overall,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def _rsi(self, closes: List[float], period: int = 14) -> Dict:
        """Calculate RSI"""
        if len(closes) < period + 1:
            return {'signal': 'NEUTRAL', 'value': 50, 'name': 'RSI'}
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi > 70:
            signal = 'SELL'
        elif rsi < 30:
            signal = 'BUY'
        else:
            signal = 'NEUTRAL'
        
        return {'signal': signal, 'value': round(rsi, 2), 'name': 'RSI'}
    
    def _macd(self, closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD"""
        if len(closes) < slow + signal:
            return {'signal': 'NEUTRAL', 'value': 0, 'name': 'MACD'}
        
        ema_fast = self._ema(closes, fast)
        ema_slow = self._ema(closes, slow)
        macd_line = ema_fast - ema_slow
        
        # Signal line (EMA of MACD)
        macd_values = []
        for i in range(len(closes) - slow + 1):
            macd_values.append(self._ema(closes[slow - 1:], signal))
        
        if len(macd_values) < 2:
            return {'signal': 'NEUTRAL', 'value': 0, 'name': 'MACD'}
        
        signal_line = macd_values[-1]
        
        if macd_line > signal_line and macd_line > 0:
            signal = 'BUY'
        elif macd_line < signal_line and macd_line < 0:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'value': round(macd_line, 4),
            'name': 'MACD'
        }
    
    def _bollinger_bands(self, closes: List[float], period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        if len(closes) < period:
            return {'signal': 'NEUTRAL', 'value': 0, 'name': 'BB'}
        
        recent = closes[-period:]
        sma = np.mean(recent)
        std = np.std(recent)
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        current = closes[-1]
        
        if current < lower:
            signal = 'BUY'  # Oversold
        elif current > upper:
            signal = 'SELL'  # Overbought
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'value': round((current - sma) / std if std > 0 else 0, 2),
            'name': 'BB',
            'upper': round(upper, 2),
            'lower': round(lower, 2),
            'middle': round(sma, 2)
        }
    
    def _moving_average(self, closes: List[float], short: int = 50, long: int = 200) -> Dict:
        """Calculate Moving Average Crossover"""
        if len(closes) < long:
            return {'signal': 'NEUTRAL', 'value': 0, 'name': 'MA'}
        
        ma_short = np.mean(closes[-short:])
        ma_long = np.mean(closes[-long:])
        
        if ma_short > ma_long:
            signal = 'BUY'
        elif ma_short < ma_long:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'value': round(ma_short - ma_long, 4),
            'name': 'MA'
        }
    
    def _volume_analysis(self, closes: List[float], volumes: List[float]) -> Dict:
        """Analyze volume trends"""
        if len(volumes) < 20:
            return {'signal': 'NEUTRAL', 'value': 1, 'name': 'Volume'}
        
        recent_vol = np.mean(volumes[-5:])
        avg_vol = np.mean(volumes[-20:])
        
        ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        # Price direction
        price_change = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
        
        if ratio > 1.5 and price_change > 0:
            signal = 'BUY'
        elif ratio > 1.5 and price_change < 0:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'signal': signal,
            'value': round(ratio, 2),
            'name': 'Volume'
        }
    
    def _ema(self, data: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return sum(data) / len(data)
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _neutral_signal(self) -> Dict:
        return {
            'indicator_scores': {},
            'buy_signals': 0,
            'sell_signals': 0,
            'overall': 'NEUTRAL',
            'timestamp': pd.Timestamp.now().isoformat()
        }
