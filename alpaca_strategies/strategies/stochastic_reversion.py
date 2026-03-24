"""
Stochastic Oscillator Mean Reversion Strategy
Overbought/Oversold signals using Stochastic
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


class StochasticReversionStrategy(BaseStrategy):
    """
    Stochastic Oscillator Mean Reversion Strategy.
    Uses %K and %D crossovers in overbought/oversold regions.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        k_period: int = 14,
        d_period: int = 3,
        slowing: int = 3,
        oversold: float = 20.0,
        overbought: float = 80.0,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Stochastic_Reversion"
        )
        self.k_period = k_period
        self.d_period = d_period
        self.slowing = slowing
        self.oversold = oversold
        self.overbought = overbought
        
        self.logger.info(
            f"Stochastic Strategy: k={k_period}, d={d_period}, "
            f"oversold={oversold}, overbought={overbought}"
        )
    
    def calculate_stochastic(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic Oscillator"""
        df = data.copy()
        
        # Calculate %K
        low_min = df['low'].rolling(window=self.k_period).min()
        high_max = df['high'].rolling(window=self.k_period).max()
        
        df['k_fast'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        
        # Slow %K (with slowing period)
        df['k'] = df['k_fast'].rolling(window=self.slowing).mean()
        
        # %D (signal line)
        df['d'] = df['k'].rolling(window=self.d_period).mean()
        
        # Stochastic RSI (alternative calculation using RSI of %K)
        # Not used by default but available
        delta = df['k'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.k_period).mean()
        avg_loss = loss.rolling(window=self.k_period).mean()
        
        rs = avg_gain / avg_loss
        df['stoch_rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate Stochastic mean reversion signals"""
        signals = []
        
        min_periods = self.k_period + self.d_period + self.slowing + 5
        if len(data) < min_periods:
            return signals
        
        df = self.calculate_stochastic(data)
        
        # Previous values
        df['k_prev'] = df['k'].shift(1)
        df['d_prev'] = df['d'].shift(1)
        
        # Zone detection
        df['oversold_zone'] = df['k'] < self.oversold
        df['overbought_zone'] = df['k'] > self.overbought
        
        # Crossovers
        df['k_cross_above_d'] = (df['k_prev'] <= df['d_prev']) & (df['k'] > df['d'])
        df['k_cross_below_d'] = (df['k_prev'] >= df['d_prev']) & (df['k'] < df['d'])
        
        # Get current and previous bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Buy signal: %K crosses above %D in oversold zone
        if current['k_cross_above_d'] and current['oversold_zone']:
            stop_loss = current_price * 0.98
            take_profit = current_price * 1.04
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'k': current['k'],
                    'd': current['d'],
                    'zone': 'oversold',
                    'signal_type': 'stoch_cross_oversold'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"Stochastic BUY signal for {symbol} at ${current_price:.2f} "
                f"(K: {current['k']:.1f}, D: {current['d']:.1f})"
            )
        
        # Sell signal: %K crosses below %D in overbought zone
        elif current['k_cross_below_d'] and current['overbought_zone']:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'k': current['k'],
                    'd': current['d'],
                    'zone': 'overbought',
                    'signal_type': 'stoch_cross_overbought'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"Stochastic SELL signal for {symbol} at ${current_price:.2f} "
                f"(K: {current['k']:.1f}, D: {current['d']:.1f})"
            )
        
        # Exit oversold zone (mean reversion complete)
        exit_oversold = (prev['k'] < self.oversold) and (current['k'] >= self.oversold)
        if exit_oversold and not any(s.signal_type == SignalType.SELL for s in signals):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'k': current['k'],
                    'signal_type': 'exit_oversold'
                }
            )
            signals.append(signal)
            self.logger.info(f"Stochastic Exit Oversold for {symbol}")
        
        # Fast stochastic reversal detection
        extreme_oversold = current['k'] < 10
        extreme_overbought = current['k'] > 90
        
        # Extreme reversal signals
        if extreme_oversold and current['k'] > prev['k']:
            if not any(s.signal_type == SignalType.BUY for s in signals):
                stop_loss = current_price * 0.97
                take_profit = current_price * 1.05
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'k': current['k'],
                        'signal_type': 'extreme_reversal'
                    }
                )
                signals.append(signal)
                self.logger.info(f"Stochastic EXTREME BUY for {symbol} (K: {current['k']:.1f})")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Stochastic Reversion live trading")
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
    strategy = StochasticReversionStrategy(
        symbols=['AAPL', 'MSFT'],
        k_period=14,
        d_period=3,
        oversold=20,
        overbought=80
    )
    
    results = strategy.backtest()
    print(f"Stochastic Reversion Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
