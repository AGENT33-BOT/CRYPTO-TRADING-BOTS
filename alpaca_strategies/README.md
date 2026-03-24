# Alpaca Multi-Strategy Trading System

A comprehensive algorithmic trading system with 25+ strategies for Alpaca paper trading.

## Features

### Trend Following Strategies (6)
- **MA Crossover** - Simple/Exponential Moving Average crossovers
- **EMA Crossover** - Fast/Slow EMA crossover
- **MACD Trend** - MACD histogram and signal line
- **Supertrend** - ATR-based trend indicator
- **ATR Trend** - Volatility-based trend detection
- **ADX Trend** - Trend strength with DI crossover

### Mean Reversion Strategies (5)
- **RSI Mean Reversion** - Relative Strength Index oversold/overbought
- **Bollinger Bands Mean Reversion** - BB extreme reversals
- **VWAP Reversion** - Volume-weighted average price mean reversion
- **Z-Score Reversion** - Statistical mean reversion
- **Stochastic Reversion** - Stochastic oscillator reversal

### Breakout/Momentum Strategies (4)
- **Breakout Retest** - Breakout with retest confirmation
- **Volatility Squeeze** - Bollinger Bands + Keltner Channel squeeze
- **Range Breakout** - Range breakout with volume confirmation
- **Momentum Ignition** - Momentum burst detection

### Grid/DCA Strategies (2)
- **Grid Trading** - Price grid orders
- **DCA Scaling** - Dollar cost averaging with position scaling

### Statistical Arbitrage (5)
- **Pairs Trading** - Cointegration-based pair trading
- **Statistical Arbitrage** - Multi-stock residual analysis
- **Market Making** - Spread capture with limit orders
- **Sector Rotation** - Momentum-based sector allocation
- **Portfolio Rebalancer** - Target weight maintenance

### Portfolio Management (3)
- **Risk Parity** - Inverse volatility allocation
- (Additional portfolio strategies included)

## Installation

```bash
cd alpaca_strategies
pip install -r requirements.txt
```

## Configuration

1. Set your Alpaca API credentials in environment variables:
```bash
set ALPACA_API_KEY=your_key
set ALPACA_SECRET_KEY=your_secret
```

Or create a `.env` file in the parent directory.

2. Configure strategies in `alpaca_config.py`:
- Enable/disable strategies
- Set symbols, timeframes, parameters
- Adjust risk management settings

## Usage

### Run All Strategies
```bash
python alpaca_strategy_manager.py all
```

### Run Specific Strategy
```bash
python alpaca_strategy_manager.py ema_crossover
python alpaca_strategy_manager.py rsi_mean_reversion
python alpaca_strategy_manager.py pairs_trading
```

### Backtest Strategies
```bash
python alpaca_backtester.py
```

## Strategy Configuration

Each strategy has its own configuration in `alpaca_config.py`:

```python
STRATEGY_CONFIGS = {
    'ema_crossover': {
        'enabled': True,
        'symbols': ['SPY', 'QQQ', 'AAPL'],
        'timeframe': '1h',
        'fast_ema': 9,
        'slow_ema': 21,
        'position_size': 1000,
    },
    # ... more strategies
}
```

## Risk Management

- **Position Sizing**: Max 10% per position
- **Stop Losses**: Automatic 2% default stops
- **Take Profits**: Automatic 4% default targets
- **Max Positions**: Configurable per strategy
- **Risk Per Trade**: Default 1% of equity

## File Structure

```
alpaca_strategies/
├── alpaca_base_strategy.py      # Base class for all strategies
├── alpaca_config.py              # Configuration settings
├── alpaca_strategy_manager.py    # Main strategy controller
├── alpaca_backtester.py          # Backtesting engine
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── strategies/
    ├── ma_crossover_strategy.py
    ├── ema_crossover_strategy.py
    ├── macd_trend_strategy.py
    ├── supertrend_strategy.py
    ├── atr_trend_strategy.py
    ├── adx_trend_strategy.py
    ├── rsi_mean_reversion.py
    ├── bb_mean_reversion.py
    ├── vwap_reversion.py
    ├── zscore_reversion.py
    ├── stochastic_reversion.py
    ├── breakout_retest_strategy.py
    ├── volatility_squeeze.py
    ├── range_breakout_volume.py
    ├── momentum_ignition.py
    ├── grid_trading_strategy.py
    ├── dca_scaling_strategy.py
    ├── pairs_trading.py
    ├── statistical_arbitrage.py
    ├── market_making.py
    ├── sector_rotation.py
    ├── portfolio_rebalancer.py
    └── risk_parity.py
```

## Paper Trading

All strategies default to Alpaca's paper trading environment. Set `paper=True` in the base strategy when ready for live trading.

## Logging

Strategies log to both console and `strategy_manager.log` file.

## Disclaimer

This is for educational purposes. Always test strategies thoroughly in paper trading before using real money. Past performance does not guarantee future results.
