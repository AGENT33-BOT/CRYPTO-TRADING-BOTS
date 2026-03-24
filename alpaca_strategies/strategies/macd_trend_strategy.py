"""
MACD Trend Strategy
Moving Average Convergence Divergence strategy
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


class MACDTrendStrategy(BaseStrategy):
    """
    MACD Trend Following Strategy.
    Uses MACD line, signal line, and histogram for trend detection.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        use_histogram: bool = True,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="MACD_Trend"
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.use_histogram = use_histogram
        
        self.logger.info(
            f"MACD Strategy: fast={fast_period}, slow={slow_period}, "
            f"signal={signal_period}"
        )
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD indicator"""
        df = data.copy()
        
        # Calculate EMAs
        ema_fast = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # MACD line
        df['macd_line'] = ema_fast - ema_slow
        
        # Signal line
        df['signal_line'] = df['macd_line'].ewm(span=self.signal_period, adjust=False).mean()
        
        # Histogram
        df['histogram'] = df['macd_line'] - df['signal_line']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate MACD signals"""
        signals = []
        
        min_periods = self.slow_period + self.signal_period + 5
        if len(data) < min_periods:
            return signals
        
        df = self.calculate_macd(data)
        
        # Calculate previous values for crossover detection
        df['prev_histogram'] = df['histogram'].shift(1)
        df['prev_macd'] = df['macd_line'].shift(1)
        df['prev_signal'] = df['signal_line'].shift(1)
        
        # Detect crossovers
        df['bull_cross'] = (df['prev_macd'] < df['prev_signal']) & (df['macd_line'] > df['signal_line'])
        df['bear_cross'] = (df['prev_macd'] > df['prev_signal']) & (df['macd_line'] < df['signal_line'])
        
        # Histogram momentum
        df['hist_rising'] = df['histogram'] > df['prev_histogram']
        df['hist_falling'] = df['histogram'] < df['prev_histogram']
        
        # Get current bar
        current = df.iloc[-1]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Bullish signal: MACD crosses above signal line
        if current['bull_cross']:
            stop_loss = self.calculate_stop_loss(current_price)
            take_profit = self.calculate_take_profit(current_price)
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'macd_line': current['macd_line'],
                    'signal_line': current['signal_line'],
                    'histogram': current['histogram'],
                    'signal_type': 'macd_crossover'
                }
            )
            signals.append(signal)
            self.logger.info(f"MACD BUY signal for {symbol} at ${current_price:.2f}")
        
        # Bearish signal: MACD crosses below signal line
        elif current['bear_cross']:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'macd_line': current['macd_line'],
                    'signal_line': current['signal_line'],
                    'histogram': current['histogram'],
                    'signal_type': 'macd_crossover'
                }
            )
            signals.append(signal)
            self.logger.info(f"MACD SELL signal for {symbol} at ${current_price:.2f}")
        
        # Additional histogram-based signals
        if self.use_histogram and len(df) >= 3:
            prev2 = df.iloc[-2]
            
            # Bullish histogram divergence (histogram turns positive after being negative)
            if current['histogram'] > 0 and prev2['histogram'] < 0 and not current['bull_cross']:
                if not any(s.signal_type == SignalType.BUY for s in signals):
                    stop_loss = self.calculate_stop_loss(current_price)
                    take_profit = self.calculate_take_profit(current_price)
                    
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        timestamp=timestamp,
                        price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        metadata={
                            'histogram': current['histogram'],
                            'signal_type': 'histogram_positive'
                        }
                    )
                    signals.append(signal)
                    self.logger.info(f"MACD Histogram BUY for {symbol} at ${current_price:.2f}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting MACD Trend live trading")
        self.is_running = True
        
        from alpaca.trading.enums import OrderSide
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    data = self.get_historical_data(symbol, limit=100)
                    
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
    strategy = MACDTrendStrategy(
        symbols=['AAPL', 'MSFT', 'AMZN'],
        fast_period=12,
        slow_period=26,
        signal_period=9
    )
    
    results = strategy.backtest()
    print(f"MACD Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
    print(f"  Win Rate: {results.get('win_rate', 0)*100:.1f}%")
