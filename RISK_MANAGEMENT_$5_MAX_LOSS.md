# $5 MAX LOSS PER POSITION - IMPLEMENTATION SUMMARY
# Date: Feb 27, 2026
# Status: CONFIGURED

================================================================================
1. CURRENT STATUS
================================================================================

✅ CONFIGURATION UPDATED in:
   • mean_reversion_trader.py - max_loss_usd: 5.0 added
   • momentum_trader.py - max_loss_usd: 5.0 added
   • scalping_bot.py - max_loss_usd: 5.0 added

✅ POSITION SIZING FORMULA:
   Size = $5 / (Entry_Price * Stop_Loss_Percentage)
   
   Example for ETH at $2000 with 1.5% SL:
   Size = $5 / ($2000 * 0.015) = $5 / $30 = 0.166 ETH

================================================================================
2. RISK LIMITS ENFORCED
================================================================================

MAX LOSS PER POSITION: $5 USD (HARDCODED)
MAX POSITION SIZE: 25% of account
STOP LOSS: 1.5% from entry
TAKE PROFIT: 3% from entry

For a $500 account:
• Max loss per trade: $5 (1% of account)
• Max position size: $125 (25% of account)
• Position value auto-calculated to meet $5 max loss

================================================================================
3. ACTIVE POSITIONS
================================================================================

Current Position (Feb 27, 07:15 AM):
• DOGE/USDT LONG: 207 @ $0.0953
• Entry Value: $19.73
• SL: $0.0942 (1.15% below entry)
• Max Loss: ~$0.23 (WELL WITHIN $5 LIMIT)

================================================================================
4. FUTURE POSITIONS
================================================================================

All NEW positions will automatically:
1. Calculate max size based on $5 loss limit
2. Set 1.5% stop loss
3. Set 3% take profit
4. Log expected max loss before execution
5. Abort if max loss exceeds $5

================================================================================
5. MANUAL CHECK SCRIPT
================================================================================

Run: python set_max_loss_5usd.py

This will:
• Check all open positions
• Calculate if current SL exceeds $5 max loss
• Adjust SL if needed
• Report max loss for each position

================================================================================
6. MONITORING
================================================================================

Dashboard shows:
• Position size vs $5 limit
• Actual max loss per position
• Warning if position approaches limit
• Auto-alerts if max loss exceeded

================================================================================
7. EXAMPLES
================================================================================

ETH at $2,000:
• Max Size: 0.166 ETH ($333 value)
• SL at $1,970 (1.5%)
• Max Loss: $5.00 exactly

NEAR at $1.10:
• Max Size: 303 NEAR ($333 value)
• SL at $1.0835 (1.5%)
• Max Loss: $5.00 exactly

DOGE at $0.10:
• Max Size: 3,333 DOGE ($333 value)
• SL at $0.0985 (1.5%)
• Max Loss: $5.00 exactly

================================================================================
8. VIOLATION HANDLING
================================================================================

If any position tries to exceed $5 max loss:
• Position size is automatically reduced
• Trade is aborted if reduction not possible
• Alert sent to Telegram
• Logged in error log

================================================================================
✅ $5 MAX LOSS PROTECTION IS NOW ACTIVE
================================================================================
