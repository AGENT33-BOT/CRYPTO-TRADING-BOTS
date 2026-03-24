# Safety Checklist - Before Going Live

## ⚠️ CRITICAL: DO NOT SKIP THESE STEPS

Trading with real money carries risk. Complete this checklist before enabling live trading.

---

## Pre-Flight Checklist

### ✅ Wallet Setup

- [ ] **Dedicated trading wallet created**
  - Don't use your primary wallet
  - Use a fresh wallet just for this bot
  
- [ ] **Polygon network configured in wallet**
  - Network Name: Polygon PoS
  - RPC URL: https://polygon-rpc.com
  - Chain ID: 137
  - Currency: MATIC
  
- [ ] **MATIC for gas fees deposited**
  - Minimum: 20 MATIC recommended
  - Check: https://polygonscan.com/address/YOUR_ADDRESS

- [ ] **USDC.e deposited on Polygon**
  - Bridge from Ethereum OR withdraw from exchange
  - Minimum recommended: $100-500 for testing
  - Verify: Token contract `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`

### ✅ API Credentials

- [ ] **New API key generated from Polymarket**
  - URL: https://polymarket.com/settings/api
  - API Key: _______________
  - API Secret: _______________
  - Passphrase: _______________
  
- [ ] **Credentials tested and valid**
  ```bash
  python diagnose_auth.py
  ```
  Expected: No "401 Unauthorized" errors
  
- [ ] **Private key added to config**
  - Format: `0x` followed by 64 hex characters
  - Total length: 66 characters
  - Example: `0x1234...abcd`

### ✅ Configuration

- [ ] **polymarket_config.json updated**
  ```json
  {
    "polymarket": {
      "api_key": "your-key",
      "api_secret": "your-secret", 
      "passphrase": "your-passphrase",
      "private_key": "0x...",
      "paper_trading": false
    }
  }
  ```

- [ ] **Position limits set conservatively**
  ```json
  "max_position_size": 20,    // Start with $20 max per trade
  "max_total_exposure": 100   // $100 max total exposure
  ```

- [ ] **Risk parameters configured**
  ```json
  "min_edge": 0.05,        // 5% minimum edge
  "min_liquidity": 5000,   // $5k minimum market liquidity
  "min_volume": 25000      // $25k minimum market volume
  ```

### ✅ Testing

- [ ] **Paper trading run for 24+ hours**
  ```bash
  python polymarket_trader.py
  ```
  - Verify opportunities are detected
  - Check token extraction logs
  - Confirm no crashes or errors

- [ ] **Log review completed**
  - Check `polymarket_trader.log`
  - Verify no ERROR or WARNING messages
  - Confirm opportunity detection is working

- [ ] **Test order placed manually (optional)**
  - Place a small test order on Polymarket UI
  - Verify wallet connection works
  - Confirm USDC.e approval/allowance

### ✅ System

- [ ] **Python environment ready**
  ```bash
  pip install py-clob-client requests
  ```

- [ ] **Monitoring in place**
  - Log files accessible
  - Telegram notifications configured (optional)
  - Way to stop bot quickly if needed

- [ ] **Emergency stop plan**
  - Know how to kill the process (Ctrl+C)
  - Have position close commands ready
  - Polymarket UI bookmarked for manual intervention

---

## First Live Trade Protocol

### Step 1: Single Trade Test

```bash
python polymarket_trader.py --live --max-trades 1
```

Watch for:
- Order placement confirmation
- Transaction hash
- Position tracking in logs

### Step 2: Verify on Blockchain

1. Copy transaction hash from logs
2. Check on https://polygonscan.com/
3. Confirm:
   - Order executed at expected price
   - Gas fees reasonable
   - Position shows in your wallet

### Step 3: Monitor Position

- Check position in `polymarket_positions.json`
- Verify market price movement
- Confirm you can close position if needed

### Step 4: Gradual Scale-Up

Only after successful single trade:

| Day | Max Trades | Max Position | Notes |
|-----|------------|--------------|-------|
| 1   | 1          | $20          | First live trade |
| 2-3 | 2          | $20          | Build confidence |
| 4-7 | 2          | $50          | Increase size |
| 2+ weeks | 3 | $100+ | Scale gradually |

---

## Risk Limits (Hard Stops)

### Daily Limits

```json
"max_daily_trades": 5
"max_daily_loss": 50    // $50 max daily loss
```

### Position Limits

- Never more than 5% of total capital per trade
- Never more than 20% total exposure
- Stop trading after 3 consecutive losses

### Market Limits

- No markets resolving in < 7 days
- No markets with < $10k liquidity
- No correlated positions (e.g., multiple Trump-related bets)

---

## Emergency Procedures

### If Bot Malfunctions

1. **Press Ctrl+C** to stop immediately
2. Check `polymarket_positions.json` for open positions
3. Manually close positions via Polymarket UI if needed
4. Review logs to identify issue

### If Market Crashes

1. Don't panic sell
2. Assess if thesis has changed
3. Close positions if stop-loss hit
4. Review risk parameters

### If API Issues

1. Check https://status.polymarket.com/
2. Verify API credentials at https://polymarket.com/settings/api
3. Generate new keys if needed
4. Restart bot

---

## Daily Checks

Before starting bot each day:

- [ ] Review overnight positions
- [ ] Check wallet balance (USDC.e + MATIC)
- [ ] Review market news for held positions
- [ ] Confirm no major system updates needed
- [ ] Clear old log files if needed

---

## Weekly Review

Every Sunday (or your chosen day):

1. **Performance Review**
   - Total P&L for week
   - Win rate
   - Average trade size
   - Max drawdown

2. **Strategy Review**
   - Are edge requirements appropriate?
   - Are we trading too many/few markets?
   - Any pattern in losses?

3. **Risk Parameter Review**
   - Adjust position sizes based on performance
   - Update edge requirements if needed
   - Review and document lessons learned

4. **Maintenance**
   - Update dependencies if needed
   - Review and rotate API keys
   - Backup configuration files

---

## Security Checklist

- [ ] Config file NOT committed to git
- [ ] Private key stored securely
- [ ] API keys rotated monthly
- [ ] Wallet has no unnecessary permissions
- [ ] Computer has antivirus/firewall
- [ ] No one else has access to trading machine

---

## Support Contacts

- **Polymarket Discord**: https://discord.gg/polymarket
- **Emergency**: Keep Polymarket support email handy
- **Technical**: Review docs at https://docs.polymarket.com

---

## Final Confirmation

**Before running with `--live` flag, confirm:**

> I have completed all items in this checklist.
> I understand the risks of automated trading.
> I am prepared to lose the entire trading capital.
> I have an emergency plan in place.

**Date:** _______________

**Signature/Initials:** _______________

---

**Remember:** It's better to be cautious and miss opportunities than reckless and lose capital. When in doubt, stay in paper trading mode.
