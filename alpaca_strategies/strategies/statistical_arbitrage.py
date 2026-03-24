"""
Statistical Arbitrage Strategy
Multi-stock statistical arbitrage using Z-scores
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from alpaca_base_strategy import BaseStrategy, Signal

class StatisticalArbitrageStrategy(BaseStrategy):
    """Statistical Arbitrage Strategy"""
    
    def __init__(self, config: dict):
        super().__init__('statistical_arbitrage', config)
        self.universe = config.get('universe', [])
        self.lookback = config.get('lookback', 30)
        self.z_threshold = config.get('z_threshold', 1.5)
    
    def fetch_universe_data(self) -> pd.DataFrame:
        """Fetch data for all stocks in universe"""
        all_data = {}
        
        for symbol in self.universe:
            try:
                df = self.get_historical_data(symbol, self.config.get('timeframe', '1d'), 
                                             limit=self.lookback + 5)
                if not df.empty:
                    all_data[symbol] = df['close']
            except Exception as e:
                self.logger.warning(f"Could not fetch {symbol}: {e}")
        
        if not all_data:
            return pd.DataFrame()
        
        return pd.DataFrame(all_data)
    
    def calculate_residuals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate residuals from market regression"""
        # Use SPY as market proxy if available, otherwise equal-weighted index
        if 'SPY' in df.columns:
            market = df['SPY']
        else:
            market = df.mean(axis=1)
        
        residuals = pd.DataFrame(index=df.index)
        
        for symbol in df.columns:
            if symbol == 'SPY':
                continue
            
            # Linear regression: stock = alpha + beta * market
            stock = df[symbol]
            
            # Calculate beta
            covariance = stock.rolling(self.lookback).cov(market)
            market_var = market.rolling(self.lookback).var()
            beta = covariance / market_var
            
            # Calculate expected return
            expected = beta * market
            
            # Calculate residual (actual - expected)
            residuals[symbol] = stock - expected
        
        return residuals
    
    def calculate_zscores(self, residuals: pd.DataFrame) -> pd.DataFrame:
        """Calculate Z-scores of residuals"""
        zscores = pd.DataFrame(index=residuals.index)
        
        for symbol in residuals.columns:
            mean = residuals[symbol].rolling(self.lookback).mean()
            std = residuals[symbol].rolling(self.lookback).std()
            zscores[symbol] = (residuals[symbol] - mean) / std
        
        return zscores
    
    def generate_signals(self, symbol: str) -> Optional[Signal]:
        """Generate signals based on Z-score extremes"""
        # Fetch all data
        df = self.fetch_universe_data()
        if df.empty or len(df) < self.lookback:
            return None
        
        residuals = self.calculate_residuals(df)
        zscores = self.calculate_zscores(residuals)
        
        if symbol not in zscores.columns:
            return None
        
        if len(zscores) < 2:
            return None
        
        current_z = zscores[symbol].iloc[-1]
        prev_z = zscores[symbol].iloc[-2]
        
        # Z-score crossed above threshold (overvalued)
        if prev_z <= self.z_threshold and current_z > self.z_threshold:
            return Signal(
                symbol=symbol,
                direction='SHORT',
                confidence=min(95, 70 + (current_z - self.z_threshold) * 10),
                entry_price=df[symbol].iloc[-1],
                timestamp=df.index[-1],
                metadata={'zscore': current_z, 'residual': residuals[symbol].iloc[-1]}
            )
        
        # Z-score crossed below threshold (undervalued)
        if prev_z >= -self.z_threshold and current_z < -self.z_threshold:
            return Signal(
                symbol=symbol,
                direction='LONG',
                confidence=min(95, 70 + abs(current_z + self.z_threshold) * 10),
                entry_price=df[symbol].iloc[-1],
                timestamp=df.index[-1],
                metadata={'zscore': current_z, 'residual': residuals[symbol].iloc[-1]}
            )
        
        return None
    
    def run(self):
        """Run statistical arbitrage analysis"""
        if not self.enabled:
            return
        
        self.logger.info("Running statistical arbitrage analysis...")
        
        for symbol in self.universe:
            try:
                signal = self.generate_signals(symbol)
                if signal:
                    self.logger.info(f"Stat Arb signal: {signal.symbol} - {signal.direction}")
                    self.signals.append(signal)
                    self.execute_signal(signal)
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")

if __name__ == '__main__':
    from alpaca_config import STRATEGY_CONFIGS
    strategy = StatisticalArbitrageStrategy(STRATEGY_CONFIGS['statistical_arbitrage'])
    strategy.run()
