# BOT MONITORING GUIDE

## Current Active Strategies

### 1. GRID TRADING (DOGE/USDT)
- **Status:** RUNNING since 9:18 PM ET
- **Strategy:** Buy low, sell high within price range
- **Grid Levels:** 10 (from $0.09 to $0.10)
- **Investment:** $30 USDT
- **Leverage:** 2x

**Expected Performance:**
- Profits from price bouncing within range
- Each grid level = ~$3 position
- Profit per completed grid cycle: ~1-2%
- Best for: Sideways/slightly volatile markets

**Monitoring:**
- Check `grid_trading.log` for fills
- Look for "BUY filled" and "SELL filled" messages
- Grid is active when DOGE price stays within $0.09-$0.10

---

### 2. FUNDING ARBITRAGE
- **Status:** RUNNING since 9:18 PM ET
- **Strategy:** Capture funding rate payments
- **Pairs Monitored:** BTC, ETH, SOL, XRP, ADA, DOGE, LINK
- **Position Size:** $20 per opportunity
- **Check Interval:** Every 5 minutes

**Expected Performance:**
- Enters when funding rate > 0.01%
- Captures funding payments every 8 hours
- Profit: Funding rate × position size
- Best for: High funding rate environments

**Monitoring:**
- Check `funding_arbitrage.log` for "ENTERING" messages
- Active arbitrages tracked every 5 min
- Next funding: Check log for countdown

---

## Performance Checkpoints

### Hour 1 (10:18 PM)
- Grid: Should have 0-2 fills if price moved
- Funding: 0-1 opportunities if rates spiked

### Hour 6 (3:18 AM)
- Grid: Should have multiple fills
- Funding: May have 1-2 active arbitrages

### Day 1 (Tomorrow 9:18 PM)
- Grid: 5-20 fills expected
- Funding: 0-3 opportunities captured

---

## Warning Signs

**Grid Trading:**
- ⚠️ Price breaks out of $0.09-$0.10 range
- ⚠️ No fills for >2 hours (price too stable)
- ⚠️ Too many fills (price too volatile)

**Funding Arbitrage:**
- ⚠️ No opportunities for >24h (low funding rates)
- ⚠️ Funding rates negative (reverse strategy needed)

---

## Log Files

```bash
# Real-time grid monitoring
tail -f crypto_trader/grid_trading.log

# Real-time funding monitoring  
tail -f crypto_trader/funding_arbitrage.log

# Performance summary
python crypto_trader/monitor_performance.py
```

---

*Created: 2026-02-09 9:36 PM ET*
*Last Updated: 2026-02-09 9:36 PM ET*
