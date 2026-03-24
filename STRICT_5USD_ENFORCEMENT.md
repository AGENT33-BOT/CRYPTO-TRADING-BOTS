# STRICT $5 MAX LOSS ENFORCEMENT PROTOCOL
# Feb 28, 2026 - EMERGENCY IMPLEMENTATION

## PROBLEM IDENTIFIED
- Multiple positions exceeded $5 max loss limit
- NEAR position reached -$12.69 (253% over limit!)
- ETH position reached -$6.57 (131% over limit!)
- Position sizing too large for $5 limit

## IMMEDIATE ACTIONS TAKEN

### 1. Position Audit
✅ Checked all positions for $5 violations
✅ Found NO current violations (positions within limit)
✅ Balance: $424.96 USDT

### 2. New Hard Limits (HARDCODED)
```python
MAX_POSITION_LOSS_USD = 5.0      # ABSOLUTE MAX - No exceptions
MAX_POSITION_SIZE_PCT = 0.05     # 5% of account (reduced from 10%)
MAX_TOTAL_EXPOSURE_PCT = 25.0    # 25% max total (reduced from 50%)
```

### 3. Position Sizing Formula (REQUIRED)
```python
# Size = $5 / (Entry_Price × Stop_Loss_Pct)
# Example: Entry $100, SL 1.5%
# Size = $5 / ($100 × 0.015) = $5 / $1.50 = 3.33 units
```

### 4. Bot Configuration Updates Required

#### Mean Reversion Bot
```python
'position_size_pct': 0.05,      # REDUCED from 0.10
'max_positions': 2,              # REDUCED from 3
'min_confidence': 85,            # INCREASED from 80
'stop_loss_pct': 0.015,          # 1.5% SL (tight)
'take_profit_pct': 0.025,        # 2.5% TP
```

#### Momentum Bot
```python
'position_size_pct': 0.05,      # REDUCED from 0.10
'max_positions': 2,              # REDUCED from 3
'min_confidence': 90,            # INCREASED from 85
'stop_loss_pct': 0.015,          # 1.5% SL (tight)
'take_profit_pct': 0.025,        # 2.5% TP
```

#### Scalping Bot
```python
'position_size_pct': 0.03,      # REDUCED from 0.05
'max_positions': 1,              # REDUCED from 2
'min_confidence': 90,            # INCREASED from 85
'max_hold_minutes': 5,           # REDUCED from 10
```

#### Grid Trading Bot
```python
'grid_levels': 3,                # REDUCED from 5
'grid_range_pct': 0.02,          # 2% range (tight)
'max_investment': 20,            # $20 max (reduced from $30)
```

### 5. NEW Circuit Breaker (IMMEDIATE DEPLOYMENT)
```python
# Auto-close if:
# - Any position loss > $5
# - Daily portfolio loss > $10
# - Margin < 10%
```

### 6. Trading Restrictions (NEW)

**BANNED from new positions:**
- LINK (historical loser)
- ADA (historical loser)
- Any position with size > $20

**ALLOWED (WINNERS ONLY):**
- BTC, ETH, SOL, DOGE, XRP, NEAR
- Must meet 85%+ confidence threshold
- Must have SL set BEFORE entry

### 7. Daily Risk Limits
```
Max Daily Loss: $10 (hard stop)
Max Trades per Day: 5
Max Concurrent Positions: 3
Max Position Size: $20 (absolute)
```

### 8. Verification Protocol
Every 5 minutes, system checks:
1. All positions < $5 loss
2. Total exposure < 25%
3. Free margin > $100
4. No banned symbols

If ANY check fails → Auto-close violating positions

## IMPLEMENTATION CHECKLIST

- [x] Audit current positions
- [ ] Stop all bots
- [ ] Update all bot configs with new limits
- [ ] Deploy strict circuit breaker
- [ ] Restart bots with new parameters
- [ ] Monitor for 1 hour
- [ ] Verify no $5 violations

## SUCCESS METRICS

Week 1:
- Zero positions exceed $5 loss
- Daily P&L never < -$10
- All positions have SL before entry
- Max 3 concurrent positions

Week 4:
- Positive overall P&L
- <10% max drawdown
- Win rate >55%

## CURRENT STATUS

Balance: $424.96 USDT
Positions: 2 (within $5 limit)
Bots: Need restart with new config

Next: Updating configs and restarting with STRICT enforcement.
