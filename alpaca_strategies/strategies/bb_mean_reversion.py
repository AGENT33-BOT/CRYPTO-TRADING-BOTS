"""
Bollinger Bands Mean Reversion Strategy
Price reversal at Bollinger Bands extremes
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


class BBMeanReversionStrategy(BaseStrategy):
    """
    Bollinger Bands Mean Reversion Strategy.
    Buys when price touches lower band (oversold).
    Sells when price touches upper band (overbought).
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        period: int = 20,
        std_dev: float = 2.0,
        use_bb_width: bool = True,
        squeeze_threshold: float = 0.1,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="BB_MeanReversion"
        )
        self.period = period
        self.std_dev = std_dev
        self.use_bb_width = use_bb_width
        self.squeeze_threshold = squeeze_threshold
        
        self.logger.info(
            f"BB Mean Reversion: period={period}, std_dev={std_dev}"
        )
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = data.copy()
        
        # Middle band (SMA)
        df['middle_band'] = df['close'].rolling(window=self.period).mean()
        
        # Standard deviation
        df['std'] = df['close'].rolling(window=self.period).std()
        
        # Upper and lower bands
        df['upper_band'] = df['middle_band'] + (df['std'] * self.std_dev)
        df['lower_band'] = df['middle_band'] - (df['std'] * self.std_dev)
        
        # Band width (volatility indicator)
        df['band_width'] = (df['upper_band'] - df['lower_band']) / df['middle_band']
        df['band_width_sma'] = df['band_width'].rolling(window=self.period).mean()
        
        # %B indicator (position within bands)
        df['percent_b'] = (df['close'] - df['lower_band']) / (df['upper_band'] - df['lower_band'])
        
        # Squeeze detection
        df['squeeze'] = df['band_width'] < (df['band_width_sma'] * self.squeeze_threshold)
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate Bollinger Bands mean reversion signals"""
        signals = []
        
        if len(data) < self.period + 5:
            return signals
        
        df = self.calculate_bollinger_bands(data)
        
        # Previous values for cross detection
        df['prev_close'] = df['close'].shift(1)
        df['prev_lower'] = df['lower_band'].shift(1)
        df['prev_upper'] = df['upper_band'].shift(1)
        df['prev_percent_b'] = df['percent_b'].shift(1)
        
        # Get current and previous bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Touch lower band (potential buy)
        touch_lower = (current['close'] <= current['lower_band']) or (
            prev['close'] <= prev['lower_band'] and current['close'] > current['lower_band']
        )
        
        # Touch upper band (potential sell)
        touch_upper = (current['close'] >= current['upper_band']) or (
            prev['close'] >= prev['upper_band'] and current['close'] < current['upper_band']
        )
        
        # Buy signal: Price touches or crosses below lower band then reverts
        if touch_lower and current['percent_b'] < 0.05:
            # Ensure bands aren't in a squeeze (low volatility = less reliable)
            if not current['squeeze']:
                stop_loss = current['lower_band'] * 0.99
                take_profit = current['middle_band']
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'upper_band': current['upper_band'],
                        'middle_band': current['middle_band'],
                        'lower_band': current['lower_band'],
                        'percent_b': current['percent_b'],
                        'band_width': current['band_width'],
                        'signal_type': 'lower_band_bounce'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"BB BUY signal for {symbol} at ${current_price:.2f} "
                    f"(%B: {current['percent_b']:.2f})"
                )
        
        # Sell signal: Price touches or crosses above upper band
        elif touch_upper and current['percent_b'] > 0.95:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'percent_b': current['percent_b'],
                    'signal_type': 'upper_band_reversal'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"BB SELL signal for {symbol} at ${current_price:.2f} "
                f"(%B: {current['percent_b']:.2f})"
            )
        
        # Middle band crossover exit
        middle_cross_up = (prev['close'] < prev['middle_band']) and (current['close'] > current['middle_band'])
        if middle_cross_up and not any(s.signal_type == SignalType.SELL for s in signals):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'percent_b': current['percent_b'],
                    'signal_type': 'middle_band_target'
                }
            )
            signals.append(signal)
            self.logger.info(f"BB Middle Band exit for {symbol}")
        
        # Squeeze breakout (momentum continuation instead of reversion)
        if current['squeeze'] and prev['squeeze']:
            # Squeeze is forming - prepare for breakout
            pass
        elif prev['squeeze'] and not current['squeeze']:
            # Squeeze released - breakout
            if current['close'] > prev['upper_band']:
                # Bullish breakout - not a mean reversion signal
                pass
            elif current['close'] < prev['lower_band']:
                # Bearish breakout - not a mean reversion signal
                pass
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting BB Mean Reversion live trading")
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
    strategy = BBMeanReversionStrategy(
        symbols=['SPY', 'AAPL'],
        period=20,
        std_dev=2.0
    )
    
    results = strategy.backtest()
    print(f"BB Mean Reversion Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
