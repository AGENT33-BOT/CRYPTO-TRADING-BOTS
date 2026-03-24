"""
Range Breakout with Volume Strategy
Breakout from trading range with volume confirmation
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


class RangeBreakoutVolumeStrategy(BaseStrategy):
    """
    Range Breakout with Volume Confirmation Strategy.
    Identifies consolidation/range periods and enters on breakouts
    confirmed by above-average volume.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        range_period: int = 10,
        breakout_threshold: float = 0.015,  # 1.5% breakout
        volume_multiplier: float = 1.5,      # 50% above average volume
        min_range_width: float = 0.03,       # Minimum 3% range width
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Range_Breakout_Volume"
        )
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Range_Breakout_Volume"
        )
        self.range_period = range_period
        self.breakout_threshold = breakout_threshold
        self.volume_multiplier = volume_multiplier
        self.min_range_width = min_range_width
        
        self.logger.info(
            f"Range Breakout: period={range_period}, "
            f"volume_mult={volume_multiplier}"
        )
    
    def calculate_range(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate trading range metrics"""
        df = data.copy()
        
        # Rolling highs and lows (range boundaries)
        df['range_high'] = df['high'].rolling(window=self.range_period).max()
        df['range_low'] = df['low'].rolling(window=self.range_period).min()
        
        # Range width as percentage
        df['range_width'] = (df['range_high'] - df['range_low']) / df['range_low']
        df['range_width_avg'] = df['range_width'].rolling(window=self.range_period).mean()
        
        # Range midpoint
        df['range_mid'] = (df['range_high'] + df['range_low']) / 2
        
        # Consolidation detection (tight range)
        df['is_consolidating'] = df['range_width'] < df['range_width_avg'] * 0.8
        
        # Volume average
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(window=self.range_period).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
        else:
            df['volume_sma'] = 0
            df['volume_ratio'] = 1
        
        # Breakout levels
        df['breakout_level'] = df['range_high'].shift(1)
        df['breakdown_level'] = df['range_low'].shift(1)
        
        # Distance from breakout
        df['dist_above_range'] = (df['close'] - df['breakout_level']) / df['breakout_level']
        df['dist_below_range'] = (df['breakdown_level'] - df['close']) / df['breakdown_level']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate range breakout signals with volume confirmation"""
        signals = []
        
        if len(data) < self.range_period + 5:
            return signals
        
        df = self.calculate_range(data)
        
        # Previous values
        df['was_consolidating'] = df['is_consolidating'].shift(1)
        
        # Get current and recent bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Volume confirmation
        volume_confirmed = current['volume_ratio'] > self.volume_multiplier
        
        # Breakout conditions
        breakout_up = current['dist_above_range'] > self.breakout_threshold
        breakout_down = current['dist_below_range'] > self.breakout_threshold
        
        # Breakout from consolidation preferred but not required
        from_consolidation = prev['was_consolidating']
        
        # Buy signal: Upside breakout with volume
        if breakout_up and volume_confirmed:
            # Check if range was meaningful (not too tight)
            sufficient_range = current['range_width'] > self.min_range_width
            
            if sufficient_range or from_consolidation:
                stop_loss = current['breakout_level']
                # Target based on range width (measured move)
                target_range = current['range_high'] - current['range_low']
                take_profit = current_price + target_range
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'range_high': current['range_high'],
                        'range_low': current['range_low'],
                        'breakout_level': current['breakout_level'],
                        'volume_ratio': current['volume_ratio'],
                        'range_width': current['range_width'],
                        'from_consolidation': from_consolidation,
                        'signal_type': 'range_breakout_up'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"Range Breakout BUY for {symbol} at ${current_price:.2f} "
                    f"(vol ratio: {current['volume_ratio']:.1f}x)"
                )
        
        # Sell signal: Downside breakdown with volume
        elif breakout_down and volume_confirmed:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'breakdown_level': current['breakdown_level'],
                    'volume_ratio': current['volume_ratio'],
                    'signal_type': 'range_breakdown'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"Range Breakdown SELL for {symbol} at ${current_price:.2f}"
            )
        
        # False breakout detection (breakout then immediate reversal)
        if len(df) >= 3:
            prev2 = df.iloc[-3]
            
            # Check if previous bar was a breakout that failed
            false_breakout = (
                (prev['close'] > prev['breakout_level']) and
                (current['close'] < prev['breakout_level']) and
                (current['volume_ratio'] > 1.2)  # Volume on reversal
            )
            
            if false_breakout and not any(s.signal_type == SignalType.SELL for s in signals):
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    metadata={
                        'signal_type': 'false_breakout_reversal'
                    }
                )
                signals.append(signal)
                self.logger.info(f"False Breakout SELL for {symbol}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Range Breakout Volume live trading")
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
    strategy = RangeBreakoutVolumeStrategy(
        symbols=['SPY', 'QQQ', 'IWM'],
        range_period=10,
        volume_multiplier=1.5
    )
    
    results = strategy.backtest()
    print(f"Range Breakout Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
