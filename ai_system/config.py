"""
AI Trading System Configuration
"""

# Trading Configuration
TRADING_CONFIG = {
    # Symbols to trade
    'symbols': [
        'BTCUSDT',
        'ETHUSDT',
        'SOLUSDT',
        'BNBUSDT',
        'NEARUSDT',
        'LINKUSDT',
        'DOGEUSDT',
        'XRPUSDT',
    ],
    
    # Minimum confidence for trade (0-100)
    'min_confidence': 60,
    
    # Position sizing
    'default_position_size': 10,  # % of portfolio
    'max_position_size': 20,
    
    # TP/SL (overridden by volatility adapter)
    'default_tp': 2.5,  # %
    'default_sl': 2.5,  # %
    'trailing_stop': 1.0,  # %
    
    # Trading hours (UTC)
    'trading_start': 0,  # Hour
    'trading_end': 23,   # Hour
    
    # Risk Management
    'max_daily_loss': 5,  # %
    'max_positions': 3,
    'emergency_stop_loss': 10,  # %
    
    # Analysis intervals
    'analysis_interval': 60,  # seconds
    'data_refresh_interval': 300,  # seconds
    
    # ML Configuration
    'ml_model_path': 'ml_model.json',
    'ml_training_data_required': 100,
    
    # Sentiment
    'sentiment_cache_duration': 300,  # seconds
    
    # Logging
    'log_level': 'INFO',
}

# API Configuration
API_CONFIG = {
    'bybit': {
        'api_key': 'KfmiIdWd16hG18v2O7',
        'api_secret': 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ',
        'testnet': False,
    }
}
