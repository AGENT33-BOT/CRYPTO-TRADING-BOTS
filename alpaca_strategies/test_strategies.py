"""
Alpaca Strategy Test Runner
Tests all strategies without requiring Alpaca API connection
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategies'))

from alpaca_config import STRATEGY_CONFIGS
import importlib
import traceback


def test_strategy_load(name: str, config: dict) -> dict:
    """Test loading a single strategy"""
    
    strategy_map = {
        'ma_crossover': ('ma_crossover_strategy', 'MACrossoverStrategy'),
        'ema_crossover': ('ema_crossover_strategy', 'EMACrossoverStrategy'),
        'macd_trend': ('macd_trend_strategy', 'MACDTrendStrategy'),
        'supertrend': ('supertrend_strategy', 'SupertrendStrategy'),
        'atr_trend': ('atr_trend_strategy', 'ATRTrendStrategy'),
        'adx_trend': ('adx_trend_strategy', 'ADXTrendStrategy'),
        'rsi_mean_reversion': ('rsi_mean_reversion', 'RSIMeanReversionStrategy'),
        'bb_mean_reversion': ('bb_mean_reversion', 'BBMeanReversionStrategy'),
        'vwap_reversion': ('vwap_reversion', 'VWAPReversionStrategy'),
        'zscore_reversion': ('zscore_reversion', 'ZScoreReversionStrategy'),
        'stochastic_reversion': ('stochastic_reversion', 'StochasticReversionStrategy'),
        'breakout_retest': ('breakout_retest_strategy', 'BreakoutRetestStrategy'),
        'volatility_squeeze': ('volatility_squeeze', 'VolatilitySqueezeStrategy'),
        'range_breakout': ('range_breakout_volume', 'RangeBreakoutVolumeStrategy'),
        'momentum_ignition': ('momentum_ignition', 'MomentumIgnitionStrategy'),
        'grid_trading': ('grid_trading_strategy', 'GridTradingStrategy'),
        'dca_scaling': ('dca_scaling_strategy', 'DCAScalingStrategy'),
        'pairs_trading': ('pairs_trading', 'PairsTradingStrategy'),
        'statistical_arbitrage': ('statistical_arbitrage', 'StatisticalArbitrageStrategy'),
        'market_making': ('market_making', 'MarketMakingStrategy'),
        'sector_rotation': ('sector_rotation', 'SectorRotationStrategy'),
        'portfolio_rebalancer': ('portfolio_rebalancer', 'PortfolioRebalancerStrategy'),
        'risk_parity': ('risk_parity', 'RiskParityStrategy'),
    }
    
    if name not in strategy_map:
        return {'status': 'NOT_FOUND', 'error': 'Strategy not in map'}
    
    module_name, class_name = strategy_map[name]
    
    try:
        # Try to import
        module = importlib.import_module(module_name)
        strategy_class = getattr(module, class_name)
        
        # Try to instantiate
        try:
            strategy = strategy_class(config)
            return {
                'status': 'OK',
                'name': strategy.name if hasattr(strategy, 'name') else name,
                'enabled': strategy.enabled if hasattr(strategy, 'enabled') else True,
                'method': 'config_dict'
            }
        except TypeError:
            # Try with parameter extraction
            symbols = config.get('symbols', [])
            timeframe = config.get('timeframe', '1d')
            
            strategy_kwargs = {
                'symbols': symbols,
                'timeframe': timeframe,
            }
            
            if name == 'ema_crossover':
                strategy_kwargs['fast_ema'] = config.get('fast_ema', 9)
                strategy_kwargs['slow_ema'] = config.get('slow_ema', 21)
            elif name == 'ma_crossover':
                strategy_kwargs['fast_period'] = config.get('fast_period', 20)
                strategy_kwargs['slow_period'] = config.get('slow_period', 50)
                strategy_kwargs['ma_type'] = config.get('ma_type', 'sma')
            elif name == 'macd_trend':
                strategy_kwargs['fast_period'] = config.get('fast_period', 12)
                strategy_kwargs['slow_period'] = config.get('slow_period', 26)
            elif name == 'rsi_mean_reversion':
                strategy_kwargs['rsi_period'] = config.get('rsi_period', 14)
                strategy_kwargs['oversold'] = config.get('rsi_oversold', 30)
                strategy_kwargs['overbought'] = config.get('rsi_overbought', 70)
            elif name == 'supertrend':
                strategy_kwargs['atr_period'] = config.get('atr_period', 10)
                strategy_kwargs['multiplier'] = config.get('multiplier', 3.0)
            elif name == 'pairs_trading':
                strategy_kwargs['pairs'] = config.get('pairs', [])
            elif name == 'grid_trading':
                strategy_kwargs['grid_levels'] = config.get('grid_levels', 5)
                strategy_kwargs['grid_range_pct'] = config.get('grid_range_pct', 0.1)
            
            strategy = strategy_class(**strategy_kwargs)
            return {
                'status': 'OK',
                'name': strategy.name if hasattr(strategy, 'name') else name,
                'enabled': strategy.enabled if hasattr(strategy, 'enabled') else True,
                'method': 'params'
            }
            
    except ImportError as e:
        return {'status': 'IMPORT_ERROR', 'error': str(e)}
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e), 'trace': traceback.format_exc()}


def run_all_tests():
    """Run tests for all enabled strategies"""
    
    print("=" * 80)
    print("           ALPACA STRATEGY TEST - AGENT ALPACA")
    print("              Testing All Strategy Configurations")
    print("=" * 80)
    print()
    
    categories = {
        'TREND FOLLOWING (6)': ['ma_crossover', 'ema_crossover', 'macd_trend', 'supertrend', 'atr_trend', 'adx_trend'],
        'MEAN REVERSION (5)': ['rsi_mean_reversion', 'bb_mean_reversion', 'vwap_reversion', 'zscore_reversion', 'stochastic_reversion'],
        'BREAKOUT/MOMENTUM (4)': ['breakout_retest', 'volatility_squeeze', 'range_breakout', 'momentum_ignition'],
        'GRID/DCA (2)': ['grid_trading', 'dca_scaling'],
        'STATISTICAL ARBITRAGE (4)': ['pairs_trading', 'statistical_arbitrage', 'market_making', 'sector_rotation'],
        'PORTFOLIO MANAGEMENT (2)': ['portfolio_rebalancer', 'risk_parity'],
    }
    
    total_passed = 0
    total_failed = 0
    total_disabled = 0
    
    for category, strategies in categories.items():
        print(f"\n[>>] {category}")
        print("-" * 80)
        
        for strat_name in strategies:
            if strat_name not in STRATEGY_CONFIGS:
                print(f"  [MISSING] {strat_name:30} - Not in config")
                total_failed += 1
                continue
            
            config = STRATEGY_CONFIGS[strat_name]
            
            if not config.get('enabled', True):
                print(f"  [DISABLED] {strat_name:30} - Skipped")
                total_disabled += 1
                continue
            
            result = test_strategy_load(strat_name, config)
            
            if result['status'] == 'OK':
                method = result.get('method', 'unknown')
                print(f"  [PASS] {strat_name:30} - Loaded ({method})")
                total_passed += 1
            else:
                print(f"  [FAIL] {strat_name:30} - {result['status']}: {result.get('error', 'Unknown')}")
                total_failed += 1
    
    print("\n" + "=" * 80)
    print("                      TEST SUMMARY")
    print("=" * 80)
    print(f"  Passed:   {total_passed}")
    print(f"  Failed:   {total_failed}")
    print(f"  Disabled: {total_disabled}")
    print(f"  Total:    {total_passed + total_failed + total_disabled}")
    print("=" * 80)
    
    if total_failed == 0:
        print("\n[OK] All enabled strategies loaded successfully!")
        print("\nAgent Alpaca is ready. To activate strategies:")
        print("  1. Install Alpaca packages: pip install alpaca-py")
        print("  2. Ensure API keys are in .alpaca_env file")
        print("  3. Run: python alpaca_strategy_manager.py all")
    else:
        print(f"\n[WARNING] {total_failed} strategies failed to load")
    
    print()
    return total_failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
