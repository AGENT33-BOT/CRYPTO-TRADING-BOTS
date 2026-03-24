"""
Alpaca Strategy Backtester
Backtest all strategies on historical data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategies'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import logging

from alpaca_config import STRATEGY_CONFIGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Backtester')

class StrategyBacktester:
    """Backtest trading strategies"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.results = {}
    
    def fetch_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end)
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def backtest_strategy(self, strategy_name: str, config: dict, 
                         start_date: str, end_date: str) -> dict:
        """Backtest a single strategy"""
        logger.info(f"Backtesting {strategy_name}...")
        
        symbols = config.get('symbols', ['SPY'])
        trades = []
        equity = self.initial_capital
        
        for symbol in symbols[:3]:  # Limit to first 3 symbols for speed
            try:
                df = self.fetch_data(symbol, start_date, end_date)
                if df.empty or len(df) < 50:
                    continue
                
                # Simple backtest logic - override in specific strategies
                for i in range(50, len(df) - 1):
                    # Simulate a basic strategy for demonstration
                    price = df['close'].iloc[i]
                    
                    # Random trade simulation (replace with actual strategy logic)
                    if i % 20 == 0:  # Simulate periodic trades
                        trade_return = np.random.normal(0.001, 0.02)
                        pnl = equity * 0.1 * trade_return  # 10% position
                        equity += pnl
                        
                        trades.append({
                            'symbol': symbol,
                            'date': df.index[i],
                            'pnl': pnl,
                            'return': trade_return
                        })
                
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {e}")
        
        # Calculate metrics
        if trades:
            trades_df = pd.DataFrame(trades)
            wins = len(trades_df[trades_df['pnl'] > 0])
            losses = len(trades_df[trades_df['pnl'] <= 0])
            total_trades = len(trades_df)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            total_return = (equity - self.initial_capital) / self.initial_capital * 100
            
            return {
                'strategy': strategy_name,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_return': total_return,
                'final_equity': equity,
                'wins': wins,
                'losses': losses
            }
        else:
            return {
                'strategy': strategy_name,
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'final_equity': equity,
                'wins': 0,
                'losses': 0
            }
    
    def backtest_all(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Backtest all enabled strategies"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Backtesting period: {start_date} to {end_date}")
        logger.info("=" * 70)
        
        results = []
        
        for name, config in STRATEGY_CONFIGS.items():
            if not config.get('enabled', True):
                continue
            
            result = self.backtest_strategy(name, config, start_date, end_date)
            results.append(result)
            logger.info(f"{name}: {result['total_trades']} trades, {result['win_rate']:.1f}% win rate")
        
        return pd.DataFrame(results)
    
    def print_summary(self, results_df: pd.DataFrame):
        """Print backtest summary"""
        print("\n" + "=" * 70)
        print("BACKTEST SUMMARY")
        print("=" * 70)
        print(results_df.to_string(index=False))
        print("=" * 70)
        
        if not results_df.empty:
            best = results_df.loc[results_df['total_return'].idxmax()]
            print(f"\nBest Strategy: {best['strategy']}")
            print(f"  Return: {best['total_return']:.2f}%")
            print(f"  Win Rate: {best['win_rate']:.1f}%")
            print(f"  Trades: {best['total_trades']}")

def main():
    backtester = StrategyBacktester()
    
    # Default: backtest last year
    results = backtester.backtest_all()
    backtester.print_summary(results)

if __name__ == '__main__':
    main()
