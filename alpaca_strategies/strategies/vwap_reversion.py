"""
VWAP Mean Reversion Strategy
Price reversion to Volume Weighted Average Price
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


class VWAPReversionStrategy(BaseStrategy):
    """
    VWAP Mean Reversion Strategy.
    Prices tend to revert to VWAP during the trading day.
    Uses distance from VWAP to generate signals.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "5Min",  # VWAP is typically intraday
        vwap_period: int = 20,
        deviation_threshold: float = 0.02,  # 2% deviation
        use_std_band: bool = True,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="VWAP_Reversion"
        )
        self.vwap_period = vwap_period
        self.deviation_threshold = deviation_threshold
        self.use_std_band = use_std_band
        
        self.logger.info(
            f"VWAP Reversion: threshold={deviation_threshold*100}%, "
            f"std_bands={use_std_band}"
        )
    
    def calculate_vwap(self, data: pd.DataFrame, period: Optional[int] = None) -> pd.DataFrame:
        """Calculate VWAP and standard deviation bands"""
        df = data.copy()
        p = period or self.vwap_period
        
        # Typical price
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # Volume-weighted calculations
        df['tp_vol'] = df['typical_price'] * df['volume']
        
        # Rolling VWAP
        df['vwap'] = df['tp_vol'].rolling(window=p).sum() / df['volume'].rolling(window=p).sum()
        
        # Standard deviation of price from VWAP
        df['price_deviation'] = df['typical_price'] - df['vwap']
        df['variance'] = (df['price_deviation'] ** 2 * df['volume']).rolling(window=p).sum() / df['volume'].rolling(window=p).sum()
        df['std'] = np.sqrt(df['variance'])
        
        # VWAP bands
        df['upper_band'] = df['vwap'] + 2 * df['std']
        df['lower_band'] = df['vwap'] - 2 * df['std']
        
        # Deviation from VWAP
        df['vwap_deviation'] = (df['close'] - df['vwap']) / df['vwap']
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate VWAP reversion signals"""
        signals = []
        
        if len(data) < self.vwap_period + 5:
            return signals
        
        df = self.calculate_vwap(data)
        
        # Previous values
        df['prev_close'] = df['close'].shift(1)
        df['prev_deviation'] = df['vwap_deviation'].shift(1)
        
        # Get current and previous bars
        current = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Deviation signals
        below_threshold = current['vwap_deviation'] < -self.deviation_threshold
        above_threshold = current['vwap_deviation'] > self.deviation_threshold
        
        # Buy signal: Price significantly below VWAP (reversion expected)
        if below_threshold:
            # Check if starting to revert
            reverting = current['close'] > prev['close'] or current['vwap_deviation'] > prev['vwap_deviation']
            
            if reverting or current['vwap_deviation'] < -self.deviation_threshold * 1.5:
                stop_loss = current_price * 0.99
                take_profit = current['vwap']
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    metadata={
                        'vwap': current['vwap'],
                        'deviation': current['vwap_deviation'],
                        'upper_band': current['upper_band'],
                        'lower_band': current['lower_band'],
                        'signal_type': 'below_vwap'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"VWAP BUY signal for {symbol} at ${current_price:.2f} "
                    f"(deviation: {current['vwap_deviation']*100:.1f}%)"
                )
        
        # Sell signal: Price significantly above VWAP
        elif above_threshold:
            reverting = current['close'] < prev['close'] or current['vwap_deviation'] < prev['vwap_deviation']
            
            if reverting:
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    metadata={
                        'vwap': current['vwap'],
                        'deviation': current['vwap_deviation'],
                        'signal_type': 'above_vwap'
                    }
                )
                signals.append(signal)
                self.logger.info(
                    f"VWAP SELL signal for {symbol} at ${current_price:.2f} "
                    f"(deviation: {current['vwap_deviation']*100:.1f}%)"
                )
        
        # VWAP cross exit
        cross_up = (prev['close'] < prev['vwap']) and (current['close'] > current['vwap'])
        if cross_up and not any(s.signal_type == SignalType.SELL for s in signals):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'vwap': current['vwap'],
                    'signal_type': 'vwap_cross_exit'
                }
            )
            signals.append(signal)
            self.logger.info(f"VWAP Cross Exit for {symbol}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting VWAP Reversion live trading")
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
                time.sleep(30)  # More frequent for intraday
                
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
    strategy = VWAPReversionStrategy(
        symbols=['SPY'],
        timeframe='5Min',
        deviation_threshold=0.02
    )
    
    results = strategy.backtest()
    print(f"VWAP Reversion Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
