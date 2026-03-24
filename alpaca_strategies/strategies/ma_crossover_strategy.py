"""
MA Crossover Strategy
Simple and Exponential Moving Average crossover strategy
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


class MACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy.
    Generates buy signals when fast MA crosses above slow MA.
    Generates sell signals when fast MA crosses below slow MA.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        fast_period: int = 20,
        slow_period: int = 50,
        ma_type: str = "sma",  # 'sma' or 'ema'
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="MA_Crossover"
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type
        
        self.logger.info(
            f"MA Crossover initialized: {ma_type.upper()}, "
            f"fast={fast_period}, slow={slow_period}"
        )
    
    def calculate_ma(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate moving average"""
        if self.ma_type == "ema":
            return series.ewm(span=period, adjust=False).mean()
        return series.rolling(window=period).mean()
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate MA crossover signals"""
        signals = []
        
        if len(data) < self.slow_period + 5:
            return signals
        
        df = data.copy()
        
        # Calculate moving averages
        df['fast_ma'] = self.calculate_ma(df['close'], self.fast_period)
        df['slow_ma'] = self.calculate_ma(df['close'], self.slow_period)
        
        # Calculate crossover
        df['ma_diff'] = df['fast_ma'] - df['slow_ma']
        df['crossover'] = np.where(
            (df['ma_diff'].shift(1) < 0) & (df['ma_diff'] > 0), 1,
            np.where((df['ma_diff'].shift(1) > 0) & (df['ma_diff'] < 0), -1, 0)
        )
        
        # Get current and previous bars
        if len(df) >= 2:
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            current_price = current['close']
            timestamp = df.index[-1]
            
            # Bullish crossover
            if current['crossover'] == 1:
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
                        'fast_ma': current['fast_ma'],
                        'slow_ma': current['slow_ma'],
                        'crossover_type': 'bullish'
                    }
                )
                signals.append(signal)
                self.logger.info(f"BUY signal for {symbol} at ${current_price:.2f}")
            
            # Bearish crossover
            elif current['crossover'] == -1:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    metadata={
                        'fast_ma': current['fast_ma'],
                        'slow_ma': current['slow_ma'],
                        'crossover_type': 'bearish'
                    }
                )
                signals.append(signal)
                self.logger.info(f"SELL signal for {symbol} at ${current_price:.2f}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting MA Crossover live trading")
        self.is_running = True
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    # Get latest data
                    data = self.get_historical_data(symbol, limit=self.slow_period + 10)
                    
                    if data.empty:
                        continue
                    
                    # Generate signals
                    signals = self.generate_signals(data, symbol)
                    
                    for signal in signals:
                        if signal.signal_type == SignalType.BUY:
                            # Calculate position size
                            quantity = self.get_position_size(symbol, signal.price)
                            if quantity > 0:
                                from alpaca.trading.enums import OrderSide
                                self.submit_order(
                                    symbol=symbol,
                                    side=OrderSide.BUY,
                                    quantity=quantity,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit
                                )
                        
                        elif signal.signal_type == SignalType.SELL:
                            # Close position if exists
                            from alpaca.trading.enums import OrderSide
                            positions = self.get_open_positions()
                            if symbol in positions:
                                qty = abs(int(float(positions[symbol].qty)))
                                if qty > 0:
                                    self.submit_order(
                                        symbol=symbol,
                                        side=OrderSide.SELL,
                                        quantity=qty
                                    )
                
                # Sleep before next iteration
                import time
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in run loop: {e}")
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
    # Example usage
    strategy = MACrossoverStrategy(
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        fast_period=20,
        slow_period=50,
        ma_type='sma'
    )
    
    # Run backtest
    results = strategy.backtest()
    print(f"Backtest Results:")
    print(f"Total Return: {results['total_return']*100:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown_pct']*100:.2f}%")
