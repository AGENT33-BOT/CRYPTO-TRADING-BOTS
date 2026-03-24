# Polymarket Setup Guide

## Overview

This guide explains how to set up the Polymarket trading bot from paper trading to live trading.

---

## Quick Start (Paper Trading)

Paper trading is enabled by default for safety. No real money is at risk.

```bash
cd crypto_trader
python polymarket_trader.py
```

The bot will:
1. Scan for trading opportunities
2. Simulate trades (no real execution)
3. Log what trades would be executed

---

## Prerequisites for Live Trading

Before going live, you need:

### 1. Polygon Wallet with USDC.e

Polymarket operates on the Polygon network. You need:

- **MATIC tokens** for gas fees (~10-20 MATIC recommended)
- **USDC.e** ( bridged USDC on Polygon) for trading

**Minimum recommended deposit:** $100-500 for testing, more for serious trading

### 2. Get USDC.e on Polygon

**Option A: Bridge from Ethereum**
1. Go to https://portal.polygon.technology/bridge
2. Connect your wallet
3. Bridge USDC from Ethereum to Polygon PoS
4. Wait for confirmation (~10-20 minutes)

**Option B: Buy directly on Polygon**
1. Use an exchange that supports Polygon withdrawals (Binance, Coinbase, etc.)
2. Withdraw USDC directly to your Polygon address
3. Make sure to select "Polygon PoS" network

### 3. API Credentials from Polymarket

The bot needs valid API credentials from Polymarket.

**Generate API Keys:**
1. Visit https://polymarket.com/settings/api
2. Connect your wallet
3. Click "Generate API Key"
4. Save the following:
   - API Key
   - API Secret
   - Passphrase

**Important:** Store these securely. The secret is shown only once.

### 4. Configure the Bot

Edit `polymarket_config.json`:

```json
{
  "polymarket": {
    "api_key": "your-api-key-here",
    "api_secret": "your-api-secret-here",
    "passphrase": "your-passphrase-here",
    "private_key": "0x-your-private-key-here",
    "paper_trading": false
  }
}
```

**Security Notes:**
- Never commit this file to git
- Use a dedicated wallet for trading
- Consider using environment variables instead of hardcoding

---

## Going Live

### Step 1: Test Paper Trading

Run for at least 24-48 hours in paper mode:

```bash
python polymarket_trader.py
```

Verify:
- Opportunities are being detected
- Token IDs are extracted correctly
- Risk management is working

### Step 2: Checklist Before Live

See [SAFETY_CHECKLIST.md](SAFETY_CHECKLIST.md) for complete checklist.

Key items:
- [ ] Valid API credentials
- [ ] USDC.e deposited on Polygon
- [ ] Token allowance approved
- [ ] Small test trade successful
- [ ] Stop-loss configured
- [ ] Position limits set appropriately

### Step 3: Enable Live Trading

Run with the `--live` flag:

```bash
python polymarket_trader.py --live --max-trades 1
```

Start with `--max-trades 1` to limit risk on first run.

### Step 4: Monitor First Trades

Watch the logs carefully:
- Verify orders are placed
- Check execution prices
- Confirm positions are tracked
- Monitor gas costs

---

## Understanding the Configuration

### Position Sizing

```json
"max_position_size": 20    // Maximum $ per trade
"max_total_exposure": 100  // Maximum total $ at risk
```

Start small and increase gradually as you gain confidence.

### Edge Requirements

```json
"min_edge": 0.05  // 5% minimum edge
```

Higher = fewer trades, better quality. Lower = more trades, more noise.

### Liquidity Filters

```json
"min_liquidity": 5000   // $5k minimum
"min_volume": 25000     // $25k minimum
```

Prevents trading illiquid markets where you can't exit.

---

## Troubleshooting

### "401 Unauthorized / Invalid api key"

Your API credentials are invalid or expired.

**Fix:** Generate new API keys at https://polymarket.com/settings/api

### "Insufficient balance"

You don't have enough USDC.e on Polygon.

**Fix:** 
1. Check your Polygon wallet balance
2. Bridge or deposit more USDC.e
3. Ensure you have MATIC for gas

### "Token allowance not set"

The bot needs approval to spend USDC.e.

**Fix:** 
The bot should auto-set allowance on first run. If it fails:
1. Manually approve USDC.e on Polymarket UI
2. Or call `set_allowance()` via py_clob_client

### Token ID Extraction Issues

If you see "No token_id for {signal} - cannot trade":

1. Check `test_token_extraction.py` output
2. Verify market data format hasn't changed
3. See [TOKEN_ID_FIX.md](TOKEN_ID_FIX.md) for details

---

## Monitoring Your Trading

### Log Files

- `polymarket_trader.log` - Main trading log
- `polymarket_positions.json` - Current positions

### Telegram Notifications (Optional)

Create `trade_notifier.py` to send trade alerts:

```python
def send_message(text):
    # Your Telegram bot implementation
    pass
```

---

## Risk Management Best Practices

1. **Never risk more than you can afford to lose**
2. **Start with paper trading** for at least a week
3. **Use conservative position sizing** initially
4. **Monitor correlation** - don't bet on related events
5. **Set stop losses** for each position
6. **Review and adjust** strategy weekly

---

## Support

- Polymarket Discord: https://discord.gg/polymarket
- CLOB Client Docs: https://github.com/Polymarket/py-clob-client
- API Reference: https://docs.polymarket.com

---

**Remember:** Trading prediction markets involves risk. Past performance doesn't guarantee future results.
