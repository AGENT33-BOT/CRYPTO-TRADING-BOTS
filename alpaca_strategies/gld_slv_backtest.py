"""
GLD + SLV Strategy Backtester
Uses Alpaca API for historical data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging

from alpaca_config import STRATEGY_CONFIGS, ALPACA_API_KEY, ALPACA_SECRET_KEY

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('GLD_SLV_Backtest')

class GLDSLBacktester:
    """Backtest GLD + SLV strategies"""
    
    def __init__(self):
        self.data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        self.initial_capital = 10000
        
    def fetch_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """Fetch historical bars from Alpaca"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start,
                end=end
            )
            
            bars = self.data_client.get_stock_bars(request)
            df = bars.df.reset_index()
            df = df[df['symbol'] == symbol].copy()
            df.set_index('timestamp', inplace=True)
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            return df
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # EMAs
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # Z-Score
        df['zscore'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).std()
        
        # Stochastic
        low14 = df['low'].rolling(14).min()
        high14 = df['high'].rolling(14).max()
        df['stoch_k'] = 100 * ((df['close'] - low14) / (high14 - low14))
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        
        return df
    
    def backtest_rsi(self, df: pd.DataFrame, position_size: float = 1000) -> dict:
        """RSI Mean Reversion backtest"""
        trades = []
        equity = self.initial_capital
        position = None
        entry_price = 0
        
        for i in range(20, len(df)):
            price = df['close'].iloc[i]
            rsi = df['rsi'].iloc[i]
            
            if position is None and rsi < 30:
                # Buy signal
                position = 'long'
                entry_price = price
                shares = position_size / price
            elif position == 'long' and rsi > 70:
                # Sell signal
                pnl = shares * (price - entry_price)
                equity += pnl
                trades.append({
                    'type': 'RSI Reversion',
                    'pnl': pnl,
                    'return_pct': (price - entry_price) / entry_price * 100,
                    'entry': entry_price,
                    'exit': price
                })
                position = None
        
        return self._calculate_metrics(trades, equity, 'RSI Mean Reversion')
    
    def backtest_bb(self, df: pd.DataFrame, position_size: float = 1000) -> dict:
        """Bollinger Bands Mean Reversion backtest"""
        trades = []
        equity = self.initial_capital
        position = None
        entry_price = 0
        
        for i in range(20, len(df)):
            price = df['close'].iloc[i]
            bb_pct = df['bb_pct'].iloc[i]
            
            if position is None and bb_pct < 0.05:
                # Buy at lower band
                position = 'long'
                entry_price = price
                shares = position_size / price
            elif position == 'long' and bb_pct > 0.95:
                # Sell at upper band
                pnl = shares * (price - entry_price)
                equity += pnl
                trades.append({
                    'type': 'BB Reversion',
                    'pnl': pnl,
                    'return_pct': (price - entry_price) / entry_price * 100,
                    'entry': entry_price,
                    'exit': price
                })
                position = None
        
        return self._calculate_metrics(trades, equity, 'Bollinger Bands')
    
    def backtest_ema(self, df: pd.DataFrame, position_size: float = 1000) -> dict:
        """EMA Crossover backtest"""
        trades = []
        equity = self.initial_capital
        position = None
        entry_price = 0
        
        for i in range(25, len(df)):
            price = df['close'].iloc[i]
            ema9 = df['ema9'].iloc[i]
            ema21 = df['ema21'].iloc[i]
            prev_ema9 = df['ema9'].iloc[i-1]
            prev_ema21 = df['ema21'].iloc[i-1]
            
            # Bullish crossover
            if position is None and prev_ema9 <= prev_ema21 and ema9 > ema21:
                position = 'long'
                entry_price = price
                shares = position_size / price
            # Bearish crossover
            elif position == 'long' and prev_ema9 >= prev_ema21 and ema9 < ema21:
                pnl = shares * (price - entry_price)
                equity += pnl
                trades.append({
                    'type': 'EMA Crossover',
                    'pnl': pnl,
                    'return_pct': (price - entry_price) / entry_price * 100,
                    'entry': entry_price,
                    'exit': price
                })
                position = None
        
        return self._calculate_metrics(trades, equity, 'EMA Crossover')
    
    def backtest_zscore(self, df: pd.DataFrame, position_size: float = 1000) -> dict:
        """Z-Score Reversion backtest"""
        trades = []
        equity = self.initial_capital
        position = None
        entry_price = 0
        
        for i in range(25, len(df)):
            price = df['close'].iloc[i]
            zscore = df['zscore'].iloc[i]
            
            if position is None and zscore < -2.0:
                # Buy when 2 std dev below mean
                position = 'long'
                entry_price = price
                shares = position_size / price
            elif position == 'long' and zscore > 0:
                # Sell when back to mean
                pnl = shares * (price - entry_price)
                equity += pnl
                trades.append({
                    'type': 'Z-Score Reversion',
                    'pnl': pnl,
                    'return_pct': (price - entry_price) / entry_price * 100,
                    'entry': entry_price,
                    'exit': price
                })
                position = None
        
        return self._calculate_metrics(trades, equity, 'Z-Score Reversion')
    
    def backtest_stoch(self, df: pd.DataFrame, position_size: float = 1000) -> dict:
        """Stochastic Reversion backtest"""
        trades = []
        equity = self.initial_capital
        position = None
        entry_price = 0
        
        for i in range(20, len(df)):
            price = df['close'].iloc[i]
            k = df['stoch_k'].iloc[i]
            d = df['stoch_d'].iloc[i]
            prev_k = df['stoch_k'].iloc[i-1]
            
            # Buy when %K crosses above %D in oversold
            if position is None and prev_k < 20 and k > d and k < 30:
                position = 'long'
                entry_price = price
                shares = position_size / price
            # Sell when overbought
            elif position == 'long' and k > 80:
                pnl = shares * (price - entry_price)
                equity += pnl
                trades.append({
                    'type': 'Stochastic Reversion',
                    'pnl': pnl,
                    'return_pct': (price - entry_price) / entry_price * 100,
                    'entry': entry_price,
                    'exit': price
                })
                position = None
        
        return self._calculate_metrics(trades, equity, 'Stochastic Reversion')
    
    def backtest_pairs(self, gld_df: pd.DataFrame, slv_df: pd.DataFrame, position_size: float = 1000) -> dict:
        """GLD/SLV Pairs Trading backtest"""
        trades = []
        equity = self.initial_capital
        position = None
        
        # Merge and calculate spread
        merged = pd.merge(gld_df[['close']], slv_df[['close']], 
                         left_index=True, right_index=True, suffixes=('_gld', '_slv'))
        merged['ratio'] = merged['close_gld'] / merged['close_slv']
        merged['ratio_mean'] = merged['ratio'].rolling(60).mean()
        merged['ratio_std'] = merged['ratio'].rolling(60).std()
        merged['zscore'] = (merged['ratio'] - merged['ratio_mean']) / merged['ratio_std']
        
        for i in range(70, len(merged)):
            zscore = merged['zscore'].iloc[i]
            
            if position is None and abs(zscore) > 2.0:
                # Enter pairs trade
                position = 'long_gld_short_slv' if zscore < 0 else 'short_gld_long_slv'
                entry_zscore = zscore
                entry_gld = merged['close_gld'].iloc[i]
                entry_slv = merged['close_slv'].iloc[i]
            elif position and abs(zscore) < 0.5:
                # Exit pairs trade
                exit_gld = merged['close_gld'].iloc[i]
                exit_slv = merged['close_slv'].iloc[i]
                
                if position == 'long_gld_short_slv':
                    gld_pnl = (exit_gld - entry_gld) / entry_gld
                    slv_pnl = (entry_slv - exit_slv) / entry_slv
                else:
                    gld_pnl = (entry_gld - exit_gld) / entry_gld
                    slv_pnl = (exit_slv - entry_slv) / entry_slv
                
                total_pnl = (gld_pnl + slv_pnl) * position_size
                equity += total_pnl
                trades.append({
                    'type': 'Pairs Trade',
                    'pnl': total_pnl,
                    'return_pct': (gld_pnl + slv_pnl) * 100,
                    'entry': f'GLD:{entry_gld:.2f}/SLV:{entry_slv:.2f}',
                    'exit': f'GLD:{exit_gld:.2f}/SLV:{exit_slv:.2f}'
                })
                position = None
        
        return self._calculate_metrics(trades, equity, 'GLD/SLV Pairs')
    
    def _calculate_metrics(self, trades, equity, name):
        """Calculate performance metrics"""
        if not trades:
            return {
                'strategy': name,
                'trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'avg_trade': 0,
                'profit_factor': 0,
                'final_equity': equity
            }
        
        df = pd.DataFrame(trades)
        wins = len(df[df['pnl'] > 0])
        losses = len(df[df['pnl'] <= 0])
        win_rate = (wins / len(df) * 100) if len(df) > 0 else 0
        total_return = (equity - self.initial_capital) / self.initial_capital * 100
        
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            'strategy': name,
            'trades': len(df),
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_trade': df['pnl'].mean(),
            'profit_factor': profit_factor,
            'final_equity': equity,
            'wins': wins,
            'losses': losses
        }
    
    def run_all(self, days: int = 730):
        """Run all backtests"""
        print("=" * 70)
        print(f"GLD + SLV STRATEGY BACKTEST")
        print(f"Period: Last {days} days | Initial Capital: ${self.initial_capital:,.0f}")
        print("=" * 70)
        
        # Fetch data
        print("\n[1] Fetching historical data...")
        gld = self.fetch_data('GLD', days)
        slv = self.fetch_data('SLV', days)
        
        if gld.empty or slv.empty:
            print("Error: Could not fetch data")
            return
        
        print(f"    GLD: {len(gld)} bars")
        print(f"    SLV: {len(slv)} bars")
        
        # Calculate indicators
        print("\n[2] Calculating indicators...")
        gld = self.calculate_indicators(gld)
        slv = self.calculate_indicators(slv)
        
        # Run backtests
        print("\n[3] Running backtests...")
        results = []
        
        for symbol, df in [('GLD', gld), ('SLV', slv)]:
            print(f"\n    --- {symbol} ---")
            results.append(self.backtest_rsi(df))
            results.append(self.backtest_bb(df))
            results.append(self.backtest_ema(df))
            results.append(self.backtest_zscore(df))
            results.append(self.backtest_stoch(df))
        
        # Pairs trading
        print(f"\n    --- GLD/SLV PAIRS ---")
        results.append(self.backtest_pairs(gld, slv))
        
        # Print summary
        print("\n" + "=" * 70)
        print("BACKTEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"{'Strategy':<25} {'Trades':>8} {'Win%':>8} {'Return%':>10} {'Avg $':>10} {'PF':>6}")
        print("-" * 70)
        
        for r in results:
            print(f"{r['strategy']:<25} {r['trades']:>8} {r['win_rate']:>7.1f}% {r['total_return']:>9.2f}% ${r['avg_trade']:>8.2f} {r['profit_factor']:>6.2f}")
        
        # Best performer
        best = max(results, key=lambda x: x['total_return'])
        print("\n" + "=" * 70)
        print(f"BEST PERFORMER: {best['strategy']}")
        print(f"  Total Return: {best['total_return']:.2f}%")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Trades: {best['trades']}")
        print(f"  Profit Factor: {best['profit_factor']:.2f}")
        print("=" * 70)
        
        return results

if __name__ == '__main__':
    backtester = GLDSLBacktester()
    backtester.run_all(days=730)
