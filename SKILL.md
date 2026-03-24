# Bybit Trading Skill for OpenClaw

A comprehensive automated trading system for Bybit Futures with multiple strategies, risk management, and monitoring.

## Features

- **Multiple Trading Strategies:**
  - Scalping (RSI + Bollinger Bands)
  - Mean Reversion
  - Momentum Trading
  - Grid Trading

- **Risk Management:**
  - Automatic TP/SL protection
  - Position sizing controls
  - Max drawdown limits
  - Circuit breakers

- **Monitoring & Alerts:**
  - P&L tracking
  - Telegram notifications
  - Bot health checks
  - Cron-scheduled reports

## Installation

```bash
# Clone to your OpenClaw skills directory
cd ~/clawd/skills
git clone https://github.com/YOUR_USERNAME/bybit-trading-skill.git

# Install dependencies
pip install ccxt pandas numpy talib

# Configure API keys
cp .env.example .env
# Edit .env with your Bybit API credentials
```

## Configuration

Create `.env` file:
```
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_secret_here
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Usage

### Start Trading Bots
```bash
python bot_manager.py restart scalping
python bot_manager.py restart mean_reversion
python bot_manager.py restart momentum
```

### Check P&L
```bash
python pnl_check.py
```

### Monitor All Bots
```bash
python bot_manager.py health
```

### Stop All Bots
```bash
python bot_manager.py stop-all
```

## File Structure

```
bybit-trading-skill/
├── SKILL.md                 # Skill documentation
├── bot_manager.py          # Central bot management
├── pnl_check.py           # P&L reporting
├── scalping_bot.py        # RSI+BB scalping strategy
├── mean_reversion_trader.py
├── momentum_trader.py
├── grid_trader.py
├── ensure_tp_sl.py        # TP/SL protection
├── challenge_monitor.py   # Challenge tracking
├── circuit_breaker.py     # Risk management
└── config/
    ├── __init__.py
    └── settings.py
```

## Strategies

### Scalping (RSI + Bollinger Bands)
- Timeframe: 1m
- Entry: RSI oversold/bought + BB bounce
- TP: 0.8%
- SL: 0.5%
- Max hold: 15-20 minutes

### Mean Reversion
- Timeframe: 5m/15m
- Entry: Price deviation from mean
- TP: 2-3%
- SL: 1.5%

### Momentum
- Timeframe: 15m/1h
- Entry: Breakout with volume
- TP: 5-8%
- SL: 2-3%

## Risk Management

- Max 5 positions per strategy
- Position size: 5-10% of balance
- Leverage: 3-5x (configurable)
- Daily loss limit: 5%
- Circuit breaker at 10% drawdown

## Cron Jobs

Set up automated monitoring:
```bash
# P&L updates every 30 minutes
# TP/SL guardian every minute
# Bot health checks every 15 minutes
```

## Disclaimer

This is for educational purposes. Trading carries risk. Never trade with money you can't afford to lose.

## License

MIT License - See LICENSE file
