# Run Backtest then Start Trendline Trader
import ccxt
import pandas as pd
from backtest import TrendlineBacktester
from trendline_trader import TrendlineTrader
import time

# API Credentials
API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

def fetch_historical_data(symbol='BTC/USDT', timeframe='4h', limit=500):
    """Fetch historical OHLCV data for backtesting"""
    print(f"Fetching {limit} candles of {symbol} {timeframe} data...")
    
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        print(f"Fetched {len(df)} candles")
        print(f"Date range: {pd.to_datetime(df['timestamp'].iloc[0], unit='ms')} to {pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')}")
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def run_backtest():
    """Run trendline strategy backtest"""
    print("\n" + "="*70)
    print("RUNNING TRENDLINE STRATEGY BACKTEST")
    print("="*70 + "\n")
    
    # Fetch historical data
    df = fetch_historical_data('BTC/USDT', '4h', 500)
    if df is None:
        print("Failed to fetch data. Exiting.")
        return False
    
    # Run backtest
    backtester = TrendlineBacktester(initial_balance=50.0, risk_per_trade=0.015)
    results = backtester.backtest(df)
    
    if isinstance(results, pd.DataFrame):
        print("\nBacktest completed successfully!")
        print(f"Total return: {results['pnl'].sum():.2f}%")
        return True
    else:
        print(f"\nBacktest results: {results}")
        return True

def start_trader():
    """Start the live trendline trader"""
    print("\n" + "="*70)
    print("STARTING LIVE TRENDLINE TRADER")
    print("="*70 + "\n")
    
    trader = TrendlineTrader()
    trader.run()

if __name__ == "__main__":
    # Step 1: Run backtest
    success = run_backtest()
    
    if success:
        print("\n[OK] Backtest completed!")
        print("Starting live trader in 5 seconds...")
        print("Press Ctrl+C to cancel if you don't want to start live trading.\n")
        
        try:
            time.sleep(5)
            # Step 2: Start live trader
            start_trader()
        except KeyboardInterrupt:
            print("\n\nLive trading cancelled by user.")
    else:
        print("\n[X] Backtest failed. Not starting live trader.")
