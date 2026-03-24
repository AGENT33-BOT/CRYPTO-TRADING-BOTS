"""
Parallel Strategy Runner for Agent Alpaca
Runs all 23 strategies continuously in separate processes
"""
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# All 23 strategies
STRATEGIES = [
    # Trend Following (6)
    'ma_crossover', 'ema_crossover', 'macd_trend', 'supertrend', 'atr_trend', 'adx_trend',
    # Mean Reversion (5)
    'rsi_mean_reversion', 'bb_mean_reversion', 'vwap_reversion', 'zscore_reversion', 'stochastic_reversion',
    # Breakout/Momentum (4)
    'breakout_retest', 'volatility_squeeze', 'range_breakout', 'momentum_ignition',
    # Grid/DCA (2)
    'grid_trading', 'dca_scaling',
    # Statistical Arbitrage (4)
    'pairs_trading', 'statistical_arbitrage', 'market_making', 'sector_rotation',
    # Portfolio Management (2)
    'portfolio_rebalancer', 'risk_parity',
]

processes = []

def signal_handler(sig, frame):
    print("\nShutting down all strategies...")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_strategy_loop(strategy_name):
    """Run a strategy in a continuous loop"""
    script_dir = Path(__file__).parent
    while True:
        try:
            result = subprocess.run(
                [sys.executable, 'alpaca_strategy_manager.py', strategy_name],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per run
            )
            if result.returncode != 0:
                print(f"[{strategy_name}] Error: {result.stderr[-500:]}")
        except subprocess.TimeoutExpired:
            print(f"[{strategy_name}] Timeout - restarting...")
        except Exception as e:
            print(f"[{strategy_name}] Exception: {e}")
        
        # Sleep before next run (5 minutes)
        time.sleep(300)

def start_all_strategies():
    """Start all strategies in parallel processes"""
    print("=" * 70)
    print("AGENT ALPACA - Starting All 23 Strategies")
    print("=" * 70)
    
    for strategy in STRATEGIES:
        print(f"Starting: {strategy}")
        p = subprocess.Popen(
            [sys.executable, '-c', 
             f'from parallel_runner import run_strategy_loop; run_strategy_loop("{strategy}")'],
            cwd=Path(__file__).parent,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        processes.append(p)
        time.sleep(0.5)  # Small delay between starts
    
    print(f"\nAll {len(STRATEGIES)} strategies started!")
    print("Press Ctrl+C to stop all strategies\n")
    
    # Monitor processes
    try:
        while True:
            time.sleep(10)
            running = sum(1 for p in processes if p.poll() is None)
            print(f"[{time.strftime('%H:%M:%S')}] {running}/{len(processes)} strategies running")
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == '__main__':
    start_all_strategies()
