"""
Volatility Adapter - Dynamic TP/SL Based on ATR
Adjusts take profit and stop loss based on market volatility
"""

import numpy as np
from typing import Dict, List


class VolatilityAdapter:
    """
    Adjusts TP/SL based on Average True Range (ATR) volatility
    Higher volatility = wider TP/SL
    Lower volatility = tighter TP/SL
    """
    
    def __init__(self):
        self.atr_period = 14
        self.multipliers = {
            'low': 1.5,      # Tight TP/SL for low volatility
            'normal': 2.0,    # Normal
            'high': 2.5,      # Wide TP/SL for high volatility
            'extreme': 3.0   # Very wide for extreme volatility
        }
    
    def analyze(self, data: Dict) -> Dict:
        """
        Calculate volatility metrics
        """
        closes = data.get('closes', [])
        highs = data.get('highs', closes)
        lows = data.get('lows', closes)
        
        if len(closes) < self.atr_period + 1:
            return self._default_volatility()
        
        # Calculate True Range
        tr = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr.append(max(high_low, high_close, low_close))
        
        # ATR
        atr = np.mean(tr[-self.atr_period:])
        
        # ATR as percentage of price
        atr_pct = (atr / closes[-1]) * 100
        
        # Determine volatility regime
        if atr_pct < 1.0:
            regime = 'low'
        elif atr_pct < 2.5:
            regime = 'normal'
        elif atr_pct < 4.0:
            regime = 'high'
        else:
            regime = 'extreme'
        
        # Calculate recommended TP/SL
        multiplier = self.multipliers[regime]
        
        # TP: 2-3x ATR depending on regime
        recommended_tp = atr_pct * multiplier
        
        # SL: 1-1.5x ATR
        recommended_sl = atr_pct * (multiplier * 0.5)
        
        # Ensure minimums
        recommended_tp = max(recommended_tp, 1.5)
        recommended_sl = max(recommended_sl, 0.8)
        
        # Cap maximums
        recommended_tp = min(recommended_tp, 8.0)
        recommended_sl = min(recommended_sl, 4.0)
        
        return {
            'atr': round(atr, 4),
            'atr_percent': round(atr_pct, 2),
            'regime': regime,
            'recommended_tp': round(recommended_tp, 2),
            'recommended_sl': round(recommended_sl, 2),
            'trailing_stop': round(atr_pct * 0.5, 2)
        }
    
    def get_dynamic_tp_sl(self, entry_price: float, position: str, volatility: Dict) -> Dict:
        """
        Calculate exact TP/SL prices based on entry and volatility
        """
        tp_percent = volatility.get('recommended_tp', 2.5) / 100
        sl_percent = volatility.get('recommended_sl', 1.5) / 100
        
        if position.upper() == 'LONG':
            tp_price = entry_price * (1 + tp_percent)
            sl_price = entry_price * (1 - sl_percent)
        else:  # SHORT
            tp_price = entry_price * (1 - tp_percent)
            sl_price = entry_price * (1 + sl_percent)
        
        return {
            'entry': entry_price,
            'tp': round(tp_price, 4),
            'sl': round(sl_price, 4),
            'tp_percent': tp_percent * 100,
            'sl_percent': sl_percent * 100
        }
    
    def should_adjust_position(self, current_volatility: Dict, original_volatility: Dict) -> bool:
        """
        Check if position should be adjusted based on changing volatility
        """
        # If volatility regime changes significantly
        regimes = ['low', 'normal', 'high', 'extreme']
        
        current_idx = regimes.index(current_volatility.get('regime', 'normal'))
        original_idx = regimes.index(original_volatility.get('regime', 'normal'))
        
        # Adjust if moved more than 1 regime
        return abs(current_idx - original_idx) > 0
    
    def _default_volatility(self) -> Dict:
        return {
            'atr': 0,
            'atr_percent': 2.0,
            'regime': 'normal',
            'recommended_tp': 2.5,
            'recommended_sl': 1.5,
            'trailing_stop': 1.0
        }
