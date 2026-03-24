"""
Sector Rotation Strategy
Rotate into sectors with strongest momentum
"""
import pandas as pd
import numpy as np
from typing import Optional, List
from alpaca_base_strategy import BaseStrategy, Signal

class SectorRotationStrategy(BaseStrategy):
    """Sector Rotation Momentum Strategy"""
    
    def __init__(self, config: dict):
        super().__init__('sector_rotation', config)
        self.sectors = config.get('sectors', [])
        self.momentum_lookback = config.get('momentum_lookback', 20)
        self.top_n = config.get('top_n', 3)
        self.position_size = config.get('position_size', 1000)
    
    def calculate_momentum(self, symbol: str) -> float:
        """Calculate momentum score for a sector"""
        df = self.get_historical_data(symbol, self.config.get('timeframe', '1d'), 
                                     limit=self.momentum_lookback + 5)
        if df.empty or len(df) < self.momentum_lookback:
            return 0
        
        # Rate of return over lookback period
        momentum = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
        return momentum
    
    def rank_sectors(self) -> List[tuple]:
        """Rank sectors by momentum"""
        sector_scores = []
        
        for sector in self.sectors:
            try:
                momentum = self.calculate_momentum(sector)
                sector_scores.append((sector, momentum))
            except Exception as e:
                self.logger.warning(f"Could not calculate momentum for {sector}: {e}")
        
        # Sort by momentum (descending)
        sector_scores.sort(key=lambda x: x[1], reverse=True)
        return sector_scores
    
    def generate_signals(self, symbol: str) -> Optional[Signal]:
        """Not used - sector rotation manages a portfolio"""
        return None
    
    def run(self):
        """Execute sector rotation"""
        if not self.enabled:
            return
        
        self.logger.info("Running sector rotation analysis...")
        
        # Rank sectors
        ranked = self.rank_sectors()
        
        if not ranked:
            self.logger.warning("No sector momentum data available")
            return
        
        # Log rankings
        self.logger.info("Sector Rankings (by momentum):")
        for i, (sector, momentum) in enumerate(ranked):
            self.logger.info(f"  {i+1}. {sector}: {momentum:+.2%}")
        
        # Top sectors to hold
        top_sectors = [s[0] for s in ranked[:self.top_n]]
        bottom_sectors = [s[0] for s in ranked[-self.top_n:]]
        
        # Get current positions
        positions = self.get_positions()
        
        # Close positions in bottom sectors
        for sector in bottom_sectors:
            if sector in positions:
                self.logger.info(f"Closing position in {sector} (weak momentum)")
                self.close_position(sector)
        
        # Open positions in top sectors
        for sector in top_sectors:
            if sector not in positions:
                self.logger.info(f"Opening position in {sector} (strong momentum)")
                # Get current price
                df = self.get_historical_data(sector, '1d', limit=5)
                if not df.empty:
                    price = df['close'].iloc[-1]
                    qty = int(self.position_size / price)
                    if qty >= 1:
                        from alpaca.trading.enums import OrderSide
                        self.submit_market_order(sector, OrderSide.BUY, qty)

if __name__ == '__main__':
    from alpaca_config import STRATEGY_CONFIGS
    strategy = SectorRotationStrategy(STRATEGY_CONFIGS['sector_rotation'])
    strategy.run()
