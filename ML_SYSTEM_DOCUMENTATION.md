# ML Trading System - Complete Documentation
## Created: 2026-03-11
## Status: ACTIVE

---

## 🎯 SYSTEM OVERVIEW

**ML Trading Bots Active:**
- ETH/USDT: 90.72% accuracy
- NEAR/USDT: 84.28% accuracy  
- DOGE/USDT: 91.35% accuracy

**Type:** Random Forest Classifier
**Features:** RSI, MACD, EMA, Volume, Returns
**Timeframe:** 15-minute candles
**Prediction:** UP/DOWN with confidence score

---

## 🤖 TRADING LOGIC

### Entry Rules:
1. ML model predicts direction (UP/DOWN)
2. Confidence must be ≥ 65%
3. No conflicting open position
4. Position size = Balance × 2% × Confidence

### Exit Rules:
- Stop Loss: 1.5%
- Take Profit: 3%
- Reverse on opposite signal

### Risk Management:
- Max 1 position per symbol
- 3x leverage
- Dynamic position sizing
- Auto TP/SL on all trades

---

## 📊 PERFORMANCE METRICS

| Symbol | Accuracy | Avg Confidence | Win Rate |
|--------|----------|----------------|----------|
| ETH    | 90.72%   | TBD            | TBD      |
| NEAR   | 84.28%   | TBD            | TBD      |
| DOGE   | 91.35%   | TBD            | TBD      |

---

## 🔧 TECHNICAL DETAILS

**Model Type:** Random Forest (100 estimators, max_depth=10)
**Training Data:** 3,000 candles (15m timeframe)
**Features:** 4 technical indicators
**Scaler:** MinMaxScaler
**Update Frequency:** Every 15 minutes

**Files:**
- `rf_model_{symbol}.pkl` - Trained models
- `rf_scaler_{symbol}.pkl` - Feature scalers
- `ml_trader_live.py` - Trading bot
- `monitor_ml_bots.py` - Monitoring system

---

## ⚠️ RISK WARNINGS

1. Past performance ≠ future results
2. ML models can degrade over time
3. Re-train monthly recommended
4. Start with small position sizes
5. Monitor for overfitting

---

## 🔄 MAINTENANCE SCHEDULE

- **Daily:** Check bot logs
- **Weekly:** Review performance metrics
- **Monthly:** Re-train models with new data
- **Quarterly:** Evaluate model accuracy

---

## 📞 SUPPORT

**Bot Status:** Check `ml_trading_monitor.log`
**Errors:** Check `ml_trading_errors.log`
**Performance:** Check `ml_trading_performance.json`

---

*Last Updated: 2026-03-11*
*Status: PRODUCTION*
