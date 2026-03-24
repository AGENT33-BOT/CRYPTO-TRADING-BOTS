"""
Alpaca Trading Configuration
Loads settings from environment variables and .alpaca_env file
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class AlpacaConfig:
    """Configuration for Alpaca API and trading strategies"""
    
    # API Credentials
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://paper-api.alpaca.markets"  # Paper trading by default
    
    # Trading Settings
    default_position_size: float = 0.1  # 10% of portfolio per position
    max_position_size: float = 0.25  # 25% max per position
    max_total_exposure: float = 1.0  # 100% of portfolio
    
    # Risk Management
    default_stop_loss_pct: float = 0.02  # 2% stop loss
    default_take_profit_pct: float = 0.05  # 5% take profit
    max_daily_loss_pct: float = 0.03  # 3% max daily loss
    max_drawdown_pct: float = 0.15  # 15% max drawdown
    risk_per_trade_pct: float = 0.01  # 1% risk per trade
    
    # Data Settings
    default_timeframe: str = "1D"
    backtest_start_date: str = "2020-01-01"
    backtest_end_date: str = ""
    
    # Strategy Settings
    enabled_strategies: List[str] = field(default_factory=list)
    strategy_configs: Dict = field(default_factory=dict)
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "trading.log"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'AlpacaConfig':
        """Load configuration from environment variables and .env file"""
        config = cls()
        
        # Try to load from .alpaca_env file
        if env_file is None:
            # Look for .alpaca_env in common locations
            possible_paths = [
                Path.cwd() / ".alpaca_env",
                Path.cwd().parent / ".alpaca_env",
                Path(__file__).parent / ".alpaca_env",
                Path(__file__).parent.parent / ".alpaca_env",
                Path.home() / ".alpaca_env",
            ]
            for path in possible_paths:
                if path.exists():
                    env_file = str(path)
                    break
        
        # Load from file if found
        if env_file and Path(env_file).exists():
            with open(env_file, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 2:
                    config.api_key = lines[0].strip()
                    config.api_secret = lines[1].strip()
        
        # Override with environment variables
        config.api_key = os.getenv('ALPACA_API_KEY', config.api_key)
        config.api_secret = os.getenv('ALPACA_API_SECRET', config.api_secret)
        config.base_url = os.getenv('ALPACA_BASE_URL', config.base_url)
        
        # Load numeric settings from env
        config.default_position_size = float(os.getenv('DEFAULT_POSITION_SIZE', config.default_position_size))
        config.max_position_size = float(os.getenv('MAX_POSITION_SIZE', config.max_position_size))
        config.default_stop_loss_pct = float(os.getenv('DEFAULT_STOP_LOSS_PCT', config.default_stop_loss_pct))
        config.default_take_profit_pct = float(os.getenv('DEFAULT_TAKE_PROFIT_PCT', config.default_take_profit_pct))
        
        return config
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret must be provided")
        if self.default_position_size <= 0 or self.default_position_size > 1:
            raise ValueError("Position size must be between 0 and 1")
        return True


# Load credentials from .alpaca_env file
ALPACA_API_KEY = ""
ALPACA_SECRET_KEY = ""

# Try to load from .alpaca_env
env_paths = [
    Path.cwd() / ".alpaca_env",
    Path.cwd().parent / ".alpaca_env",
    Path(__file__).parent / ".alpaca_env",
    Path(__file__).parent.parent / ".alpaca_env",
]

for env_path in env_paths:
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) >= 2:
                    ALPACA_API_KEY = lines[0].strip()
                    ALPACA_SECRET_KEY = lines[1].strip()
                    break
        except Exception:
            pass

# Override with environment variables
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', ALPACA_API_KEY)
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', ALPACA_SECRET_KEY)
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

# Default trading configuration
class TradingConfig:
    def __init__(self):
        self.risk_per_trade_pct = 0.01  # 1% risk per trade
        self.max_position_size_pct = 0.10  # 10% max per position
        self.default_stop_loss_pct = 0.02  # 2% default SL
        self.default_take_profit_pct = 0.04  # 4% default TP

# Default universe of stocks for strategies
DEFAULT_UNIVERSE = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
    'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'UBER', 'ABNB', 'COIN',
    'SQ', 'ROKU', 'ZM', 'PLTR', 'SNOW', 'CRWD', 'NET', 'DDOG',
    'MDB', 'OKTA', 'TWLO', 'FSLY', 'SHOP', 'SPY', 'QQQ', 'IWM',
    'VTI', 'VXUS', 'BND', 'GLD', 'SLV', 'USO'
]

# Sector ETFs for sector rotation
SECTOR_ETFS = {
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLI': 'Industrials',
    'XLP': 'Consumer Staples',
    'XLY': 'Consumer Discretionary',
    'XLB': 'Materials',
    'XLU': 'Utilities',
    'XLV': 'Healthcare',
    'XLRE': 'Real Estate',
    'XLC': 'Communication Services'
}

# Market hours
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Timeframes
TIMEFRAMES = {
    '1Min': '1 minute',
    '5Min': '5 minutes',
    '15Min': '15 minutes',
    '30Min': '30 minutes',
    '1H': '1 hour',
    '4H': '4 hours',
    '1D': '1 day',
    '1W': '1 week',
    '1M': '1 month'
}

# =====================================================
# STRATEGY CONFIGURATION - AGENT ALPACA
# All strategies ENABLED for testing
# =====================================================

STRATEGY_CONFIGS = {
    # =====================================================
    # TREND FOLLOWING STRATEGIES (6)
    # =====================================================
    
    # 1. MA Crossover - Simple Moving Average crossover
    'ma_crossover': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA'],
        'timeframe': '1d',
        'fast_period': 20,
        'slow_period': 50,
        'ma_type': 'sma',
        'position_size': 1000,
    },
    
    # 2. EMA Crossover - Exponential Moving Average crossover
    # NOTE: GLD + SLV removed due to low win rate (36-37%) in backtest
    'ema_crossover': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'],
        'timeframe': '1h',
        'fast_ema': 9,
        'slow_ema': 21,
        'position_size': 1000,
    },
    
    # 3. MACD Trend - MACD histogram and signal line
    'macd_trend': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'COIN'],
        'timeframe': '1d',
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9,
        'position_size': 1000,
    },
    
    # 4. Supertrend - ATR-based trend indicator
    'supertrend': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA'],
        'timeframe': '1d',
        'atr_period': 10,
        'multiplier': 3.0,
        'position_size': 1000,
    },
    
    # 5. ATR Trend - Volatility-based trend detection
    'atr_trend': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD'],
        'timeframe': '1d',
        'atr_period': 14,
        'trend_threshold': 1.5,
        'position_size': 1000,
    },
    
    # 6. ADX Trend - Trend strength with DI crossover
    'adx_trend': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA'],
        'timeframe': '1d',
        'adx_period': 14,
        'adx_threshold': 25,
        'position_size': 1000,
    },
    
    # =====================================================
    # MEAN REVERSION STRATEGIES (4)
    # =====================================================
    
    # 7. RSI Mean Reversion - RSI oversold/overbought
    'rsi_mean_reversion': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'COIN', 'GLD', 'SLV'],
        'timeframe': '1d',
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'position_size': 1000,
    },
    
    # 8. Bollinger Bands Mean Reversion - BB extreme reversals
    'bb_mean_reversion': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'GLD', 'SLV'],
        'timeframe': '1d',
        'bb_period': 20,
        'bb_std': 2.0,
        'position_size': 1000,
    },
    
    # 9. VWAP Reversion - Volume-weighted average price mean reversion
    'vwap_reversion': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA'],
        'timeframe': '1h',
        'vwap_deviation': 0.02,  # 2% deviation from VWAP
        'position_size': 1000,
    },
    
    # 10. Z-Score Reversion - Statistical mean reversion
    'zscore_reversion': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'GLD', 'SLV'],
        'timeframe': '1d',
        'lookback': 20,
        'z_threshold': 2.0,
        'position_size': 1000,
    },
    
    # =====================================================
    # BREAKOUT/MOMENTUM STRATEGIES (4)
    # =====================================================
    
    # 11. Breakout Retest - Breakout with retest confirmation
    'breakout_retest': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'COIN'],
        'timeframe': '1d',
        'lookback': 20,
        'breakout_threshold': 0.02,  # 2% breakout
        'retest_tolerance': 0.01,
        'position_size': 1000,
    },
    
    # 12. Volatility Squeeze - Bollinger + Keltner squeeze
    'volatility_squeeze': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD'],
        'timeframe': '1d',
        'bb_period': 20,
        'bb_std': 2.0,
        'kc_period': 20,
        'kc_atr_mult': 1.5,
        'position_size': 1000,
    },
    
    # 13. Range Breakout - Range breakout with volume
    'range_breakout': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA'],
        'timeframe': '1d',
        'range_period': 20,
        'volume_threshold': 1.5,
        'position_size': 1000,
    },
    
    # 14. Momentum Ignition - Momentum burst detection
    'momentum_ignition': {
        'enabled': True,
        'symbols': ['TSLA', 'NVDA', 'AMD', 'COIN', 'ROKU', 'SQ', 'PLTR'],
        'timeframe': '1d',
        'momentum_period': 10,
        'momentum_threshold': 0.05,
        'position_size': 1000,
    },
    
    # =====================================================
    # GRID/DCA STRATEGIES (2)
    # =====================================================
    
    # 15. Grid Trading - Price grid orders
    'grid_trading': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ'],
        'grid_levels': 5,
        'grid_range_pct': 0.10,
        'investment_per_grid': 500,
    },
    
    # 16. DCA Scaling - Dollar cost averaging with scaling
    'dca_scaling': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'VTI', 'VXUS'],
        'base_investment': 1000,
        'scale_factor': 1.5,
        'max_scales': 3,
        'interval_days': 7,
    },
    
    # =====================================================
    # STATISTICAL ARBITRAGE STRATEGIES (4)
    # =====================================================
    
    # 17. Pairs Trading - Cointegration-based pairs
    # NOTE: GLD/SLV pair removed - 75% win rate but negative returns (-0.31%)
    'pairs_trading': {
        'enabled': True,
        'pairs': [
            ('PEP', 'KO'),      # Pepsi vs Coke
            ('JPM', 'BAC'),     # JPMorgan vs BofA
            ('XOM', 'CVX'),     # Exxon vs Chevron
            ('F', 'GM'),        # Ford vs GM
            ('AAPL', 'MSFT'),   # Apple vs Microsoft
            ('GOOGL', 'META'),  # Google vs Meta
            ('XLF', 'XLK'),     # Financials vs Tech
        ],
        'timeframe': '1d',
        'lookback': 60,
        'z_threshold': 2.0,
        'position_size': 1000,
    },
    
    # 18. Statistical Arbitrage - Multi-stock residual analysis
    'statistical_arbitrage': {
        'enabled': True,
        'universe': ['SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'XLE', 'XLI', 'XLV'],
        'timeframe': '1d',
        'lookback': 30,
        'z_threshold': 1.5,
        'position_size': 500,
    },
    
    # 19. Market Making - Spread capture with limit orders
    'market_making': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ'],
        'spread_pct': 0.001,
        'position_size': 500,
    },
    
    # 20. Sector Rotation - Momentum-based sector allocation
    'sector_rotation': {
        'enabled': False,  # DISABLED - Losing on IWM small caps
        'sectors': ['XLK', 'XLF', 'XLE', 'XLI', 'XLV', 'XLU', 'XLP', 'XLB', 'XLY'],
        'timeframe': '1d',
        'momentum_lookback': 20,
        'top_n': 3,
        'position_size': 1000,
    },
    
    # =====================================================
    # PORTFOLIO MANAGEMENT STRATEGIES (2)
    # =====================================================
    
    # 21. Portfolio Rebalancer - Target weight maintenance (Index Bot)
    'portfolio_rebalancer': {
        'enabled': False,  # DISABLED - Losing on VTI broad market
        'target_allocation': {
            'SPY': 0.30,
            'QQQ': 0.25,
            'IWM': 0.15,
            'VTI': 0.20,
            'BND': 0.10,
        },
        'rebalance_threshold': 0.05,
    },
    
    # 22. Risk Parity - Inverse volatility allocation
    'risk_parity': {
        'enabled': False,  # DISABLED - Losing on DBC commodities & GLD gold
        'universe': ['SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'DBC'],
        'timeframe': '1d',
        'risk_lookback': 60,
        'target_volatility': 0.10,
    },
    
    # 23. Stochastic Reversion - Additional mean reversion
    'stochastic_reversion': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'GLD', 'SLV'],
        'timeframe': '1d',
        'k_period': 14,
        'd_period': 3,
        'oversold': 20,
        'overbought': 80,
        'position_size': 1000,
    },
}

# Default universal settings
DEFAULT_SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
MARKET_HOURS_ONLY = True
LOG_LEVEL = 'INFO'

# Export for backward compatibility
ENABLED_STRATEGIES = [name for name, config in STRATEGY_CONFIGS.items() if config.get('enabled', True)]
