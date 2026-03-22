"""
Time Filter - Trading Hours & Volume Filter
Prevents trading during low liquidity periods
"""

from datetime import datetime, time
from typing import Dict


class TimeFilter:
    """
    Filters trades based on time and volume conditions
    - No trading during low volume periods (23:00-04:00 UTC)
    - No trading during major market closures
    - Weekend handling
    """
    
    def __init__(self):
        # Low volume hours (UTC) - typically 11 PM to 4 AM
        self.low_volume_start = 23
        self.low_volume_end = 4
        
        # Asian session (lower volume)
        self.asian_session_start = 0
        self.asian_session_end = 8
        
        # Major market hours (highest volume) - US session
        self.us_session_start = 14  # 2 PM UTC
        self.us_session_end = 21     # 9 PM UTC
    
    def is_trading_allowed(self) -> Dict:
        """
        Check if current time is suitable for trading
        """
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Check weekend
        if weekday >= 5:  # Saturday or Sunday
            return {
                'allowed': False,
                'reason': 'weekend',
                'session': 'closed'
            }
        
        # Check low volume hours
        if self._is_low_volume_hour(hour):
            return {
                'allowed': False,
                'reason': 'low_volume',
                'session': 'low_volume'
            }
        
        # Determine session
        session = self._get_session(hour)
        
        return {
            'allowed': True,
            'reason': 'active',
            'session': session,
            'hour': hour,
            'weekday': weekday
        }
    
    def _is_low_volume_hour(self, hour: int) -> bool:
        """Check if hour is low volume"""
        if self.low_volume_start > self.low_volume_end:
            # Crosses midnight
            return hour >= self.low_volume_start or hour < self.low_volume_end
        else:
            return self.low_volume_start <= hour < self.low_volume_end
    
    def _get_session(self, hour: int) -> str:
        """Determine trading session"""
        if self.asian_session_start <= hour < self.asian_session_end:
            return 'asian'
        elif self.us_session_start <= hour < self.us_session_end:
            return 'us'
        else:
            return 'overlap'
    
    def get_recommended_position_size(self, session: str) -> float:
        """
        Adjust position size based on session
        """
        sizes = {
            'asian': 0.5,      # Half size during Asian
            'overlap': 1.0,    # Normal during overlap
            'us': 1.0          # Full size during US
        }
        return sizes.get(session, 0.5)
    
    def should_use_tighter_sl(self) -> bool:
        """
        Whether to use tighter stop loss
        """
        now = datetime.utcnow()
        hour = now.hour
        
        # Tighter SL during low volume
        return self._is_low_volume_hour(hour)
    
    def get_next_trading_window(self) -> Dict:
        """
        Get next optimal trading time
        """
        now = datetime.utcnow()
        hour = now.hour
        
        # Find next US session start
        if hour < self.us_session_start:
            next_hour = self.us_session_start
            next_day = now.date()
        else:
            # Next day US session
            from datetime import timedelta
            next_day = now.date() + timedelta(days=1)
            next_hour = self.us_session_start
        
        return {
            'day': str(next_day),
            'hour': next_hour,
            'session': 'us'
        }
