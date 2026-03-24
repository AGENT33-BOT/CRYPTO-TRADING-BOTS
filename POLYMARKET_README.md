# Polymarket Trading Bot System

## Overview
Complete prediction market trading system for Polymarket - trade on real-world event outcomes.

## What is Polymarket?
Polymarket is a decentralized prediction market where you trade on the outcome of real-world events. Prices represent the crowd's estimate of probability.

## Features

### 🤖 Trading Bot (`polymarket_trader.py`)
- Scans all active prediction markets
- Filters for crypto-related events
- Analyzes market sentiment and pricing
- Identifies trading opportunities
- Tracks positions and P&L

### 📊 Strategies (`polymarket_strategies.py`)
1. **Extreme Sentiment** - Trade against crowd extremes (>90%, <10%)
2. **Time Decay** - Scalp as resolution approaches
3. **News Events** - Trade ETF approvals, Fed decisions, etc.
4. **Arbitrage** - Find pricing inconsistencies
5. **Kelly Criterion** - Optimal bet sizing
6. **Portfolio Allocation** - Diversification

## Installation

```bash
# Install dependencies
pip install requests

# No API key needed for read-only mode
# For trading, get API key from Polymarket
```

## Usage

### 1. Market Scanner (Read-Only)
```bash
python polymarket_trader.py
```
Shows all opportunities without placing trades.

### 2. Continuous Monitoring
```python
from polymarket_trader import PolymarketTrader

trader = PolymarketTrader()
trader.run_continuous(interval=60)  # Scan every minute
```

### 3. Use Strategies
```python
from polymarket_strategies import PolymarketStrategies

# Get contrarian signal
signal = PolymarketStrategies.extreme_sentiment_strategy(market)

# Calculate bet size
bet = PolymarketStrategies.kelly_criterion_sizing(
    probability=0.6,
    odds=2.0,
    bankroll=1000
)
```

## Trading Strategies

### Strategy 1: Contrarian Extremes
When crowd is >90% confident, bet the opposite direction.
- Works because crowds overreact at extremes
- High win rate when probability <10% or >90%

### Strategy 2: Event-Driven
Trade before major announcements:
- ETF approvals
- Fed rate decisions
- Regulatory news
- Exchange listings

### Strategy 3: Time Decay Scalping
As resolution approaches, prices converge to 0 or 1.
- Scalp middle-range prices (40-60%) in final days
- Quick in-and-out trades

## Example Markets to Trade

### Crypto
- "Will Bitcoin hit $70k by March 2026?"
- "Will Ethereum ETF be approved?"
- "Will SOL flip ADA in market cap?"

### Macro
- "Will Fed raise rates in March?"
- "Will inflation drop below 3%?"

### Politics
- "Will Trump win 2026 election?"
- "Will specific bill pass?"

## Risk Management

### Position Sizing
- Max 2% per position (diversification)
- Half-Kelly criterion for optimal sizing
- Never bet more than 5% on single event

### Exit Rules
- Take profits at 50% gain
- Cut losses at 25% loss
- Close before resolution if uncertain

## Differences from Crypto Trading

| Aspect | Crypto (Bybit) | Polymarket |
|--------|---------------|------------|
| Asset | BTC/ETH/ALT | Event outcomes (YES/NO) |
| Price | Market price | Probability (0-1) |
| Leverage | 3x-100x | 1x (no leverage) |
| Outcome | Continuous | Binary (win/lose) |
| Edge | Technical analysis | Information/sentiment |
| Returns | Unlimited | Capped at 1x (100%) |

## API Endpoints

- **Gamma API**: Market discovery
  - `https://gamma-api.polymarket.com/markets`
  
- **CLOB API**: Orderbook & trading
  - `https://clob.polymarket.com/book`

## Files

- `polymarket_trader.py` - Main trading bot
- `polymarket_strategies.py` - Strategy library
- `POLYMARKET_IDEAS.md` - Integration ideas with Bybit

## Next Steps

1. Test scanner in read-only mode
2. Identify which strategy works best
3. Paper trade with small amounts
4. Scale up successful strategies

## Disclaimer

Prediction markets involve risk. Only trade what you can afford to lose. Past performance doesn't guarantee future results.
