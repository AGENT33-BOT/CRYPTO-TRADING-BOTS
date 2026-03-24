"""
EMA Crossover Strategy
Fast and Slow Exponential Moving Average crossover
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


class EMACrossoverStrategy(BaseStrategy):
    """
    EMA Crossover Strategy with triple EMA option.
    Generates signals based on fast EMA crossing slow EMA.
    Optional trend filter using a third EMA.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        fast_ema: int = 12,
        slow_ema: int = 26,
        trend_ema: Optional[int] = 200,  # Optional trend filter
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="EMA_Crossover"
        )
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.trend_ema = trend_ema
        
        self.logger.info(
            f"EMA Crossover: fast={fast_ema}, slow={slow_ema}, "
            f"trend_filter={trend_ema if trend_ema else 'None'}"
        )
    
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate exponential moving average"""
        return series.ewm(span=period, adjust=False).mean()
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate EMA crossover signals"""
        signals = []
        
        min_periods = max(self.slow_ema, self.trend_ema or 0) + 5
        if len(data) < min_periods:
            return signals
        
        df = data.copy()
        
        # Calculate EMAs
        df['fast_ema'] = self.calculate_ema(df['close'], self.fast_ema)
        df['slow_ema'] = self.calculate_ema(df['close'], self.slow_ema)
        
        if self.trend_ema:
            df['trend_ema'] = self.calculate_ema(df['close'], self.trend_ema)
        
        # Calculate EMA difference and crossover
        df['ema_diff'] = df['fast_ema'] - df['slow_ema']
        
        # Detect crossovers
        df['bull_cross'] = (df['ema_diff'].shift(1) < 0) & (df['ema_diff'] > 0)
        df['bear_cross'] = (df['ema_diff'].shift(1) > 0) & (df['ema_diff'] < 0)
        
        # Apply trend filter if enabled
        if self.trend_ema:
            df['above_trend'] = df['close'] > df['trend_ema']
            df['bull_cross'] = df['bull_cross'] & df['above_trend']
            df['bear_cross'] = df['bear_cross'] & ~df['above_trend']
        
        # Get current bar
        current = df.iloc[-1]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Bullish crossover
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
                    'fast_ema': current['fast_ema'],
                    'slow_ema': current['slow_ema'],
                    'trend_aligned': self.trend_ema is None or current.get('above_trend', True)
                }
            )
            signals.append(signal)
            self.logger.info(f"EMA BUY signal for {symbol} at ${current_price:.2f}")
        
        # Bearish crossover
        elif current['bear_cross']:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'fast_ema': current['fast_ema'],
                    'slow_ema': current['slow_ema']
                }
            )
            signals.append(signal)
            self.logger.info(f"EMA SELL signal for {symbol} at ${current_price:.2f}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting EMA Crossover live trading")
        self.is_running = True
        
        from alpaca.trading.enums import OrderSide
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    data = self.get_historical_data(symbol, limit=250)
                    
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
    strategy = EMACrossoverStrategy(
        symbols=['SPY', 'QQQ'],
        fast_ema=12,
        slow_ema=26,
        trend_ema=200
    )
    
    results = strategy.backtest()
    print(f"EMA Crossover Results:")
    for key, value in results.items():
        print(f"  {key}: {value}")
