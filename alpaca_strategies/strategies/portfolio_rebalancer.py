"""
Portfolio Rebalancer Strategy
Maintain target asset allocation
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict
from alpaca_base_strategy import BaseStrategy, Signal

class PortfolioRebalancerStrategy(BaseStrategy):
    """Portfolio Rebalancing Strategy"""
    
    def __init__(self, config: dict):
        super().__init__('portfolio_rebalancer', config)
        self.target_allocation = config.get('target_allocation', {})
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)
    
    def get_current_allocation(self) -> Dict[str, float]:
        """Get current portfolio allocation"""
        account = self.get_account()
        positions = self.get_positions()
        
        if not account or not positions:
            return {}
        
        total_equity = float(account.equity)
        allocation = {}
        
        for symbol, pos in positions.items():
            market_value = float(pos.market_value)
            allocation[symbol] = market_value / total_equity
        
        return allocation
    
    def calculate_rebalance_trades(self) -> list:
        """Calculate trades needed to rebalance"""
        current = self.get_current_allocation()
        account = self.get_account()
        
        if not account:
            return []
        
        total_equity = float(account.equity)
        trades = []
        
        for symbol, target_pct in self.target_allocation.items():
            current_pct = current.get(symbol, 0)
            diff = target_pct - current_pct
            
            # Check if rebalance needed
            if abs(diff) > self.rebalance_threshold:
                target_value = total_equity * target_pct
                current_value = total_equity * current_pct
                trade_value = target_value - current_value
                
                trades.append({
                    'symbol': symbol,
                    'target_pct': target_pct,
                    'current_pct': current_pct,
                    'diff': diff,
                    'trade_value': trade_value
                })
        
        return trades
    
    def generate_signals(self, symbol: str) -> Optional[Signal]:
        """Not used for rebalancing"""
        return None
    
    def run(self):
        """Execute portfolio rebalancing"""
        if not self.enabled:
            return
        
        self.logger.info("Checking portfolio rebalancing needs...")
        
        trades = self.calculate_rebalance_trades()
        
        if not trades:
            self.logger.info("Portfolio is within rebalance thresholds")
            return
        
        self.logger.info(f"Rebalancing needed for {len(trades)} positions:")
        
        for trade in trades:
            symbol = trade['symbol']
            diff = trade['diff']
            trade_value = trade['trade_value']
            
            self.logger.info(f"  {symbol}: {trade['current_pct']:.1%} → {trade['target_pct']:.1%}")
            
            # Get current price
            df = self.get_historical_data(symbol, '1d', limit=5)
            if df.empty:
                continue
            
            price = df['close'].iloc[-1]
            qty = abs(int(trade_value / price))
            
            if qty < 1:
                continue
            
            from alpaca.trading.enums import OrderSide
            if diff > 0:  # Need to buy
                self.logger.info(f"    Buying {qty} shares of {symbol}")
                self.submit_market_order(symbol, OrderSide.BUY, qty)
            else:  # Need to sell
                self.logger.info(f"    Selling {qty} shares of {symbol}")
                self.submit_market_order(symbol, OrderSide.SELL, qty)

if __name__ == '__main__':
    from alpaca_config import STRATEGY_CONFIGS
    strategy = PortfolioRebalancerStrategy(STRATEGY_CONFIGS['portfolio_rebalancer'])
    strategy.run()
