# Bybit Trading Strategies - Quick Reference

## Strategy Comparison

| Strategy | Market Condition | Risk Level | Profit Potential | Timeframe | Best For |
|----------|-----------------|------------|------------------|-----------|----------|
| **Mean Reversion** | Oversold/Overbought | Medium | High | 5m | Counter-trend trades |
| **Momentum** | Trending | Medium | High | 5m | Following trends |
| **Scalping** | Any (quick moves) | High | Medium | 1m | Fast execution |
| **Grid Trading** | Sideways/Range | Low-Medium | Medium | 1h/4h | Passive income |
| **Funding Arbitrage** | Any (delta neutral) | Low | Low-Medium | 8h | Passive income |
| **Trendline** | Trending/Swing | Medium | High | 5m/15m | Active markets |

---

## 1. Mean Reversion (`mean_reversion_trader.py`)

### How It Works
- **Long**: Price touches lower Bollinger Band + RSI oversold (<35)
- **Short**: Price touches upper Bollinger Band + RSI overbought (>65)
- Profits from price returning to mean (middle BB)
- Counter-trend strategy

### Configuration
```python
CONFIG = {
    'symbols': ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...],
    'timeframe': '5m',
    'leverage': 3,
    'position_size': 10,      # USDT per trade
    'max_positions': 3,
    'min_confidence': 75,
    'rsi_oversold': 35,       # Long when RSI < 35
    'rsi_overbought': 65,     # Short when RSI > 65
    'stop_loss_pct': 0.015,   # 1.5% SL
    'take_profit_pct': 0.025, # 2.5% TP
}
```

### When to Use
- After sharp price moves (pumps/dumps)
- RSI shows extreme readings
- Price at Bollinger Band extremes
- Choppy/sideways markets

### Risk
- **Trend continuation**: Can enter too early in strong trends
- **Whipsaws**: False signals near boundaries
- **Requires patience**: Mean reversion takes time

---

## 2. Momentum (`momentum_trader.py`)

### How It Works
- **Long**: EMA 9 crosses above EMA 21 + RSI > 50 + MACD positive
- **Short**: EMA 9 crosses below EMA 21 + RSI < 50 + MACD negative
- Volume confirmation required (>1.2x average)
- Trend-following strategy

### Configuration
```python
CONFIG = {
    'symbols': ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...],
    'timeframe': '5m',
    'leverage': 3,
    'position_size': 10,
    'max_positions': 2,
    'min_confidence': 75,
    'ema_fast': 9,
    'ema_slow': 21,
    'volume_threshold': 1.2,
    'stop_loss_pct': 0.02,    # 2% SL (wider for momentum)
    'take_profit_pct': 0.04,  # 4% TP
}
```

### When to Use
- Clear trending markets
- After consolidation breakout
- Strong volume surge
- EMA alignment (stacked)

### Risk
- **Late entries**: Can enter near trend exhaustion
- **False breakouts**: Requires confirmation
- **Wider stops**: Needs room to breathe

---

## 3. Scalping (`scalping_bot.py`)

### How It Works
- 1-minute timeframe for quick entries/exits
- RSI extreme reversals (30/70 levels)
- Fast 7-period RSI for responsiveness
- Time-based exits (max 15 min hold)

### Configuration
```python
CONFIG = {
    'symbols': ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...],
    'timeframe': '1m',
    'leverage': 5,            # Higher leverage
    'position_size': 5,       # Smaller size
    'max_positions': 2,
    'min_confidence': 80,     # Higher threshold
    'rsi_period': 7,
    'profit_target': 0.008,   # 0.8% profit
    'stop_loss': 0.005,       # 0.5% stop
    'max_hold_minutes': 15,
}
```

### When to Use
- High volatility periods
- Quick intraday moves
- Tight spreads on major pairs
- When you can monitor actively

### Risk
- **High frequency**: Many small losses can add up
- **Slippage**: Fast moves can affect fills
- **Requires attention**: Needs monitoring
- **Higher leverage**: Magnifies both gains and losses

---

## 4. Grid Trading (`grid_trader.py`)

### How It Works
- Places buy orders at regular intervals below current price
- Places sell orders at regular intervals above current price
- Profits as price oscillates between grid levels
- No directional bias - makes money in sideways markets

### Configuration
```python
CONFIG = {
    'symbol': 'BTC/USDT:USDT',  # Trading pair
    'grid_levels': 10,          # Number of grid lines
    'grid_lower': 65000,        # Lower price bound
    'grid_upper': 75000,        # Upper price bound
    'total_investment': 50,     # USDT to use
    'leverage': 2,
}
```

