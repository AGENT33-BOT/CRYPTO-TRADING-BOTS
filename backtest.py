# Backtesting Module for Trendline Strategy
# Tests strategy on historical data

import pandas as pd
import numpy as np
import talib
from scipy import stats
from datetime import datetime

class TrendlineBacktester:
    def __init__(self, initial_balance=50.0, risk_per_trade=0.015):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.rr_ratio = 2.0
        self.positions = []
        self.trades = []
        
        # Strategy parameters
        self.lookback = 100
        self.min_swings = 3
        self.tolerance = 0.008
        self.volume_mult = 1.5
    
    def find_swing_points(self, highs, lows, window=5):
        """Find swing highs and lows"""
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(highs) - window):
            # Swing high
            if all(highs[i] > highs[i-j] for j in range(1, window+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, window+1)):
                swing_highs.append((i, highs[i]))
            
            # Swing low
            if all(lows[i] < lows[i-j] for j in range(1, window+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, window+1)):
                swing_lows.append((i, lows[i]))
        
        return swing_highs, swing_lows
    
    def fit_trendline(self, points, tolerance=0.008):
        """Fit trendline"""
        if len(points) < self.min_swings:
            return None
        
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])
        
        slope, intercept, r_value, _, _ = stats.linregress(x, y)
        
        touches = 0
        for idx, price in points:
            expected = slope * idx + intercept
            deviation = abs(price - expected) / expected
            if deviation <= tolerance:
                touches += 1
        
        if touches >= self.min_swings:
            return {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value**2,
                'touches': touches
            }
        return None
    
    def backtest(self, df):
        """Run backtest on historical data"""
        print(f"Starting backtest on {len(df)} candles")
        print(f"Initial balance: ${self.initial_balance}")
        print("="*70)
        
        for i in range(100, len(df) - 1):
            # Get window of data
            window_df = df.iloc[i-100:i+1].reset_index(drop=True)
            
            # Find swing points
            highs = window_df['high'].values
            lows = window_df['low'].values
            swing_highs, swing_lows = self.find_swing_points(highs, lows)
            
            # Current candle
            current_open = df['open'].iloc[i]
            current_close = df['close'].iloc[i]
            current_high = df['high'].iloc[i]
            current_low = df['low'].iloc[i]
            current_idx = 100  # Last index in window
            
            # Calculate RSI
            rsi = talib.RSI(df['close'].values[:i+1], timeperiod=14)[-1]
            
            # Check volume
            current_vol = df['volume'].iloc[i]
            avg_vol = df['volume'].iloc[i-20:i].mean()
            vol_ok = current_vol > (avg_vol * self.volume_mult)
            
            # Check support trendlines (LONG)
            if len(swing_lows) >= 3:
                for j in range(len(swing_lows) - 2):
                    points = swing_lows[j:]
                    tl = self.fit_trendline(points)
                    
                    if tl and tl['slope'] > 0:  # Upward
                        tl_value = tl['slope'] * current_idx + tl['intercept']
                        
                        # Check touch
                        if current_low <= tl_value * 1.02:
                            if current_close > current_open:  # Bullish
                                if 30 <= rsi <= 50 and vol_ok:
                                    # Execute trade
                                    entry = current_close
                                    stop = tl_value * 0.97
                                    target = entry + (entry - stop) * 2
                                    
                                    # Check if trade hits
                                    future_prices = df['close'].iloc[i+1:min(i+50, len(df))]
                                    exit_price = None
                                    exit_reason = None
                                    
                                    for fp in future_prices:
                                        if fp <= stop:
                                            exit_price = stop
                                            exit_reason = "STOP"
                                            break
                                        elif fp >= target:
                                            exit_price = target
                                            exit_reason = "TARGET"
                                            break
                                    
                                    if exit_price is None:
                                        exit_price = df['close'].iloc[-1]
                                        exit_reason = "END"
                                    
                                    pnl = (exit_price - entry) / entry * 100
                                    self.trades.append({
                                        'type': 'LONG',
                                        'entry': entry,
                                        'exit': exit_price,
                                        'pnl': pnl,
                                        'reason': exit_reason,
                                        'rsi': rsi,
                                        'r_squared': tl['r_squared']
                                    })
            
            # Check resistance trendlines (SHORT)
            if len(swing_highs) >= 3:
                for j in range(len(swing_highs) - 2):
                    points = swing_highs[j:]
                    tl = self.fit_trendline(points)
                    
                    if tl and tl['slope'] < 0:  # Downward
                        tl_value = tl['slope'] * current_idx + tl['intercept']
                        
                        if current_high >= tl_value * 0.98:
                            if current_close < current_open:  # Bearish
                                if 50 <= rsi <= 70 and vol_ok:
                                    entry = current_close
                                    stop = tl_value * 1.03
                                    target = entry - (stop - entry) * 2
                                    
                                    future_prices = df['close'].iloc[i+1:min(i+50, len(df))]
                                    exit_price = None
                                    exit_reason = None
                                    
                                    for fp in future_prices:
                                        if fp >= stop:
                                            exit_price = stop
                                            exit_reason = "STOP"
                                            break
                                        elif fp <= target:
                                            exit_price = target
                                            exit_reason = "TARGET"
                                            break
                                    
                                    if exit_price is None:
                                        exit_price = df['close'].iloc[-1]
                                        exit_reason = "END"
                                    
                                    pnl = (entry - exit_price) / entry * 100
                                    self.trades.append({
                                        'type': 'SHORT',
                                        'entry': entry,
                                        'exit': exit_price,
                                        'pnl': pnl,
                                        'reason': exit_reason,
                                        'rsi': rsi,
                                        'r_squared': tl['r_squared']
                                    })
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate backtest report"""
        if not self.trades:
            return "No trades found in backtest period"
        
        df = pd.DataFrame(self.trades)
        
        wins = len(df[df['pnl'] > 0])
        losses = len(df[df['pnl'] <= 0])
        total = len(df)
        win_rate = wins / total * 100 if total > 0 else 0
        
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
        avg_loss = df[df['pnl'] <= 0]['pnl'].mean() if losses > 0 else 0
        total_pnl = df['pnl'].sum()
        
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        print(f"Total Trades: {total}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"\nAverage Win: +{avg_win:.2f}%")
        print(f"Average Loss: {avg_loss:.2f}%")
        print(f"Total PnL: {total_pnl:.2f}%")
        print(f"\nSample Trades:")
        print(df.head(10).to_string())
        print("="*70)
        
        return df

if __name__ == "__main__":
    print("Backtest module ready")
    print("Use with historical data from exchange")
