"""
Breakout and Retest Strategy
Breakout with retest confirmation
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


class BreakoutRetestStrategy(BaseStrategy):
    """
    Breakout and Retest Strategy.
    Waits for price to break above resistance, then retests the breakout level
    as support before entering long. Reduces false breakout risk.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        lookback_period: int = 20,
        breakout_threshold: float = 0.02,  # 2% above resistance
        retest_tolerance: float = 0.01,     # 1% tolerance for retest
        confirmation_bars: int = 2,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Breakout_Retest"
        )
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.retest_tolerance = retest_tolerance
        self.confirmation_bars = confirmation_bars
        
        # Track breakout states
        self.breakout_levels: Dict[str, Dict] = {}
        
        self.logger.info(
            f"Breakout Retest: lookback={lookback_period}, "
            f"threshold={breakout_threshold*100}%"
        )
    
    def calculate_levels(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate support and resistance levels"""
        df = data.copy()
        
        # Resistance and support over lookback period
        df['resistance'] = df['high'].rolling(window=self.lookback_period).max()
        df['support'] = df['low'].rolling(window=self.lookback_period).min()
        
        # Breakout levels
        df['breakout_level'] = df['resistance'].shift(1)
        df['breakdown_level'] = df['support'].shift(1)
        
        # Price distance from levels
        df['dist_from_resistance'] = (df['close'] - df['resistance'].shift(1)) / df['resistance'].shift(1)
        df['dist_from_support'] = (df['support'].shift(1) - df['close']) / df['support'].shift(1)
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate breakout and retest signals"""
        signals = []
        
        if len(data) < self.lookback_period + 10:
            return signals
        
        df = self.calculate_levels(data)
        
        # Get last few bars for pattern detection
        recent = df.tail(self.confirmation_bars + 3)
        current = df.iloc[-1]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Initialize symbol state
        if symbol not in self.breakout_levels:
            self.breakout_levels[symbol] = {
                'resistance_broken': False,
                'breakout_price': 0,
                'waiting_retest': False,
                'retest_count': 0
            }
        
        state = self.breakout_levels[symbol]
        
        # Check for breakout
        breakout_occurred = current['dist_from_resistance'] > self.breakout_threshold
        
        if breakout_occurred and not state['resistance_broken']:
            state['resistance_broken'] = True
            state['breakout_price'] = current_price
            state['waiting_retest'] = True
            state['breakout_bar'] = len(df)
            self.logger.info(f"{symbol}: Breakout detected at ${current_price:.2f}")
        
        # Check for retest of breakout level
        if state['waiting_retest']:
            bars_since_breakout = len(df) - state['breakout_bar']
            
            # Only wait for retest within reasonable timeframe
            if bars_since_breakout <= 10:
                breakout_level = state['breakout_price'] * (1 - self.breakout_threshold)
                retest_zone_low = breakout_level * (1 - self.retest_tolerance)
                retest_zone_high = breakout_level * (1 + self.retest_tolerance)
                
                # Price in retest zone
                in_retest_zone = retest_zone_low <= current_price <= retest_zone_high
                
                # Price bounced from retest zone (bullish candle)
                bullish_bounce = in_retest_zone and (current['close'] > current['open'])
                
                if bullish_bounce:
                    stop_loss = breakout_level * 0.98
                    take_profit = current_price + (current_price - breakout_level) * 2
                    
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        timestamp=timestamp,
                        price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        metadata={
                            'breakout_level': breakout_level,
                            'retest_zone_low': retest_zone_low,
                            'retest_zone_high': retest_zone_high,
                            'signal_type': 'breakout_retest'
                        }
                    )
                    signals.append(signal)
                    self.logger.info(
                        f"Breakout Retest BUY for {symbol} at ${current_price:.2f}"
                    )
                    
                    # Reset state after entry
                    state['waiting_retest'] = False
                    state['resistance_broken'] = False
            else:
                # Reset if no retest within timeframe
                state['waiting_retest'] = False
                state['resistance_broken'] = False
        
        # Alternative: Simple breakout entry (without waiting for retest)
        # This is for momentum trades
        if breakout_occurred and not state['waiting_retest']:
            # Check momentum
            volume_confirmed = current['volume'] > df['volume'].rolling(20).mean().iloc[-1] * 1.5 if 'volume' in df.columns else True
            
            if volume_confirmed:
                stop_loss = current['breakout_level'] * 0.98
                take_profit = current_price * 1.06
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'breakout_level': current['breakout_level'],
                        'signal_type': 'direct_breakout'
                    }
                )
                signals.append(signal)
                self.logger.info(f"Direct Breakout BUY for {symbol} at ${current_price:.2f}")
        
        # Breakdown (short) signals - mirror of breakout
        breakdown_occurred = current['dist_from_support'] > self.breakout_threshold
        if breakdown_occurred:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'breakdown_level': current['breakdown_level'],
                    'signal_type': 'breakdown'
                }
            )
            signals.append(signal)
            self.logger.info(f"Breakdown SELL for {symbol} at ${current_price:.2f}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Breakout Retest live trading")
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
    strategy = BreakoutRetestStrategy(
        symbols=['AAPL', 'TSLA'],
        lookback_period=20,
        breakout_threshold=0.02
    )
    
    results = strategy.backtest()
    print(f"Breakout Retest Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
