"""
ATR Trend Strategy
ATR-based trend detection and position sizing
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


class ATRTrendStrategy(BaseStrategy):
    """
    ATR Trend Strategy.
    Uses ATR for trend detection, volatility measurement, and dynamic position sizing.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        atr_period: int = 14,
        ma_period: int = 20,
        volatility_threshold: float = 1.5,
        use_atr_stops: bool = True,
        atr_multiplier: float = 2.0,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="ATR_Trend"
        )
        self.atr_period = atr_period
        self.ma_period = ma_period
        self.volatility_threshold = volatility_threshold
        self.use_atr_stops = use_atr_stops
        self.atr_multiplier = atr_multiplier
        
        self.logger.info(
            f"ATR Trend initialized: ATR={atr_period}, MA={ma_period}"
        )
    
    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(window=period).mean()
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend indicators"""
        df = data.copy()
        
        # Calculate ATR
        df['atr'] = self.calculate_atr(df, self.atr_period)
        
        # Calculate moving average
        df['ma'] = df['close'].rolling(window=self.ma_period).mean()
        
        # ATR-based trend strength
        df['atr_percent'] = df['atr'] / df['close'] * 100
        df['high_volatility'] = df['atr_percent'] > df['atr_percent'].rolling(20).mean() * self.volatility_threshold
        
        # Price vs MA
        df['price_above_ma'] = df['close'] > df['ma']
        df['price_below_ma'] = df['close'] < df['ma']
        
        # Trend momentum (rate of change of MA)
        df['ma_slope'] = df['ma'].diff()
        df['trend_strength'] = df['ma_slope'] / df['atr']
        
        # ATR bands for breakout detection
        df['upper_atr_band'] = df['ma'] + (df['atr'] * self.atr_multiplier)
        df['lower_atr_band'] = df['ma'] - (df['atr'] * self.atr_multiplier)
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate ATR-based trend signals"""
        signals = []
        
        min_periods = max(self.atr_period, self.ma_period) + 5
        if len(data) < min_periods:
            return signals
        
        df = self.calculate_indicators(data)
        
        # Get current and previous bars
        if len(df) < 2:
            return signals
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Buy signal: Price crosses above MA with positive trend strength
        price_cross_up = (~prev['price_above_ma']) & current['price_above_ma']
        strong_trend = current['trend_strength'] > 0.5
        
        if price_cross_up and strong_trend and not current['high_volatility']:
            # Dynamic stop loss based on ATR
            if self.use_atr_stops:
                stop_loss = current_price - (current['atr'] * self.atr_multiplier)
            else:
                stop_loss = self.calculate_stop_loss(current_price)
            
            take_profit = current_price + (current['atr'] * self.atr_multiplier * 2)
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'atr': current['atr'],
                    'atr_percent': current['atr_percent'],
                    'trend_strength': current['trend_strength'],
                    'ma': current['ma'],
                    'signal_type': 'atr_trend_breakout'
                }
            )
            signals.append(signal)
            self.logger.info(f"ATR Trend BUY signal for {symbol} at ${current_price:.2f}")
        
        # Sell signal: Price crosses below MA
        price_cross_down = (~prev['price_below_ma']) & current['price_below_ma']
        
        if price_cross_down or (current['trend_strength'] < -0.5):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'atr': current['atr'],
                    'trend_strength': current['trend_strength'],
                    'ma': current['ma'],
                    'signal_type': 'atr_trend_reversal'
                }
            )
            signals.append(signal)
            self.logger.info(f"ATR Trend SELL signal for {symbol} at ${current_price:.2f}")
        
        # ATR Breakout signal (high volatility expansion)
        atr_breakout_up = current['close'] > current['upper_atr_band']
        atr_breakout_down = current['close'] < current['lower_atr_band']
        
        if atr_breakout_up and current['high_volatility']:
            # Volatility expansion breakout - momentum trade
            if not any(s.signal_type == SignalType.BUY for s in signals):
                stop_loss = current_price - current['atr']
                take_profit = current_price + (current['atr'] * 3)
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'atr': current['atr'],
                        'signal_type': 'atr_volatility_breakout'
                    }
                )
                signals.append(signal)
                self.logger.info(f"ATR Volatility BUY for {symbol} at ${current_price:.2f}")
        
        return signals
    
    def get_position_size(self, symbol: str, price: float, atr: Optional[float] = None) -> int:
        """Dynamic position sizing based on ATR volatility"""
        portfolio_value = self.get_portfolio_value()
        
        if atr and price > 0:
            # Risk-based position sizing: risk 1% per trade
            risk_per_trade = portfolio_value * 0.01
            risk_per_share = atr
            
            if risk_per_share > 0:
                shares = int(risk_per_trade / risk_per_share)
                max_shares = int((portfolio_value * self.config.max_position_size) / price)
                return min(shares, max_shares)
        
        return super().get_position_size(symbol, price)
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting ATR Trend live trading")
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
                        atr = signal.metadata.get('atr', None)
                        
                        if signal.signal_type == SignalType.BUY:
                            quantity = self.get_position_size(symbol, signal.price, atr)
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
    strategy = ATRTrendStrategy(
        symbols=['SPY', 'QQQ', 'IWM'],
        atr_period=14,
        atr_multiplier=2.0
    )
    
    results = strategy.backtest()
    print(f"ATR Trend Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
