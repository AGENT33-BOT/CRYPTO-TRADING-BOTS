"""
Market Making Strategy
Capture spread by placing limit orders on both sides
"""
import pandas as pd
import numpy as np
from typing import Optional
from alpaca_base_strategy import BaseStrategy, Signal

class MarketMakingStrategy(BaseStrategy):
    """Basic Market Making Strategy"""
    
    def __init__(self, config: dict):
        super().__init__('market_making', config)
        self.spread_pct = config.get('spread_pct', 0.001)
        self.position_size = config.get('position_size', 500)
        self.active_orders = {}
    
    def calculate_quotes(self, current_price: float) -> tuple:
        """Calculate bid and ask prices"""
        half_spread = self.spread_pct / 2
        bid = current_price * (1 - half_spread)
        ask = current_price * (1 + half_spread)
        return bid, ask
    
    def generate_signals(self, symbol: str) -> Optional[Signal]:
        """Market making doesn't use traditional signals"""
        return None
    
    def run(self):
        """Manage market making orders"""
        if not self.enabled:
            return
        
        self.logger.info("Running market making strategy...")
        
        for symbol in self.config.get('symbols', []):
            try:
                # Get current price
                df = self.get_historical_data(symbol, '1m', limit=5)
                if df.empty:
                    continue
                
                current_price = df['close'].iloc[-1]
                bid, ask = self.calculate_quotes(current_price)
                
                # Calculate quantity
                qty = int(self.position_size / current_price)
                
                if qty >= 1:
                    self.logger.info(f"{symbol}: Bid ${bid:.2f} / Ask ${ask:.2f} (mid: ${current_price:.2f})")
                    
                    # In a real implementation, you would:
                    # 1. Cancel existing orders for this symbol
                    # 2. Place new bid and ask limit orders
                    # 3. Track fills and adjust inventory
                
            except Exception as e:
                self.logger.error(f"Error market making {symbol}: {e}")

if __name__ == '__main__':
    from alpaca_config import STRATEGY_CONFIGS
    strategy = MarketMakingStrategy(STRATEGY_CONFIGS['market_making'])
    strategy.run()
