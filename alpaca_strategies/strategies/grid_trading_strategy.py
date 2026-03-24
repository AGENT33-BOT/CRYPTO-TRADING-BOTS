"""
Grid Trading Strategy
Price-based grid order placement
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Tuple
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alpaca_base_strategy import BaseStrategy, Signal, SignalType
from alpaca_config import AlpacaConfig


class GridTradingStrategy(BaseStrategy):
    """
    Grid Trading Strategy.
    Places buy and sell orders at predetermined price levels (grid).
    Profits from sideways market movement by buying low and selling high
    within a defined price range.
    """
    
    def __init__(
        self,
        config: Optional[AlpacaConfig] = None,
        symbols: Optional[List[str]] = None,
        timeframe: str = "5Min",
        grid_levels: int = 5,
        grid_spacing_pct: float = 0.01,  # 1% between grids
        grid_upper_pct: float = 0.05,    # Upper bound from current price
        grid_lower_pct: float = 0.05,    # Lower bound from current price
        position_size_per_grid: float = 0.02,  # 2% per grid level
        rebalance_threshold: float = 0.02,
        **kwargs
    ):
        super().__init__(
            config=config,
            symbols=symbols,
            timeframe=timeframe,
            name="Grid_Trading"
        )
        self.grid_levels = grid_levels
        self.grid_spacing_pct = grid_spacing_pct
        self.grid_upper_pct = grid_upper_pct
        self.grid_lower_pct = grid_lower_pct
        self.position_size_per_grid = position_size_per_grid
        self.rebalance_threshold = rebalance_threshold
        
        # Track grid state per symbol
        self.grid_states: Dict[str, Dict] = {}
        self.active_grids: Dict[str, List[float]] = {}
        
        self.logger.info(
            f"Grid Trading: levels={grid_levels}, spacing={grid_spacing_pct*100}%"
        )
    
    def calculate_grid_levels(self, center_price: float) -> Tuple[List[float], List[float]]:
        """
        Calculate buy and sell grid levels
        
        Returns:
            Tuple of (buy_levels, sell_levels)
        """
        buy_levels = []
        sell_levels = []
        
        for i in range(1, self.grid_levels + 1):
            buy_price = center_price * (1 - self.grid_spacing_pct * i)
            sell_price = center_price * (1 + self.grid_spacing_pct * i)
            buy_levels.append(buy_price)
            sell_levels.append(sell_price)
        
        return sorted(buy_levels), sorted(sell_levels)
    
    def initialize_grid(self, symbol: str, current_price: float):
        """Initialize grid levels for a symbol"""
        buy_levels, sell_levels = self.calculate_grid_levels(current_price)
        
        self.active_grids[symbol] = {
            'center_price': current_price,
            'buy_levels': buy_levels,
            'sell_levels': sell_levels,
            'filled_buys': set(),
            'filled_sells': set(),
            'inventory': 0,
            'avg_entry': 0
        }
        
        self.logger.info(
            f"Initialized grid for {symbol}: center=${current_price:.2f}, "
            f"buys={['$%.2f' % p for p in buy_levels]}, "
            f"sells={['$%.2f' % p for p in sell_levels]}"
        )
    
    def needs_rebalance(self, symbol: str, current_price: float) -> bool:
        """Check if grid needs rebalancing due to price movement"""
        if symbol not in self.active_grids:
            return True
        
        center = self.active_grids[symbol]['center_price']
        price_change = abs(current_price - center) / center
        
        return price_change > self.rebalance_threshold
    
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """Generate grid trading signals"""
        signals = []
        
        if len(data) < 5:
            return signals
        
        current_price = data['close'].iloc[-1]
        timestamp = data.index[-1]
        
        # Initialize or rebalance grid
        if symbol not in self.active_grids or self.needs_rebalance(symbol, current_price):
            self.initialize_grid(symbol, current_price)
        
        grid = self.active_grids[symbol]
        
        # Check if price crossed any buy level
        for i, level in enumerate(grid['buy_levels']):
            level_key = f"buy_{i}"
            
            # Price at or below level and level not yet filled
            if current_price <= level and level_key not in grid['filled_buys']:
                portfolio_value = self.get_portfolio_value()
                position_value = portfolio_value * self.position_size_per_grid
                quantity = int(position_value / current_price)
                
                if quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        timestamp=timestamp,
                        price=current_price,
                        quantity=quantity,
                        metadata={
                            'grid_level': level,
                            'level_type': 'buy_grid',
                            'grid_center': grid['center_price']
                        }
                    )
                    signals.append(signal)
                    grid['filled_buys'].add(level_key)
                    
                    # Update inventory
                    total_cost = grid['inventory'] * grid['avg_entry'] + quantity * current_price
                    grid['inventory'] += quantity
                    if grid['inventory'] > 0:
                        grid['avg_entry'] = total_cost / grid['inventory']
                    
                    self.logger.info(
                        f"Grid BUY for {symbol} at ${current_price:.2f} "
                        f"(level: ${level:.2f})"
                    )
        
        # Check if price crossed any sell level (and we have inventory)
        if grid['inventory'] > 0:
            for i, level in enumerate(grid['sell_levels']):
                level_key = f"sell_{i}"
                
                # Price at or above level and level not yet filled
                if current_price >= level and level_key not in grid['filled_sells']:
                    # Only sell if profitable
                    if current_price > grid['avg_entry'] * 1.005:  # 0.5% profit minimum
                        quantity = min(
                            grid['inventory'],
                            int(self.get_portfolio_value() * self.position_size_per_grid / current_price)
                        )
                        
                        if quantity > 0:
                            signal = Signal(
                                symbol=symbol,
                                signal_type=SignalType.SELL,
                                timestamp=timestamp,
                                price=current_price,
                                quantity=quantity,
                                metadata={
                                    'grid_level': level,
                                    'level_type': 'sell_grid',
                                    'avg_entry': grid['avg_entry'],
                                    'profit_pct': (current_price - grid['avg_entry']) / grid['avg_entry'] * 100
                                }
                            )
                            signals.append(signal)
                            grid['filled_sells'].add(level_key)
                            grid['inventory'] -= quantity
                            
                            self.logger.info(
                                f"Grid SELL for {symbol} at ${current_price:.2f} "
                                f"(profit: {(current_price - grid['avg_entry']) / grid['avg_entry'] * 100:.2f}%)"
                            )
        
        # Reset filled levels if price returns to center area
        center_zone_upper = grid['center_price'] * (1 + self.grid_spacing_pct * 0.5)
        center_zone_lower = grid['center_price'] * (1 - self.grid_spacing_pct * 0.5)
        
        if center_zone_lower <= current_price <= center_zone_upper:
            # Reset grids to allow re-trading
            grid['filled_buys'] = set()
            grid['filled_sells'] = set()
        
        return signals
    
    def run(self):
        """Execute live trading"""
        self.logger.info("Starting Grid Trading live trading")
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
                time.sleep(30)
                
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
    strategy = GridTradingStrategy(
        symbols=['BTC-USD'],  # Grid works well for crypto
        grid_levels=5,
        grid_spacing_pct=0.02
    )
    
    results = strategy.backtest()
    print(f"Grid Trading Results:")
    print(f"  Total Return: {results.get('total_return', 0)*100:.2f}%")
