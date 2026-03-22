"""
Risk Manager - Position sizing and risk management
"""

from typing import Dict, Optional


class RiskManager:
    """
    Risk management for trading
    - Max position size
    - Max daily loss
    - Max open positions
    - Risk per trade
    """
    
    def __init__(self):
        # Risk parameters
        self.max_position_size_percent = 20  # Max 20% of portfolio per trade
        self.max_daily_loss_percent = 5  # Max 5% daily loss
        self.max_open_positions = 3  # Max 3 open positions
        self.risk_per_trade_percent = 1  # 1% risk per trade
        
        # Daily tracking
        self.daily_pnl = 0
        self.daily_trades = 0
        self.daily_loss_count = 0
        
        # Position tracking
        self.open_positions = 0
    
    def check_risk(self, signal_score: Dict) -> tuple:
        """
        Check if signal passes risk management
        Returns: (allowed: bool, reason: str)
        """
        # Check max positions
        if self.open_positions >= self.max_open_positions:
            return False, "Max positions reached"
        
        # Check daily loss limit
        if self.daily_loss_count >= 2:
            return False, "Daily loss limit reached"
        
        # Check confidence
        confidence = signal_score.get('confidence', 0)
        if confidence < 60:
            return False, "Low confidence"
        
        return True, "OK"
    
    def calculate_position_size(self, confidence: float) -> float:
        """
        Calculate position size based on confidence
        Higher confidence = larger position
        """
        # Base size
        base_size = self.risk_per_trade_percent
        
        # Scale by confidence (60-90 range)
        confidence_factor = max(0, (confidence - 50) / 40)
        
        # Calculate final size
        size = base_size * (1 + confidence_factor * 2)
        
        # Cap at max
        return min(size, self.max_position_size_percent)
    
    def should_take_trade(self, signal: Dict, balance: float) -> tuple:
        """
        Final risk check before trade
        """
        # Check balance
        if balance < 100:
            return False, "Insufficient balance"
        
        # Check position size
        position_value = balance * (signal.get('size_percent', 10) / 100)
        if position_value > balance * (self.max_position_size_percent / 100):
            return False, "Position too large"
        
        return True, "OK"
    
    def update_daily_pnl(self, pnl: float):
        """Update daily PnL tracking"""
        self.daily_pnl += pnl
        self.daily_trades += 1
        
        if pnl < 0:
            self.daily_loss_count += 1
    
    def reset_daily(self):
        """Reset daily counters (call at start of new day)"""
        self.daily_pnl = 0
        self.daily_trades = 0
        self.daily_loss_count = 0
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'daily_loss_count': self.daily_loss_count,
            'open_positions': self.open_positions,
            'max_positions': self.max_open_positions,
            'risk_per_trade': self.risk_per_trade_percent
        }
    
    def emergency_stop(self) -> bool:
        """
        Check if emergency stop should trigger
        """
        # Stop if daily loss > 10%
        if self.daily_pnl < -10:
            return True
        
        # Stop if 3 consecutive losses
        if self.daily_loss_count >= 3:
            return True
        
        return False
