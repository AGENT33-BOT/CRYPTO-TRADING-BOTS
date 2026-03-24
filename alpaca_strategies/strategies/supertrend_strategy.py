"""
Supertrend Strategy
ATR-based trend following indicator
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


class SupertrendStrategy(BaseStrategy):
    """
    Supertrend Strategy - ATR based trend indicator.
    Uses Average True Range to determine trend direction and strength.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        atr_period: int = 10,
        multiplier: float = 3.0,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Supertrend"
        )
        self.atr_period = atr_period
        self.multiplier = multiplier
        
        self.logger.info(
            f"Supertrend initialized: ATR period={atr_period}, "
            f"multiplier={multiplier}"
        )
    
    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(window=period).mean()
    
    def calculate_supertrend(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Supertrend indicator"""
        df = data.copy()
        
        # Calculate ATR
        df['atr'] = self.calculate_atr(df, self.atr_period)
        
        # Calculate basic upper and lower bands
        hl2 = (df['high'] + df['low']) / 2
        df['upper_band'] = hl2 + (self.multiplier * df['atr'])
        df['lower_band'] = hl2 - (self.multiplier * df['atr'])
        
        # Initialize Supertrend columns
        df['supertrend'] = 0.0
        df['in_uptrend'] = True
        
        for i in range(1, len(df)):
            curr_upper = df['upper_band'].iloc[i]
            curr_lower = df['lower_band'].iloc[i]
            prev_close = df['close'].iloc[i - 1]
            prev_upper = df['upper_band'].iloc[i - 1]
            prev_lower = df['lower_band'].iloc[i - 1]
            prev_supertrend = df['supertrend'].iloc[i - 1]
            prev_uptrend = df['in_uptrend'].iloc[i - 1]
            
            # Adjust bands
            if prev_close > prev_upper:
                curr_upper = max(curr_upper, prev_upper)
            if prev_close < prev_lower:
                curr_lower = min(curr_lower, prev_lower)
            
            # Determine trend
            if prev_uptrend:
                if df['close'].iloc[i] <= curr_lower:
                    df.loc[df.index[i], 'in_uptrend'] = False
                    df.loc[df.index[i], 'supertrend'] = curr_upper
                else:
                    df.loc[df.index[i], 'in_uptrend'] = True
                    df.loc[df.index[i], 'supertrend'] = curr_lower
            else:
                if df['close'].iloc[i] >= curr_upper:
                    df.loc[df.index[i], 'in_uptrend'] = True
                    df.loc[df.index[i], 'supertrend'] = curr_lower
                else:
                    df.loc[df.index[i], 'in_uptrend'] = False
                    df.loc[df.index[i], 'supertrend'] = curr_upper
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate Supertrend signals"""
        signals = []
        
        if len(data) < self.atr_period + 5:
            return signals
        
        df = self.calculate_supertrend(data)
        
        # Detect trend changes
        df['prev_uptrend'] = df['in_uptrend'].shift(1)
        
        # Buy signal: trend changes from down to up
        df['buy_signal'] = (~df['prev_uptrend'].fillna(True)) & df['in_uptrend']
        
        # Sell signal: trend changes from up to down
        df['sell_signal'] = df['prev_uptrend'].fillna(False) & (~df['in_uptrend'])
        
        # Get current bar
        current = df.iloc[-1]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Generate buy signal
        if current['buy_signal']:
            stop_loss = current['supertrend']
            take_profit = current_price * (1 + self.config.default_take_profit_pct)
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'supertrend_value': current['supertrend'],
                    'atr': current['atr'],
                    'trend': 'uptrend'
                }
            )
            signals.append(signal)
            self.logger.info(f"Supertrend BUY signal for {symbol} at ${current_price:.2f}")
        
        # Generate sell signal
        elif current['sell_signal']:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'supertrend_value': current['supertrend'],
                    'atr': current['atr'],
                    'trend': 'downtrend'
                }
            )
            signals.append(signal)
            self.logger.info(f"Supertrend SELL signal for {symbol} at ${current_price:.2f}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Supertrend live trading")
        self.is_running = True
        
        from alpaca.trading.enums import OrderSide
        
        while self.is_running:
            try:
                for symbol in self.symbols:
                    data = self.get_historical_data(symbol, limit=50)
                    
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
    strategy = SupertrendStrategy(
        symbols=['AAPL', 'TSLA'],
        atr_period=10,
        multiplier=3.0
    )
    
    results = strategy.backtest()
    print(f"Supertrend Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
