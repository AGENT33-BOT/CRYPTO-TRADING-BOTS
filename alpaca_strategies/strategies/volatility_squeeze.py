"""
Volatility Squeeze Strategy
Bollinger Bands + Keltner Channel squeeze for breakout prediction
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


class VolatilitySqueezeStrategy(BaseStrategy):
    """
    Volatility Squeeze Strategy.
    Identifies periods of low volatility (squeeze) using Bollinger Bands
    and Keltner Channels. Breakouts after squeezes tend to be powerful.
    Based on John Carter's TTM Squeeze indicator concept.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        bb_period: int = 20,
        bb_std: float = 2.0,
        kc_period: int = 20,
        kc_atr_mult: float = 1.5,
        momentum_period: int = 12,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Volatility_Squeeze"
        )
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.kc_period = kc_period
        self.kc_atr_mult = kc_atr_mult
        self.momentum_period = momentum_period
        
        self.logger.info(
            f"Volatility Squeeze: BB({bb_period},{bb_std}), KC({kc_period},{kc_atr_mult})"
        )
    
    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def calculate_squeeze(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility squeeze indicator"""
        df = data.copy()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * self.bb_std)
        
        # Keltner Channel
        df['kc_middle'] = df['close'].ewm(span=self.kc_period, adjust=False).mean()
        df['atr'] = self.calculate_atr(df, self.kc_period)
        df['kc_upper'] = df['kc_middle'] + (df['atr'] * self.kc_atr_mult)
        df['kc_lower'] = df['kc_middle'] - (df['atr'] * self.kc_atr_mult)
        
        # Squeeze detection: BB inside KC = low volatility
        df['squeeze_on'] = (
            (df['bb_upper'] <= df['kc_upper']) & 
            (df['bb_lower'] >= df['kc_lower'])
        )
        
        # Squeeze release
        df['squeeze_off'] = (
            (df['bb_upper'] > df['kc_upper']) | 
            (df['bb_lower'] < df['kc_lower'])
        )
        
        # Squeeze momentum (rate of change)
        df['momentum'] = df['close'].diff(self.momentum_period)
        df['momentum_norm'] = df['momentum'] / df['close'] * 100
        
        # Squeeze count (consecutive squeeze periods)
        df['squeeze_count'] = 0
        squeeze_count = 0
        for i in range(len(df)):
            if df['squeeze_on'].iloc[i]:
                squeeze_count += 1
            else:
                squeeze_count = 0
            df.iloc[i, df.columns.get_loc('squeeze_count')] = squeeze_count
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate volatility squeeze signals"""
        signals = []
        
        min_periods = max(self.bb_period, self.kc_period) + 10
        if len(data) < min_periods:
            return signals
        
        df = self.calculate_squeeze(data)
        
        # Previous values
        df['squeeze_on_prev'] = df['squeeze_on'].shift(1)
        
        # Get current and previous bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Squeeze release detection
        squeeze_released = prev['squeeze_on'] and not current['squeeze_on']
        
        if squeeze_released:
            # Determine direction based on momentum
            bullish_breakout = current['momentum_norm'] > 0
            bearish_breakout = current['momentum_norm'] < 0
            
            # Require minimum squeeze duration for better signals
            min_squeeze_bars = 3
            sufficient_squeeze = prev['squeeze_count'] >= min_squeeze_bars
            
            if bullish_breakout and sufficient_squeeze:
                # Volatility expansion to upside
                stop_loss = current['bb_lower']
                take_profit = current_price + (current_price - current['bb_lower']) * 2
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'squeeze_count': current['squeeze_count'],
                        'momentum': current['momentum_norm'],
                        'bb_width': current['bb_upper'] - current['bb_lower'],
                        'signal_type': 'squeeze_release_bullish'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"Squeeze BREAKOUT BUY for {symbol} at ${current_price:.2f} "
                    f"(squeeze bars: {prev['squeeze_count']})"
                )
            
            elif bearish_breakout and sufficient_squeeze:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    metadata={
                        'squeeze_count': current['squeeze_count'],
                        'momentum': current['momentum_norm'],
                        'signal_type': 'squeeze_release_bearish'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"Squeeze BREAKOUT SELL for {symbol} at ${current_price:.2f}"
                )
        
        # Squeeze forming (anticipation setup)
        squeeze_forming = current['squeeze_on'] and not prev['squeeze_on']
        if squeeze_forming:
            self.logger.info(f"{symbol}: Squeeze forming - watching for breakout")
        
        # Alternative signal: Price above upper BB after squeeze
        if not current['squeeze_on'] and current['close'] > current['bb_upper']:
            if current['momentum_norm'] > 2 and not any(s.signal_type == SignalType.BUY for s in signals):
                stop_loss = current['bb_middle']
                take_profit = current_price * 1.05
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'momentum': current['momentum_norm'],
                        'signal_type': 'bb_momentum'
                    }
                )
                signals.append(signal)
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Volatility Squeeze live trading")
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
    strategy = VolatilitySqueezeStrategy(
        symbols=['TSLA', 'NVDA'],
        bb_period=20,
        kc_atr_mult=1.5
    )
    
    results = strategy.backtest()
    print(f"Volatility Squeeze Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
