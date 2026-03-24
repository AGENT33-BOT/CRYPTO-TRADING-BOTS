"""
Z-Score Statistical Reversion Strategy
Statistical mean reversion using z-scores
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpaca_base_strategy import BaseStrategy, Signal, SignalType
from alpaca_config import AlpacaConfig


class ZScoreReversionStrategy(BaseStrategy):
    """
    Z-Score Statistical Mean Reversion Strategy.
    Uses statistical z-scores to identify extreme price deviations
    that are likely to revert to the mean.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        lookback_period: int = 20,
        entry_zscore: float = 2.0,  # Entry threshold
        exit_zscore: float = 0.5,   # Exit threshold
        use_volume_filter: bool = True,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="ZScore_Reversion"
        )
        self.lookback_period = lookback_period
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.use_volume_filter = use_volume_filter
        
        self.logger.info(
            f"Z-Score Strategy: period={lookback_period}, "
            f"entry_z={entry_zscore}, exit_z={exit_zscore}"
        )
    
    def calculate_zscore(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate rolling z-score of price"""
        df = data.copy()
        
        # Calculate rolling mean and std
        df['mean'] = df['close'].rolling(window=self.lookback_period).mean()
        df['std'] = df['close'].rolling(window=self.lookback_period).std()
        
        # Z-score
        df['zscore'] = (df['close'] - df['mean']) / df['std']
        
        # Rate of change z-score
        df['returns'] = df['close'].pct_change()
        df['returns_zscore'] = (df['returns'] - df['returns'].rolling(window=self.lookback_period).mean()) / df['returns'].rolling(window=self.lookback_period).std()
        
        # Volume z-score (to filter signals)
        if self.use_volume_filter and 'volume' in df.columns:
            df['volume_mean'] = df['volume'].rolling(window=self.lookback_period).mean()
            df['volume_std'] = df['volume'].rolling(window=self.lookback_period).std()
            df['volume_zscore'] = (df['volume'] - df['volume_mean']) / df['volume_std']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate z-score mean reversion signals"""
        signals = []
        
        if len(data) < self.lookback_period + 5:
            return signals
        
        df = self.calculate_zscore(data)
        
        # Previous values
        df['prev_zscore'] = df['zscore'].shift(1)
        
        # Get current and previous bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Entry conditions
        oversold_z = current['zscore'] < -self.entry_zscore  # Price far below mean
        overbought_z = current['zscore'] > self.entry_zscore   # Price far above mean
        
        # Mean reversion underway (z-score moving toward 0)
        reverting_up = current['zscore'] > prev['zscore']  # Was oversold, now recovering
        reverting_down = current['zscore'] < prev['zscore']  # Was overbought, now falling
        
        # Volume filter
        volume_ok = True
        if self.use_volume_filter and 'volume_zscore' in df.columns:
            volume_ok = current['volume_zscore'] > 0  # Above average volume
        
        # Buy signal: Z-score indicates oversold and starting to revert
        if oversold_z and reverting_up and volume_ok:
            stop_loss = current_price * 0.98
            take_profit = current['mean']
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'zscore': current['zscore'],
                    'mean': current['mean'],
                    'std': current['std'],
                    'returns_zscore': current['returns_zscore'],
                    'signal_type': 'zscore_oversold'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"Z-Score BUY signal for {symbol} at ${current_price:.2f} "
                f"(z: {current['zscore']:.2f})"
            )
        
        # Sell signal: Z-score indicates overbought and starting to revert
        elif overbought_z and reverting_down and volume_ok:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'zscore': current['zscore'],
                    'mean': current['mean'],
                    'signal_type': 'zscore_overbought'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"Z-Score SELL signal for {symbol} at ${current_price:.2f} "
                f"(z: {current['zscore']:.2f})"
            )
        
        # Exit when z-score returns to near mean
        exit_long = abs(current['zscore']) < self.exit_zscore
        if exit_long and not any(s.signal_type == SignalType.SELL for s in signals):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'zscore': current['zscore'],
                    'signal_type': 'zscore_mean_reached'
                }
            )
            signals.append(signal)
            self.logger.info(f"Z-Score Mean Exit for {symbol} (z: {current['zscore']:.2f})")
        
        # Bollinger Bands style mean reversion using z-scores
        # Entry at 2 std dev, exit at 0.5 std dev
        extreme_low = current['zscore'] < -2.5
        extreme_high = current['zscore'] > 2.5
        
        if extreme_low and not any(s.signal_type == SignalType.BUY for s in signals):
            stop_loss = current_price * 0.97
            take_profit = current['mean']
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'zscore': current['zscore'],
                    'signal_type': 'extreme_zscore'
                }
            )
            signals.append(signal)
            self.logger.info(f"Z-Score EXTREME BUY for {symbol} (z: {current['zscore']:.2f})")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Z-Score Reversion live trading")
        self.is_running = True
        
        from alpaca.trading.enums import OrderSide
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    data = self.get_historical_data(symbol, limit=30)
                    
                    if data.empty:
                        continue
                    
                    signals = self.generate_signals(data, symbol)
                    
                    for signal in signals:
                        if signal.signal_type == SignalType.BUY:
                            quantity = self.get_position_size(symbol, signal.price)
                            if quantity > 0:
                                self.submit_order(
                                    symbol=symbol,
                                    side=OrderSide.BUY,
                                    quantity=quantity,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit
                                )
                        
                        elif signal.signal_type == SignalType.SELL:
                            positions = self.get_open_positions()
                            if symbol in positions:
                                qty = abs(int(float(positions[symbol].qty)))
                                if qty > 0:
                                    self.submit_order(
                                        symbol=symbol,
                                        side=OrderSide.SELL,
                                        quantity=qty
                                    )
                
                import time
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error: {e}")
                import time
                time.sleep(60)
    
    def backtest(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        initial_capital: float = 100000.0
    ) -> Dict:
        """Run backtest"""
        from alpaca_backtester import Backtester
        
        backtester = Backtester(config=self.config)
        result = backtester.run_backtest(
            strategy=self,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        return result.to_dict()


if __name__ == "__main__":
    strategy = ZScoreReversionStrategy(
        symbols=['SPY', 'QQQ'],
        lookback_period=20,
        entry_zscore=2.0,
        exit_zscore=0.5
    )
    
    results = strategy.backtest()
    print(f"Z-Score Reversion Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
