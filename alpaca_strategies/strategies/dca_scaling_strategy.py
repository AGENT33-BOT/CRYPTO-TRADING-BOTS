"""
DCA Scaling Strategy
Dollar Cost Averaging with position scaling
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpaca_base_strategy import BaseStrategy, Signal, SignalType
from alpaca_config import AlpacaConfig


class DCAScalingStrategy(BaseStrategy):
    """
    Dollar Cost Averaging with Scaling Strategy.
    Systematically invests at regular intervals and scales into positions
    on drawdowns. Reduces timing risk and averages entry prices.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "1D",
        base_investment_pct: float = 0.02,  # 2% base investment
        dca_interval_days: int = 7,          # Weekly DCA
        scale_multiplier: float = 1.5,       # Increase size on dips
        max_scale_levels: int = 3,           # Max scaling levels
        drawdown_thresholds: List[float] = None,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="DCA_Scaling"
        )
        self.base_investment_pct = base_investment_pct
        self.dca_interval_days = dca_interval_days
        self.scale_multiplier = scale_multiplier
        self.max_scale_levels = max_scale_levels
        self.drawdown_thresholds = drawdown_thresholds or [-0.05, -0.10, -0.15]
        
        # Track DCA state per symbol
        self.dca_states: Dict[str, Dict] = {}
        self.last_dca_dates: Dict[str, datetime] = {}
        
        self.logger.info(
            f"DCA Scaling: interval={dca_interval_days}d, "
            f"base={base_investment_pct*100}%, scales={max_scale_levels}"
        )
    
    def get_drawdown_level(self, symbol: str, current_price: float) -> int:
        """Determine scaling level based on drawdown from entry"""
        if symbol not in self.dca_states:
            return 0
        
        state = self.dca_states[symbol]
        if 'avg_entry' not in state or state['avg_entry'] == 0:
            return 0
        
        drawdown = (current_price - state['avg_entry']) / state['avg_entry']
        
        for i, threshold in enumerate(self.drawdown_thresholds):
            if drawdown <= threshold:
                return min(i + 1, self.max_scale_levels)
        
        return 0
    
    def calculate_investment_size(self, symbol: str, drawdown_level: int) -> float:
        """Calculate investment amount based on drawdown level"""
        portfolio_value = self.get_portfolio_value()
        base_amount = portfolio_value * self.base_investment_pct
        
        # Scale up based on drawdown
        multiplier = self.scale_multiplier ** drawdown_level
        
        return base_amount * multiplier
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate DCA signals"""
        signals = []
        
        if len(data) < 5:
            return signals
        
        current_price = data['close'].iloc[-1]
        timestamp = data.index[-1]
        
        # Initialize state
        if symbol not in self.dca_states:
            self.dca_states[symbol] = {
                'avg_entry': 0,
                'total_shares': 0,
                'total_invested': 0,
                'dca_count': 0
            }
            self.last_dca_dates[symbol] = timestamp - timedelta(days=self.dca_interval_days + 1)
        
        state = self.dca_states[symbol]
        last_dca = self.last_dca_dates[symbol]
        
        # Check if enough time passed since last DCA
        days_since_last = (timestamp - last_dca).days
        time_for_dca = days_since_last >= self.dca_interval_days
        
        # Check drawdown levels for scaling
        drawdown_level = self.get_drawdown_level(symbol, current_price)
        scale_trigger = drawdown_level > 0 and days_since_last >= 1  # Faster on drawdowns
        
        # Generate DCA signal
        if time_for_dca or scale_trigger:
            # Determine investment size
            if scale_trigger:
                investment_amount = self.calculate_investment_size(symbol, drawdown_level)
                signal_type = 'scale_in'
            else:
                investment_amount = self.calculate_investment_size(symbol, 0)
                signal_type = 'regular_dca'
            
            quantity = int(investment_amount / current_price)
            
            if quantity > 0:
                # Adjust stop loss based on DCA level
                if drawdown_level > 0:
                    stop_loss = current_price * (1 + self.drawdown_thresholds[drawdown_level - 1] - 0.05)
                else:
                    stop_loss = current_price * 0.90  # 10% stop for regular DCA
                
                signal = Signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    metadata={
                        'dca_type': signal_type,
                        'drawdown_level': drawdown_level,
                        'investment_amount': investment_amount,
                        'dca_count': state['dca_count'] + 1,
                        'avg_entry_before': state['avg_entry']
                    }
                )
                signals.append(signal)
                
                # Update state
                state['total_invested'] += investment_amount
                state['total_shares'] += quantity
                state['avg_entry'] = state['total_invested'] / state['total_shares']
                state['dca_count'] += 1
                self.last_dca_dates[symbol] = timestamp
                
                self.logger.info(
                    f"DCA BUY for {symbol}: ${investment_amount:.0f} at ${current_price:.2f} "
                    f"({signal_type}, level {drawdown_level})"
                )
        
        # Take profit signal (sell portion on significant gains)
        if state['total_shares'] > 0 and state['avg_entry'] > 0:
            gain_pct = (current_price - state['avg_entry']) / state['avg_entry']
            
            if gain_pct >= 0.20:  # 20% gain - take profit on half
                sell_quantity = state['total_shares'] // 2
                
                if sell_quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        timestamp=timestamp,
                        price=current_price,
                        quantity=sell_quantity,
                        metadata={
                            'sell_type': 'take_profit',
                            'gain_pct': gain_pct * 100,
                            'avg_entry': state['avg_entry']
                        }
                    )
                    signals.append(signal)
                    
                    # Update state
                    state['total_shares'] -= sell_quantity
                    if state['total_shares'] > 0:
                        state['total_invested'] = state['total_shares'] * state['avg_entry']
                    else:
                        state['avg_entry'] = 0
                        state['total_invested'] = 0
                    
                    self.logger.info(
                        f"DCA TAKE PROFIT for {symbol}: {sell_quantity} shares at ${current_price:.2f} "
                        f"({gain_pct*100:.1f}% gain)"
                    )
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting DCA Scaling live trading")
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
                            self.submit_order(
                                symbol=symbol,
                                side=OrderSide.BUY,
                                quantity=signal.quantity
                            )
                        
                        elif signal.signal_type == SignalType.SELL:
                            self.submit_order(
                                symbol=symbol,
                                side=OrderSide.SELL,
                                quantity=signal.quantity
                            )
                
                import time
                time.sleep(3600)  # Check hourly
                
            except Exception as e:
                self.logger.error(f"Error: {e}")
                import time
                time.sleep(3600)
    
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
    strategy = DCAScalingStrategy(
        symbols=['SPY', 'QQQ'],
        base_investment_pct=0.02,
        dca_interval_days=7,
        max_scale_levels=3
    )
    
    results = strategy.backtest()
    print(f"DCA Scaling Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
    print(f"  Trades: {results.get('total_trades', 0)}")