### When to Use
- Market is trading in a range (sideways)
- High volatility but no clear trend
- You want passive income without directional risk

### Risk
- **Range breakout**: If price breaks above upper or below lower grid, orders stop filling
- **Requires monitoring**: Need to adjust grid if price moves outside range
- **Capital intensive**: Capital is locked in multiple orders

---

## 5. Funding Rate Arbitrage (`funding_arbitrage.py`)

### How It Works
- **Positive funding**: Short perpetual + Long spot = Earn funding payments
- **Negative funding**: Long perpetual + Short spot = Earn funding payments
- Delta neutral (no directional risk)
- Funding paid every 8 hours on Bybit

### Configuration
```python
CONFIG = {
    'min_funding_rate': 0.0001,  # 0.01% minimum to trade
    'max_funding_rate': 0.01,    # Skip if >1%
    'position_size': 20,         # USDT per arbitrage
    'check_interval': 300,       # Check every 5 min
}
```

### When to Use
- Funding rates are consistently high (check before funding times)
- You want market-neutral returns
- Holding positions through funding periods

### Risk
- **Basis risk**: Spot and perp prices can diverge
- **Liquidation**: If using leverage on perp side
- **Negative funding flips**: Rate can change sign
- **Capital requirements**: Needs capital in both spot and futures

### Funding Schedule (Bybit)
- 00:00 UTC
- 08:00 UTC
- 16:00 UTC

**Best entry**: 30-60 minutes before funding time when rates are known

---

## Strategy Selection Guide

### Bullish Trend
1. **Momentum** (primary) - Follow the trend
2. **Scalping** (supplementary) - Quick longs on dips
3. Grid Trading (if range-bound within uptrend)

### Bearish Trend
1. **Momentum** (primary) - Short signals
2. **Mean Reversion** (careful) - Counter-trend bounces
3. Funding Arbitrage (if positive funding)

### Sideways/Range
1. **Mean Reversion** (best) - BB extremes
2. **Grid Trading** (passive) - Set and forget
3. **Scalping** (active) - Range-bound scalps

### High Volatility
1. **Scalping** (quick profits)
2. **Grid Trading** (wider ranges)
3. **Mean Reversion** (extreme moves)

---

## Risk Management Summary

| Strategy | Max Loss per Trade | Recommended Allocation | Time Required |
|----------|-------------------|----------------------|---------------|
| Mean Reversion | $5 (1.5% SL) | 25% of portfolio | Low |
| Momentum | $5 (2% SL) | 25% of portfolio | Low |
| Scalping | $2.5 (0.5% SL) | 15% of portfolio | High |
| Grid Trading | Grid range width | 25% of portfolio | None |
| Funding Arbitrage | Spread + fees | 10% of portfolio | None |

---

## Running Multiple Strategies

### Recommended Combinations

**Conservative (Low Risk)**
- Grid Trading + Funding Arbitrage
- Passive income, minimal monitoring

**Balanced (Medium Risk)**
- Mean Reversion + Momentum + Grid
- Diversified across market conditions

**Aggressive (Higher Risk)**
- All strategies including Scalping
- Requires active monitoring

### Avoid
- Running Mean Reversion + Momentum on same pair (conflicting signals)
- Multiple scalping bots on same pair (overexposure)
- Grid + Mean Reversion overlap (different timeframes okay)

---

## Quick Commands

```bash
# Mean Reversion
cd crypto_trader
python mean_reversion_trader.py

# Momentum
cd crypto_trader
python momentum_trader.py

# Scalping
cd crypto_trader
python scalping_bot.py

# Grid Trading
cd crypto_trader
python grid_trader.py

# Funding Arbitrage
cd crypto_trader
python funding_arbitrage.py

# Backtest a strategy
cd crypto_trader
python backtest_strategies.py BTC/USDT:USDT mean_reversion

# Start all bots
cd crypto_trader
python launch_all.py
```

---

## Backtesting

Test strategies before live trading:

```bash
# Compare all strategies
python backtest_strategies.py BTC/USDT:USDT compare

# Test specific strategy
python backtest_strategies.py ETH/USDT:USDT mean_reversion
python backtest_strategies.py SOL/USDT:USDT momentum
python backtest_strategies.py BTC/USDT:USDT breakout
```

---

*Last updated: 2026-02-11*
