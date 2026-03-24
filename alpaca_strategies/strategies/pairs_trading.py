"""
Pairs Trading Strategy
Cointegration-based pairs trading
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple
from alpaca_base_strategy import BaseStrategy, Signal

class PairsTradingStrategy(BaseStrategy):
    """Pairs Trading (Statistical Arbitrage) Strategy"""
    
    def __init__(self, config: dict):
        super().__init__('pairs_trading', config)
        self.pairs = config.get('pairs', [])
        self.lookback = config.get('lookback', 60)
        self.z_threshold = config.get('z_threshold', 2.0)
        self.spread_data = {}  # Track spread for each pair
    
    def calculate_spread(self, stock_a: pd.DataFrame, stock_b: pd.DataFrame) -> pd.DataFrame:
        """Calculate spread between two stocks"""
        # Align dates
        df = pd.DataFrame({
            'a': stock_a['close'],
            'b': stock_b['close']
        }).dropna()
        
        # Calculate hedge ratio using linear regression
        df['ratio'] = df['a'] / df['b']
        df['hedge_ratio'] = df['ratio'].rolling(window=self.lookback).mean()
        
        # Calculate spread
        df['spread'] = df['a'] - (df['hedge_ratio'] * df['b'])
        
        # Z-score of spread
        df['spread_mean'] = df['spread'].rolling(window=self.lookback).mean()
        df['spread_std'] = df['spread'].rolling(window=self.lookback).std()
        df['zscore'] = (df['spread'] - df['spread_mean']) / df['spread_std']
        
        return df
    
    def generate_pair_signals(self, pair: Tuple[str, str]) -> Optional[Signal]:
        """Generate signals for a pair"""
        stock_a, stock_b = pair
        
        # Get data for both stocks
        df_a = self.get_historical_data(stock_a, self.config.get('timeframe', '1d'), 
                                        limit=self.lookback + 10)
        df_b = self.get_historical_data(stock_b, self.config.get('timeframe', '1d'), 
                                        limit=self.lookback + 10)
        
        if df_a.empty or df_b.empty or len(df_a) < self.lookback or len(df_b) < self.lookback:
            return None
        
        spread_df = self.calculate_spread(df_a, df_b)
        
        if len(spread_df) < 2:
            return None
        
        current = spread_df.iloc[-1]
        prev = spread_df.iloc[-2]
        
        # Spread is too high - short A, long B
        if current['zscore'] > self.z_threshold and prev['zscore'] <= self.z_threshold:
            return Signal(
                symbol=f"{stock_a}/{stock_b}",
                direction='PAIR_SHORT_A',
                confidence=min(95, 70 + (current['zscore'] - self.z_threshold) * 10),
                entry_price=current['a'],
                timestamp=df_a.index[-1],
                metadata={
                    'pair': pair,
                    'action': 'short_spread',
                    'zscore': current['zscore'],
                    'hedge_ratio': current['hedge_ratio'],
                    'stock_a': stock_a,
                    'stock_b': stock_b
                }
            )
        
        # Spread is too low - long A, short B
        if current['zscore'] < -self.z_threshold and prev['zscore'] >= -self.z_threshold:
            return Signal(
                symbol=f"{stock_a}/{stock_b}",
                direction='PAIR_LONG_A',
                confidence=min(95, 70 + abs(current['zscore'] + self.z_threshold) * 10),
                entry_price=current['a'],
                timestamp=df_a.index[-1],
                metadata={
                    'pair': pair,
                    'action': 'long_spread',
                    'zscore': current['zscore'],
                    'hedge_ratio': current['hedge_ratio'],
                    'stock_a': stock_a,
                    'stock_b': stock_b
                }
            )
        
        return None
    
    def generate_signals(self, symbol: str) -> Optional[Signal]:
        """Not used for pairs trading"""
        return None
    
    def run(self):
        """Run pairs trading analysis"""
        if not self.enabled:
            return
        
        self.logger.info("Running pairs trading analysis...")
        
        for pair in self.pairs:
            try:
                signal = self.generate_pair_signals(pair)
                if signal:
                    self.logger.info(f"Pair signal: {signal.symbol} - {signal.direction}")
                    self.signals.append(signal)
            except Exception as e:
                self.logger.error(f"Error analyzing pair {pair}: {e}")

if __name__ == '__main__':
    from alpaca_config import STRATEGY_CONFIGS
    strategy = PairsTradingStrategy(STRATEGY_CONFIGS['pairs_trading'])
    strategy.run()
