"""
Alpaca Strategy Manager
Main controller for running all strategies
"""
import sys
import os
import json
import importlib
from datetime import datetime
from typing import Dict, List
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategies'))

from alpaca_config import STRATEGY_CONFIGS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StrategyManager')


class StrategyManager:
    """Manages multiple trading strategies"""
    
    def __init__(self):
        self.strategies = {}
        self.results = {}
        
    def load_strategy(self, name: str, config: dict):
        """Dynamically load a strategy class"""
        try:
            # Map strategy names to module/class names
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
                logger.error(f"Unknown strategy: {name}")
                return None
            
            module_name, class_name = strategy_map[name]
            
            # Import module
            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                logger.error(f"Could not import module {module_name}: {e}")
                return None
            
            # Get class
            strategy_class = getattr(module, class_name)
            
            # Instantiate with config dict (new style)
            try:
                strategy = strategy_class(config)
                logger.info(f"Loaded strategy: {name} (config dict style)")
            except TypeError as e:
                # Try old style with individual params
                logger.warning(f"Config dict style failed for {name}, trying parameter style: {e}")
                
                # Extract parameters from config
                symbols = config.get('symbols', [])
                timeframe = config.get('timeframe', '1d')
                
                # Create strategy with extracted params
                strategy_kwargs = {
                    'symbols': symbols,
                    'timeframe': timeframe,
                }
                
                # Add strategy-specific params
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
                logger.info(f"Loaded strategy: {name} (parameter style)")
            
            self.strategies[name] = strategy
            return strategy
            
        except Exception as e:
            logger.error(f"Error loading strategy {name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_strategy(self, name: str):
        """Run a single strategy"""
        if name not in self.strategies:
            logger.error(f"Strategy not loaded: {name}")
            return
        
        try:
            logger.info(f"Running strategy: {name}")
            strategy = self.strategies[name]
            
            # Run the strategy
            result = strategy.run()
            
            # Record results
            self.results[name] = {
                'signals': len(strategy.signals) if hasattr(strategy, 'signals') else 0,
                'timestamp': datetime.now().isoformat(),
                'enabled': strategy.enabled if hasattr(strategy, 'enabled') else False
            }
            
            logger.info(f"Strategy {name} completed")
            
        except Exception as e:
            logger.error(f"Error running strategy {name}: {e}")
            import traceback
            traceback.print_exc()
            self.results[name] = {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all(self):
        """Run all enabled strategies"""
        logger.info("=" * 70)
        logger.info("Starting Strategy Manager - Running All Strategies")
        logger.info("=" * 70)
        
        for name in STRATEGY_CONFIGS.keys():
            config = STRATEGY_CONFIGS[name]
            
            if not config.get('enabled', True):
                logger.info(f"Skipping disabled strategy: {name}")
                continue
            
            # Load and run
            strategy = self.load_strategy(name, config)
            if strategy:
                self.run_strategy(name)
        
        logger.info("=" * 70)
        logger.info("Strategy Manager Complete")
        logger.info(f"Results: {json.dumps(self.results, indent=2, default=str)}")
        logger.info("=" * 70)
    
    def run_specific(self, name: str):
        """Run a specific strategy"""
        if name not in STRATEGY_CONFIGS:
            logger.error(f"Strategy not found in config: {name}")
            return
        
        config = STRATEGY_CONFIGS[name]
        strategy = self.load_strategy(name, config)
        if strategy:
            self.run_strategy(name)
    
    def get_status(self) -> dict:
        """Get status of all strategies"""
        return {
            'loaded': list(self.strategies.keys()),
            'results': self.results
        }


def main():
    manager = StrategyManager()
    
    if len(sys.argv) > 1:
        strategy_name = sys.argv[1]
        if strategy_name == 'all':
            manager.run_all()
        else:
            manager.run_specific(strategy_name)
    else:
        print("=" * 70)
        print("              ALPACA MULTI-STRATEGY TRADING SYSTEM")
        print("=" * 70)
        print()
        print("Usage: python alpaca_strategy_manager.py [strategy_name|all]")
        print()
        print("Available strategies:")
        
        # Group by category
        categories = {
            'Trend Following': ['ma_crossover', 'ema_crossover', 'macd_trend', 'supertrend', 'atr_trend', 'adx_trend'],
            'Mean Reversion': ['rsi_mean_reversion', 'bb_mean_reversion', 'vwap_reversion', 'zscore_reversion', 'stochastic_reversion'],
            'Breakout/Momentum': ['breakout_retest', 'volatility_squeeze', 'range_breakout', 'momentum_ignition'],
            'Grid/DCA': ['grid_trading', 'dca_scaling'],
            'Statistical Arbitrage': ['pairs_trading', 'statistical_arbitrage', 'market_making', 'sector_rotation'],
            'Portfolio Management': ['portfolio_rebalancer', 'risk_parity'],
        }
        
        for category, strategies in categories.items():
            print(f"\n  [>>] {category}")
            for strat_name in strategies:
                if strat_name in STRATEGY_CONFIGS:
                    enabled = STRATEGY_CONFIGS[strat_name].get('enabled', True)
                    status = "[ON]" if enabled else "[OFF]"
                    print(f"      {status} {strat_name}")
        
        print("\n" + "=" * 70)
        print("Examples:")
        print("  python alpaca_strategy_manager.py all")
        print("  python alpaca_strategy_manager.py ema_crossover")
        print("  python alpaca_strategy_manager.py rsi_mean_reversion")
        print("=" * 70)


if __name__ == '__main__':
    main()
