"""
Multi-Strategy Backtester for Bybit Futures
Tests: Trend Following, Mean Reversion, Breakout strategies
"""

import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
import ccxt
import json

class MultiStrategyBacktester:
    def __init__(self, initial_balance=100.0, leverage=3):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.leverage = leverage
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def fetch_historical_data(self, symbol, timeframe='1h', limit=500):
        """Fetch OHLCV data from Bybit"""
        print(f"Fetching {limit} candles for {symbol} ({timeframe})...")
        
        exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['rsi_ma'] = df['rsi'].rolling(window=9).mean()
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
        )
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # EMAs
        df['ema_9'] = talib.EMA(df['close'], timeperiod=9)
        df['ema_21'] = talib.EMA(df['close'], timeperiod=21)
        df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
        
        # ATR for volatility
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['atr_pct'] = df['atr'] / df['close'] * 100
        
        # Volume
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        return df
    
    def strategy_trend_following(self, df, i):
        """
        Trend Following Strategy
        Entry: EMA crossover + RSI confirmation
        Exit: Opposite crossover or trailing stop
        """
        if i < 50:  # Need enough data
            return None
        
        current = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Long signal
        if (prev['ema_9'] <= prev['ema_21'] and 
            current['ema_9'] > current['ema_21'] and
            current['rsi'] > 50 and
            current['volume_ratio'] > 1.2):
            return {
                'signal': 'LONG',
                'confidence': min(95, 60 + (current['rsi'] - 50) * 1.5),
                'entry_price': current['close'],
                'stop_loss': current['close'] - (current['atr'] * 2),
                'take_profit': current['close'] + (current['atr'] * 4)
            }
        
        # Short signal
        if (prev['ema_9'] >= prev['ema_21'] and 
            current['ema_9'] < current['ema_21'] and
            current['rsi'] < 50 and
            current['volume_ratio'] > 1.2):
            return {
                'signal': 'SHORT',
                'confidence': min(95, 60 + (50 - current['rsi']) * 1.5),
                'entry_price': current['close'],
                'stop_loss': current['close'] + (current['atr'] * 2),
                'take_profit': current['close'] - (current['atr'] * 4)
            }
        
        return None
    
    def strategy_mean_reversion(self, df, i):
        """
        Mean Reversion Strategy
        Entry: Price touches Bollinger Band extreme + RSI extreme
        Exit: Middle band or opposite band
        """
        if i < 20:
            return None
        
        current = df.iloc[i]
        
        # Long signal - oversold bounce
        if (current['bb_position'] < 0.1 and 
            current['rsi'] < 35 and
            current['volume_ratio'] > 1.0):
            return {
                'signal': 'LONG',
                'confidence': min(95, 70 + (35 - current['rsi']) * 1.5),
                'entry_price': current['close'],
                'stop_loss': current['bb_lower'] * 0.99,
                'take_profit': current['bb_middle']
            }
        
        # Short signal - overbought reversal
        if (current['bb_position'] > 0.9 and 
            current['rsi'] > 65 and
            current['volume_ratio'] > 1.0):
            return {
                'signal': 'SHORT',
                'confidence': min(95, 70 + (current['rsi'] - 65) * 1.5),
                'entry_price': current['close'],
                'stop_loss': current['bb_upper'] * 1.01,
                'take_profit': current['bb_middle']
            }
        
        return None
    
    def strategy_breakout(self, df, i):
        """
        Breakout Strategy
        Entry: Price breaks above/below recent highs/lows with volume
        Exit: Trailing stop or reversal
        """
        if i < 50:
            return None
        
        lookback = 20
        current = df.iloc[i]
        
        recent_high = df['high'].iloc[i-lookback:i].max()
        recent_low = df['low'].iloc[i-lookback:i].min()
        
        # Long breakout
        if (current['close'] > recent_high * 0.995 and 
            current['volume_ratio'] > 1.5 and
            current['rsi'] > 55):
            return {
                'signal': 'LONG',
                'confidence': min(95, 65 + (current['volume_ratio'] - 1) * 20),
                'entry_price': current['close'],
                'stop_loss': recent_low,
                'take_profit': current['close'] + (current['close'] - recent_low) * 2
            }
        
        # Short breakout
        if (current['close'] < recent_low * 1.005 and 
            current['volume_ratio'] > 1.5 and
            current['rsi'] < 45):
            return {
                'signal': 'SHORT',
                'confidence': min(95, 65 + (current['volume_ratio'] - 1) * 20),
                'entry_price': current['close'],
                'stop_loss': recent_high,
                'take_profit': current['close'] - (recent_high - current['close']) * 2
            }
        
        return None
    
    def strategy_orb(self, df, i):
        """
        ORB (Opening Range Breakout) Strategy
        For crypto 24/7 markets: Uses first N candles of each 4h/8h session as "opening range"
        Entry: Price breaks above/below opening range high/low with volume confirmation
        Exit: Opposite side of range or trailing stop
        """
        if i < 24:  # Need at least 24 candles of data
            return None
        
        # Define opening range as first 4 candles (e.g., first 4 hours on 1h chart)
        opening_range_periods = 4
        
        # Calculate session start (every 24 candles for daily sessions on 1h chart)
        session_start = (i // 24) * 24
        
        # Only trade within the first 4-20 candles of a session
        candles_into_session = i - session_start
        if candles_into_session < opening_range_periods or candles_into_session > 20:
            return None
        
        current = df.iloc[i]
        
        # Calculate opening range (first 4 candles of session)
        orb_high = df['high'].iloc[session_start:session_start + opening_range_periods].max()
        orb_low = df['low'].iloc[session_start:session_start + opening_range_periods].min()
        orb_range = orb_high - orb_low
        
        # Avoid trading if opening range is too small (choppy market)
        orb_range_pct = orb_range / orb_low * 100
        if orb_range_pct < 0.3:  # Less than 0.3% range
            return None
        
        # Check for breakout above opening range high
        if (current['close'] > orb_high and 
            current['volume_ratio'] > 1.3 and
            current['rsi'] > 50 and
            current['rsi'] < 75):  # Not overbought
            
            # Dynamic position sizing based on range volatility
            confidence = min(95, 70 + (current['volume_ratio'] - 1) * 25 + orb_range_pct * 2)
            
            return {
                'signal': 'LONG',
                'confidence': confidence,
                'entry_price': current['close'],
                'stop_loss': orb_low - (orb_range * 0.1),  # Slightly below orb low
                'take_profit': current['close'] + (orb_range * 2)  # 2x range extension
            }
        
        # Check for breakdown below opening range low
        if (current['close'] < orb_low and 
            current['volume_ratio'] > 1.3 and
            current['rsi'] < 50 and
            current['rsi'] > 25):  # Not oversold
            
            confidence = min(95, 70 + (current['volume_ratio'] - 1) * 25 + orb_range_pct * 2)
            
            return {
                'signal': 'SHORT',
                'confidence': confidence,
                'entry_price': current['close'],
                'stop_loss': orb_high + (orb_range * 0.1),  # Slightly above orb high
                'take_profit': current['close'] - (orb_range * 2)  # 2x range extension
            }
        
        return None
        
        recent_high = df['high'].iloc[i-lookback:i].max()
        recent_low = df['low'].iloc[i-lookback:i].min()
        
        # Long breakout
        if (current['close'] > recent_high * 0.995 and 
            current['volume_ratio'] > 1.5 and
            current['rsi'] > 55):
            return {
                'signal': 'LONG',
                'confidence': min(95, 65 + (current['volume_ratio'] - 1) * 20),
                'entry_price': current['close'],
                'stop_loss': recent_low,
                'take_profit': current['close'] + (current['close'] - recent_low) * 2
            }
        
        # Short breakout
        if (current['close'] < recent_low * 1.005 and 
            current['volume_ratio'] > 1.5 and
            current['rsi'] < 45):
            return {
                'signal': 'SHORT',
                'confidence': min(95, 65 + (current['volume_ratio'] - 1) * 20),
                'entry_price': current['close'],
                'stop_loss': recent_high,
                'take_profit': current['close'] - (recent_high - current['close']) * 2
            }
        
        return None
    
    def run_backtest(self, symbol, strategy_name, timeframe='1h', limit=500, 
                     min_confidence=70, risk_per_trade=0.02):
        """Run backtest for a specific strategy"""
        
        print(f"\n{'='*70}")
        print(f"BACKTEST: {strategy_name} on {symbol}")
        print(f"Timeframe: {timeframe} | Min Confidence: {min_confidence}%")
        print(f"Risk per trade: {risk_per_trade*100}% | Leverage: {self.leverage}x")
        print('='*70)
        
        # Fetch and prepare data
        df = self.fetch_historical_data(symbol, timeframe, limit)
        df = self.calculate_indicators(df)
        
        # Select strategy
        strategies = {
            'trend_following': self.strategy_trend_following,
            'mean_reversion': self.strategy_mean_reversion,
            'breakout': self.strategy_breakout,
            'orb': self.strategy_orb
        }
        strategy_func = strategies.get(strategy_name, self.strategy_trend_following)
        
        # Reset state
        self.balance = self.initial_balance
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
        position = None
        
        # Run simulation
        for i in range(50, len(df) - 1):
            current = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Record equity
            self.equity_curve.append({
                'timestamp': current.name,
                'balance': self.balance,
                'price': current['close']
            })
            
            # Check if position is open
            if position:
                exit_price = None
                exit_reason = None
                
                # Check stop loss
                if position['side'] == 'LONG':
                    if current['low'] <= position['stop_loss']:
                        exit_price = position['stop_loss']
                        exit_reason = 'STOP_LOSS'
                    elif current['high'] >= position['take_profit']:
                        exit_price = position['take_profit']
                        exit_reason = 'TAKE_PROFIT'
                else:  # SHORT
                    if current['high'] >= position['stop_loss']:
                        exit_price = position['stop_loss']
                        exit_reason = 'STOP_LOSS'
                    elif current['low'] <= position['take_profit']:
                        exit_price = position['take_profit']
                        exit_reason = 'TAKE_PROFIT'
                
                if exit_price:
                    # Close position
                    if position['side'] == 'LONG':
                        pnl_pct = (exit_price - position['entry']) / position['entry'] * 100
                    else:
                        pnl_pct = (position['entry'] - exit_price) / exit_price * 100
                    
                    pnl_usd = position['size'] * (pnl_pct / 100) * self.leverage
                    self.balance += pnl_usd
                    
                    self.trades.append({
                        'symbol': symbol,
                        'side': position['side'],
                        'entry': position['entry'],
                        'exit': exit_price,
                        'entry_time': position['time'],
                        'exit_time': current.name,
                        'pnl_pct': pnl_pct,
                        'pnl_usd': pnl_usd,
                        'reason': exit_reason,
                        'confidence': position['confidence']
                    })
                    
                    position = None
            
            # Look for new entry (only if no position)
            if not position:
                signal = strategy_func(df, i)
                
                if signal and signal['confidence'] >= min_confidence:
                    position_size = self.balance * risk_per_trade
                    
                    position = {
                        'side': signal['signal'],
                        'entry': signal['entry_price'],
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'size': position_size,
                        'time': current.name,
                        'confidence': signal['confidence']
                    }
        
        # Close any open position at end
        if position:
            final_price = df['close'].iloc[-1]
            if position['side'] == 'LONG':
                pnl_pct = (final_price - position['entry']) / position['entry'] * 100
            else:
                pnl_pct = (position['entry'] - final_price) / final_price * 100
            
            pnl_usd = position['size'] * (pnl_pct / 100) * self.leverage
            self.balance += pnl_usd
            
            self.trades.append({
                'symbol': symbol,
                'side': position['side'],
                'entry': position['entry'],
                'exit': final_price,
                'entry_time': position['time'],
                'exit_time': df.index[-1],
                'pnl_pct': pnl_pct,
                'pnl_usd': pnl_usd,
                'reason': 'END_OF_DATA',
                'confidence': position['confidence']
            })
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        if not self.trades:
            print("\nNo trades executed during backtest period")
            return None
        
        trades_df = pd.DataFrame(self.trades)
        
        wins = len(trades_df[trades_df['pnl_usd'] > 0])
        losses = len(trades_df[trades_df['pnl_usd'] <= 0])
        total = len(trades_df)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        avg_win = trades_df[trades_df['pnl_usd'] > 0]['pnl_usd'].mean() if wins > 0 else 0
        avg_loss = trades_df[trades_df['pnl_usd'] <= 0]['pnl_usd'].mean() if losses > 0 else 0
        
        total_pnl = trades_df['pnl_usd'].sum()
        total_return = (total_pnl / self.initial_balance) * 100
        
        # Calculate max drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        if len(equity_df) > 0:
            equity_df['peak'] = equity_df['balance'].cummax()
            equity_df['drawdown'] = (equity_df['balance'] - equity_df['peak']) / equity_df['peak'] * 100
            max_drawdown = equity_df['drawdown'].min()
        else:
            max_drawdown = 0
        
        # Profit factor
        gross_profit = trades_df[trades_df['pnl_usd'] > 0]['pnl_usd'].sum()
        gross_loss = abs(trades_df[trades_df['pnl_usd'] <= 0]['pnl_usd'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        print(f"\n{'='*70}")
        print("BACKTEST RESULTS")
        print('='*70)
        print(f"Total Trades:     {total}")
        print(f"Win Rate:         {win_rate:.1f}% ({wins}W / {losses}L)")
        print(f"Total P&L:        ${total_pnl:.2f} ({total_return:+.2f}%)")
        print(f"Starting Balance: ${self.initial_balance:.2f}")
        print(f"Final Balance:    ${self.balance:.2f}")
        print(f"Average Win:      ${avg_win:.2f}")
        print(f"Average Loss:     ${avg_loss:.2f}")
        print(f"Max Drawdown:     {max_drawdown:.2f}%")
        print(f"Profit Factor:    {profit_factor:.2f}")
        
        print(f"\n--- Recent Trades ---")
        print(trades_df.tail(10)[['side', 'entry', 'exit', 'pnl_usd', 'reason']].to_string())
        
        return {
            'total_trades': total,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'trades': trades_df
        }


def compare_strategies(symbol='BTC/USDT:USDT', timeframe='1h', limit=500):
    """Compare all strategies on the same data"""
    
    print(f"\n{'#'*70}")
    print(f"STRATEGY COMPARISON: {symbol}")
    print(f"{'#'*70}")
    
    backtester = MultiStrategyBacktester(initial_balance=100.0, leverage=3)
    
    strategies = ['trend_following', 'mean_reversion', 'breakout', 'orb']
    results = {}
    
    for strategy in strategies:
        try:
            result = backtester.run_backtest(
                symbol=symbol,
                strategy_name=strategy,
                timeframe=timeframe,
                limit=limit,
                min_confidence=70,
                risk_per_trade=0.02
            )
            if result:
                results[strategy] = result
        except Exception as e:
            print(f"Error testing {strategy}: {e}")
    
    # Summary table
    if results:
        print(f"\n{'='*70}")
        print("STRATEGY COMPARISON SUMMARY")
        print('='*70)
        print(f"{'Strategy':<20} {'Trades':<8} {'Win Rate':<10} {'Total P&L':<12} {'Max DD':<10}")
        print('-'*70)
        for name, result in results.items():
            print(f"{name:<20} {result['total_trades']:<8} {result['win_rate']:>7.1f}%   ${result['total_pnl']:>+8.2f}   {result['max_drawdown']:>7.1f}%")
        
        # Best strategy
        best = max(results.items(), key=lambda x: x[1]['total_pnl'])
        print(f"\nBest Strategy: {best[0]} with ${best[1]['total_pnl']:+.2f} P&L")
    
    return results


if __name__ == "__main__":
    import sys
    
    print("Multi-Strategy Backtester for Bybit Futures")
    print("="*70)
    
    # Default run
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT:USDT'
    strategy = sys.argv[2] if len(sys.argv) > 2 else 'compare'
    
    if strategy == 'compare':
        compare_strategies(symbol)
    else:
        backtester = MultiStrategyBacktester(initial_balance=100.0, leverage=3)
        backtester.run_backtest(
            symbol=symbol,
            strategy_name=strategy,
            timeframe='1h',
            limit=500,
            min_confidence=70,
            risk_per_trade=0.02
        )
        
    print("\nDone!")
