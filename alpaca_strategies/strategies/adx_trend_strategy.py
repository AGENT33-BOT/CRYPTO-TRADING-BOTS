"""
ADX Trend Strategy
Average Directional Index trend strength strategy
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


class ADXTrendStrategy(BaseStrategy):
    """
    ADX Trend Strategy.
    Uses ADX (Average Directional Index) to measure trend strength
    and +DI/-DI crossovers for trend direction.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        adx_period: int = 14,
        di_period: int = 14,
        adx_threshold: float = 25.0,  # Minimum ADX for trend
        use_adx_filter: bool = True,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="ADX_Trend"
        )
        self.adx_period = adx_period
        self.di_period = di_period
        self.adx_threshold = adx_threshold
        self.use_adx_filter = use_adx_filter
        
        self.logger.info(
            f"ADX Strategy: period={adx_period}, threshold={adx_threshold}"
        )
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX, +DI, and -DI"""
        df = data.copy()
        
        # True Range
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # +DM and -DM
        df['plus_dm'] = np.where(
            (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
            np.maximum(df['high'] - df['high'].shift(1), 0),
            0
        )
        df['minus_dm'] = np.where(
            (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
            np.maximum(df['low'].shift(1) - df['low'], 0),
            0
        )
        
        # Smoothed values
        df['atr'] = df['true_range'].ewm(span=self.adx_period, adjust=False).mean()
        df['plus_di'] = 100 * (df['plus_dm'].ewm(span=self.adx_period, adjust=False).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].ewm(span=self.adx_period, adjust=False).mean() / df['atr'])
        
        # DX and ADX
        df['dx'] = 100 * np.abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].ewm(span=self.adx_period, adjust=False).mean()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate ADX-based signals"""
        signals = []
        
        min_periods = self.adx_period * 2 + 5
        if len(data) < min_periods:
            return signals
        
        df = self.calculate_adx(data)
        
        # Detect DI crossovers
        df['plus_di_prev'] = df['plus_di'].shift(1)
        df['minus_di_prev'] = df['minus_di'].shift(1)
        
        # Bullish crossover: +DI crosses above -DI
        df['bull_cross'] = (df['plus_di_prev'] <= df['minus_di_prev']) & (df['plus_di'] > df['minus_di'])
        
        # Bearish crossover: +DI crosses below -DI
        df['bear_cross'] = (df['plus_di_prev'] >= df['minus_di_prev']) & (df['plus_di'] < df['minus_di'])
        
        # Trend strength check
        df['strong_trend'] = df['adx'] > self.adx_threshold
        df['trend_strengthening'] = df['adx'] > df['adx'].shift(1)
        
        # Get current bar
        current = df.iloc[-1]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Buy signal: +DI crosses above -DI with strong trend
        if current['bull_cross']:
            if not self.use_adx_filter or current['strong_trend']:
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
                        'adx': current['adx'],
                        'plus_di': current['plus_di'],
                        'minus_di': current['minus_di'],
                        'strong_trend': current['strong_trend'],
                        'trend_strengthening': current['trend_strengthening']
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"ADX BUY signal for {symbol} at ${current_price:.2f} "
                    f"(ADX: {current['adx']:.1f})"
                )
        
        # Sell signal: +DI crosses below -DI
        elif current['bear_cross']:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'adx': current['adx'],
                    'plus_di': current['plus_di'],
                    'minus_di': current['minus_di'],
                    'signal_type': 'di_crossover'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"ADX SELL signal for {symbol} at ${current_price:.2f}"
            )
        
        # ADX momentum signal: ADX rising from below threshold
        if len(df) >= 3:
            prev_adx = df['adx'].iloc[-2]
            
            adx_momentum = (
                current['adx'] > self.adx_threshold and 
                prev_adx < self.adx_threshold and
                current['plus_di'] > current['minus_di']
            )
            
            if adx_momentum and not any(s.signal_type == SignalType.BUY for s in signals):
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
                        'adx': current['adx'],
                        'signal_type': 'adx_momentum'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"ADX Momentum BUY for {symbol} at ${current_price:.2f}"
                )
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting ADX Trend live trading")
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
    strategy = ADXTrendStrategy(
        symbols=['AAPL', 'MSFT'],
        adx_period=14,
        adx_threshold=25.0
    )
    
    results = strategy.backtest()
    print(f"ADX Trend Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
