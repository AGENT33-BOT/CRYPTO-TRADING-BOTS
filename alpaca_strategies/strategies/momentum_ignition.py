"""
Momentum Ignition Strategy
Detects momentum bursts and acceleration
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


class MomentumIgnitionStrategy(BaseStrategy):
    """
    Momentum Ignition Strategy.
    Detects sudden momentum acceleration and volume spikes
    that often precede strong directional moves.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "5Min",
        momentum_period: int = 10,
        acceleration_threshold: float = 2.0,
        volume_surge: float = 2.0,
        min_momentum: float = 0.01,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Momentum_Ignition"
        )
        self.momentum_period = momentum_period
        self.acceleration_threshold = acceleration_threshold
        self.volume_surge = volume_surge
        self.min_momentum = min_momentum
        
        self.logger.info(
            f"Momentum Ignition: period={momentum_period}, "
            f"accel_threshold={acceleration_threshold}"
        )
    
    def calculate_momentum(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum and acceleration metrics"""
        df = data.copy()
        
        # Price momentum (rate of change)
        df['momentum'] = df['close'].pct_change(self.momentum_period)
        df['momentum_prev'] = df['momentum'].shift(1)
        
        # Momentum acceleration (change in momentum)
        df['acceleration'] = df['momentum'] - df['momentum_prev']
        
        # Short-term momentum (1-period)
        df['st_momentum'] = df['close'].pct_change()
        df['st_momentum_prev'] = df['st_momentum'].shift(1)
        df['st_momentum_prev2'] = df['st_momentum'].shift(2)
        
        # Acceleration of short-term momentum
        df['st_accel'] = df['st_momentum'] - df['st_momentum_prev']
        df['st_accel_prev'] = df['st_momentum_prev'] - df['st_momentum_prev2']
        
        # Volume momentum
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(window=self.momentum_period).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_momentum'] = df['volume'].pct_change(3)
        else:
            df['volume_ratio'] = 1
            df['volume_momentum'] = 0
        
        # Price velocity (average of recent changes)
        df['velocity'] = df['st_momentum'].rolling(window=3).mean()
        df['velocity_change'] = df['velocity'].diff()
        
        # Consecutive up/down bars
        df['is_up'] = df['close'] > df['open']
        df['consecutive_up'] = df['is_up'].astype(int).groupby(
            (df['is_up'] != df['is_up'].shift()).cumsum()
        ).cumsum()
        df['consecutive_down'] = (~df['is_up']).astype(int).groupby(
            ((~df['is_up']) != (~df['is_up']).shift()).cumsum()
        ).cumsum()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate momentum ignition signals"""
        signals = []
        
        if len(data) < self.momentum_period + 5:
            return signals
        
        df = self.calculate_momentum(data)
        
        # Get current and recent bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Volume surge check
        volume_surge = current['volume_ratio'] > self.volume_surge
        
        # Momentum ignition conditions
        # 1. Acceleration of momentum
        acceleration_up = current['acceleration'] > self.acceleration_threshold * abs(current['momentum_prev'])
        acceleration_down = current['acceleration'] < -self.acceleration_threshold * abs(current['momentum_prev'])
        
        # 2. Short-term momentum acceleration
        st_ignition = (
            current['st_momentum'] > current['st_momentum_prev'] and
            current['st_momentum_prev'] > 0 and
            current['st_accel'] > current['st_accel_prev']
        )
        
        # 3. Consecutive momentum
        consecutive_momentum = current['consecutive_up'] >= 3
        
        # Buy signal: Momentum ignition detected
        if (acceleration_up or st_ignition) and volume_surge:
            if abs(current['momentum']) > self.min_momentum:
                # Dynamic stop based on recent volatility
                recent_range = df['high'].tail(10).max() - df['low'].tail(10).min()
                stop_loss = current_price - recent_range * 0.5
                take_profit = current_price + recent_range * 1.5
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'momentum': current['momentum'],
                        'acceleration': current['acceleration'],
                        'volume_ratio': current['volume_ratio'],
                        'consecutive_up': current['consecutive_up'],
                        'signal_type': 'momentum_ignition'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"Momentum IGNITION BUY for {symbol} at ${current_price:.2f} "
                    f"(mom: {current['momentum']*100:.1f}%, vol: {current['volume_ratio']:.1f}x)"
                )
        
        # Sell signal: Negative momentum ignition
        elif (acceleration_down or (current['st_momentum'] < current['st_momentum_prev'] and current['st_momentum_prev'] < 0)) and volume_surge:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'momentum': current['momentum'],
                    'acceleration': current['acceleration'],
                    'volume_ratio': current['volume_ratio'],
                    'signal_type': 'momentum_ignition_down'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"Momentum IGNITION SELL for {symbol} at ${current_price:.2f}"
            )
        
        # Exhaustion signal (momentum slowing after strong move)
        if len(df) >= 4:
            prev2 = df.iloc[-3]
            
            momentum_exhaustion = (
                current['st_momentum'] < prev['st_momentum'] and
                prev['st_momentum'] < prev2['st_momentum'] and
                prev2['st_momentum'] > 0.02  # Was a strong move
            )
            
            if momentum_exhaustion and not any(s.signal_type == SignalType.SELL for s in signals):
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    metadata={
                        'signal_type': 'momentum_exhaustion'
                    }
                )
                signals.append(signal)
                self.logger.info(f"Momentum EXHAUSTION SELL for {symbol}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Momentum Ignition live trading")
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
                time.sleep(30)  # More frequent for intraday momentum
                
            except Exception as e:
                self.logger.error(f"Error: {e}")
                import time
                time.sleep(30)
    
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
    strategy = MomentumIgnitionStrategy(
        symbols=['TSLA', 'NVDA', 'AMD'],
        timeframe='5Min',
        acceleration_threshold=2.0,
        volume_surge=2.0
    )
    
    results = strategy.backtest()
    print(f"Momentum Ignition Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
