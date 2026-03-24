"""
Alpaca Strategy Status Checker
Quick status overview of all strategies
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alpaca_config import STRATEGY_CONFIGS

def print_strategy_status():
    """Print status of all strategies"""
    
    print("=" * 80)
    print("              ALPACA MULTI-STRATEGY TRADING SYSTEM")
    print("                        Status Overview")
    print("=" * 80)
    print()
    
    categories = {
        'Trend Following': ['ma_crossover', 'ema_crossover', 'macd_trend', 'supertrend', 'atr_trend', 'adx_trend'],
        'Mean Reversion': ['rsi_mean_reversion', 'bb_mean_reversion', 'vwap_reversion', 'zscore_reversion', 'stochastic_reversion'],
        'Breakout/Momentum': ['breakout_retest', 'volatility_squeeze', 'range_breakout', 'momentum_ignition'],
        'Grid/DCA': ['grid_trading', 'dca_scaling'],
        'Statistical Arbitrage': ['pairs_trading', 'statistical_arbitrage', 'market_making', 'sector_rotation'],
        'Portfolio Management': ['portfolio_rebalancer', 'risk_parity'],
    }
    
    total_enabled = 0
    total_disabled = 0
    
    for category, strategies in categories.items():
        print(f"\n[>>] {category}")
        print("-" * 80)
        
        for strategy_name in strategies:
            if strategy_name in STRATEGY_CONFIGS:
                config = STRATEGY_CONFIGS[strategy_name]
                enabled = config.get('enabled', True)
                symbols = config.get('symbols', config.get('pairs', config.get('universe', [])))
                symbol_count = len(symbols)
                
                status = "[ON] ENABLED" if enabled else "[OFF] DISABLED"
                symbol_str = f"({symbol_count} symbols)"
                
                print(f"  {status:12} {strategy_name:25} {symbol_str}")
                
                if enabled:
                    total_enabled += 1
                else:
                    total_disabled += 1
    
    print("\n" + "=" * 80)
    print(f"Summary: {total_enabled} strategies enabled, {total_disabled} disabled")
    print("=" * 80)
    print()
    print("Quick Commands:")
    print("  python alpaca_strategy_manager.py all          # Run all enabled strategies")
    print("  python alpaca_strategy_manager.py ema_crossover # Run specific strategy")
    print("  python alpaca_backtester.py                    # Backtest all strategies")
    print()

if __name__ == '__main__':
    print_strategy_status()
