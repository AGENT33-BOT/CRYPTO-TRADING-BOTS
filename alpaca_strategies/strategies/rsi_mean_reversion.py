"""
RSI Mean Reversion Strategy
Oversold/Overbought RSI trading
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


class RSIMeanReversionStrategy(BaseStrategy):
    """
    RSI Mean Reversion Strategy.
    Buys when RSI is oversold (below threshold).
    Sells when RSI is overbought (above threshold).
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        exit_middle: bool = True,  # Exit when RSI returns to middle (50)
        use_divergence: bool = True,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="RSI_MeanReversion"
        )
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.exit_middle = exit_middle
        self.use_divergence = use_divergence
        
        self.logger.info(
            f"RSI Mean Reversion: period={rsi_period}, "
            f"oversold={oversold}, overbought={overbought}"
        )
    
    def calculate_rsi(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data['close'].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def detect_divergence(self, df: pd.DataFrame) -> Dict:
        """Detect bullish/bearish divergence"""
        # Look for price making lower lows while RSI makes higher lows (bullish)
        # Or price making higher highs while RSI makes lower highs (bearish)
        
        n = len(df)
        if n < 20:
            return {'bullish': False, 'bearish': False}
        
        # Get last 10 bars
        recent = df.iloc[-10:]
        
        # Find local minima/maxima
        price_lows = recent['close'].nsmallest(2).index
        rsi_lows = recent['rsi'].nsmallest(2).index
        
        price_highs = recent['close'].nlargest(2).index
        rsi_highs = recent['rsi'].nlargest(2).index
        
        # Bullish divergence: price lower low, RSI higher low
        bullish = (
            len(price_lows) >= 2 and len(rsi_lows) >= 2 and
            df.loc[price_lows[0], 'close'] < df.loc[price_lows[1], 'close'] and
            df.loc[rsi_lows[0], 'rsi'] > df.loc[rsi_lows[1], 'rsi']
        )
        
        # Bearish divergence: price higher high, RSI lower high
        bearish = (
            len(price_highs) >= 2 and len(rsi_highs) >= 2 and
            df.loc[price_highs[0], 'close'] > df.loc[price_highs[1], 'close'] and
            df.loc[rsi_highs[0], 'rsi'] < df.loc[rsi_highs[1], 'rsi']
        )
        
        return {'bullish': bullish, 'bearish': bearish}
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate RSI mean reversion signals"""
        signals = []
        
        if len(data) < self.rsi_period + 5:
            return signals
        
        df = data.copy()
        df['rsi'] = self.calculate_rsi(df, self.rsi_period)
        df['rsi_prev'] = df['rsi'].shift(1)
        
        # Detect zones
        df['oversold_zone'] = df['rsi'] < self.oversold
        df['overbought_zone'] = df['rsi'] > self.overbought
        
        # Detect crosses
        df['enter_oversold'] = (~(df['rsi_prev'] < self.oversold)) & (df['rsi'] < self.oversold)
        df['exit_oversold'] = (df['rsi_prev'] < self.oversold) & (df['rsi'] >= self.oversold)
        df['enter_overbought'] = (~(df['rsi_prev'] > self.overbought)) & (df['rsi'] > self.overbought)
        df['exit_overbought'] = (df['rsi_prev'] > self.overbought) & (df['rsi'] <= self.overbought)
        
        # Get current bar
        current = df.iloc[-1]
        current_price = current['close']
        timestamp = df.index[-1]
        
        # Divergence detection
        divergence = {'bullish': False, 'bearish': False}
        if self.use_divergence:
            divergence = self.detect_divergence(df)
        
        # Buy signal: RSI exits oversold zone or bullish divergence
        if current['exit_oversold'] or (divergence['bullish'] and current['rsi'] < 40):
            stop_loss = current_price * 0.98  # 2% stop below entry
            take_profit = current_price * 1.04  # 4% target
            
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                timestamp=timestamp,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    'rsi': current['rsi'],
                    'rsi_prev': current['rsi_prev'],
                    'divergence': divergence['bullish'],
                    'signal_type': 'oversold_bounce'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"RSI BUY signal for {symbol} at ${current_price:.2f} "
                f"(RSI: {current['rsi']:.1f})"
            )
        
        # Sell signal: RSI exits overbought zone or bearish divergence
        elif current['exit_overbought'] or divergence['bearish']:
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                timestamp=timestamp,
                price=current_price,
                metadata={
                    'rsi': current['rsi'],
                    'divergence': divergence['bearish'],
                    'signal_type': 'overbought_reversal'
                }
            )
            signals.append(signal)
            self.logger.info(
                f"RSI SELL signal for {symbol} at ${current_price:.2f} "
                f"(RSI: {current['rsi']:.1f})"
            )
        
        # Mean reversion to middle (50) exit
        if self.exit_middle:
            df['middle_cross_up'] = (df['rsi_prev'] < 50) & (df['rsi'] >= 50)
            df['middle_cross_down'] = (df['rsi_prev'] > 50) & (df['rsi'] <= 50)
            
            if current['middle_cross_up'] and not any(s.signal_type == SignalType.SELL for s in signals):
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    metadata={
                        'rsi': current['rsi'],
                        'signal_type': 'mean_reversion_complete'
                    }
                )
                signals.append(signal)
                self.logger.info(f"RSI Middle Exit SELL for {symbol}")
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting RSI Mean Reversion live trading")
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
    strategy = RSIMeanReversionStrategy(
        symbols=['SPY', 'QQQ'],
        rsi_period=14,
        oversold=30,
        overbought=70
    )
    
    results = strategy.backtest()
    print(f"RSI Mean Reversion Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
