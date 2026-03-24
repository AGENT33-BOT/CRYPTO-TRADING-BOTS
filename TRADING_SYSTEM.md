# OPENCLAW BYBIT TRADING SYSTEM

## System Overview
AI-powered cryptocurrency trading on Bybit USDT Perpetual Futures

## Approved Pairs (CRITICAL)
- ✅ ETHUSDT (LONG only)
- ✅ SOLUSDT (LONG only)
- ❌ NEAR, LINK, ADA, DOT, AVAX, LTC, BCH (BANNED)

## Risk Parameters
- Max positions: 1-2
- Position size: 5% of balance
- TP: +2.5%
- SL: -1.5%
- Keep 50%+ cash

## Critical Rules
1. NEVER trade banned symbols
2. NEVER open SHORT (LONG only)
3. ALWAYS set TP/SL immediately
4. Cut losers within 1%
5. Monitor balance constantly

## Key Files
```
crypto_trader/
├── quick_check.py     # Balance & positions
├── pnl_check.py       # P&L report
├── ensure_tp_sl.py   # TP/SL guardian
├── emergency_close.py # Close by symbol
├── close_all.py      # Close all
├── stop_bots_now.py  # Kill bots
└── .env.bybit        # API keys
```

## Commands
```bash
# Check status
python quick_check.py

# Emergency close
python emergency_close.py ETHUSDT

# Stop all bots
python stop_bots_now.py

# Close all
python close_all.py ALL
```

## Bot Management
- Mean Reversion: crypto_trader/mean_reversion_trader.py
- Momentum: crypto_trader/momentum_trader.py
- Scalping: crypto_trader/scalping_bot.py
- Funding: crypto_trader/funding_arbitrage.py

## Emergency Contacts
- Telegram Alerts: Configured
- TP/SL Guardian: Cron job every 1 min
