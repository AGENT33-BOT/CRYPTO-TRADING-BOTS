"""
Risk Parity Strategy
Allocate based on inverse risk (volatility)
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
from alpaca_base_strategy import BaseStrategy, Signal

class RiskParityStrategy(BaseStrategy):
    """Risk Parity Portfolio Strategy"""
    
    def __init__(self, config: dict):
        super().__init__('risk_parity', config)
        self.universe = config.get('universe', [])
        self.risk_lookback = config.get('risk_lookback', 60)
        self.target_volatility = config.get('target_volatility', 0.10)
    
    def calculate_volatility(self, symbol: str) -> float:
        """Calculate annualized volatility"""
        df = self.get_historical_data(symbol, self.config.get('timeframe', '1d'), 
                                     limit=self.risk_lookback + 5)
        if df.empty or len(df) < self.risk_lookback:
            return 0.20  # Default 20% vol
        
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        return volatility if volatility > 0 else 0.20
    
    def calculate_risk_parity_weights(self) -> Dict[str, float]:
        """Calculate risk parity weights (inverse volatility)"""
        volatilities = {}
        
        for symbol in self.universe:
            try:
                vol = self.calculate_volatility(symbol)
                volatilities[symbol] = vol
            except Exception as e:
                self.logger.warning(f"Could not calculate vol for {symbol}: {e}")
                volatilities[symbol] = 0.20
        
        # Inverse volatility weights
        inverse_vols = {s: 1/v for s, v in volatilities.items() if v > 0}
        total_inv_vol = sum(inverse_vols.values())
        
        weights = {s: w/total_inv_vol for s, w in inverse_vols.items()}
        
        return weights, volatilities
    
    def generate_signals(self, symbol: str) -> Optional[Signal]:
        """Not used for risk parity"""
        return None
    
    def run(self):
        """Execute risk parity allocation"""
        if not self.enabled:
            return
        
        self.logger.info("Calculating risk parity allocation...")
        
        weights, volatilities = self.calculate_risk_parity_weights()
        
        if not weights:
            self.logger.warning("No valid weights calculated")
            return
        
        # Log allocations
        self.logger.info("Risk Parity Allocation:")
        for symbol, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            vol = volatilities.get(symbol, 0)
            self.logger.info(f"  {symbol}: {weight:.1%} (vol: {vol:.1%})")
        
        # Get account info
        account = self.get_account()
        if not account:
            return
        
        total_equity = float(account.equity)
        positions = self.get_positions()
        
        # Adjust positions to target weights
        for symbol, target_weight in weights.items():
            target_value = total_equity * target_weight
            
            # Get current position value
            current_value = 0
            if symbol in positions:
                current_value = float(positions[symbol].market_value)
            
            diff = target_value - current_value
            
            # Check if adjustment needed
            if abs(diff) / total_equity > 0.02:  # 2% threshold
                # Get price
                df = self.get_historical_data(symbol, '1d', limit=5)
                if df.empty:
                    continue
                
                price = df['close'].iloc[-1]
                qty = abs(int(diff / price))
                
                if qty < 1:
                    continue
                
                from alpaca.trading.enums import OrderSide
                if diff > 0:  # Buy
                    self.logger.info(f"Buying {qty} shares of {symbol}")
                    self.submit_market_order(symbol, OrderSide.BUY, qty)
                else:  # Sell
                    self.logger.info(f"Selling {qty} shares of {symbol}")
                    self.submit_market_order(symbol, OrderSide.SELL, qty)

if __name__ == '__main__':
    from alpaca_config import STRATEGY_CONFIGS
    strategy = RiskParityStrategy(STRATEGY_CONFIGS['risk_parity'])
    strategy.run()
