# TP/SL GUARDIAN MONITOR - SETUP GUIDE
# Feb 27, 2026

================================================================================
1. WHAT IS THIS?
================================================================================

The TP/SL Guardian Monitor is a continuous protection system that:
✅ Checks ALL open positions every 5 minutes
✅ Verifies every position has Take Profit (TP) and Stop Loss (SL)
✅ AUTOMATICALLY adds missing TP/SL
✅ Sends alerts when protection is added
✅ Logs all activity for review

================================================================================
2. FILES CREATED
================================================================================

📁 tpsl_guardian_monitor.py    - Main monitoring script
📁 start_guardian_monitor.bat   - Windows launcher
📁 guardian_monitor.log         - Live log of all checks
📁 guardian_report.json         - Latest check report

================================================================================
3. HOW TO RUN
================================================================================

METHOD 1: Manual (Windows)
----------------------------
Double-click: start_guardian_monitor.bat

Or run in terminal:
    cd C:\Users\digim\clawd\crypto_trader
    python tpsl_guardian_monitor.py

METHOD 2: Background Service (Windows)
--------------------------------------
1. Open Task Scheduler
2. Create Basic Task
3. Name: "TP/SL Guardian"
4. Trigger: When computer starts
5. Action: Start a program
6. Program: C:\Users\digim\clawd\crypto_trader\start_guardian_monitor.bat
7. Check: "Run whether user is logged on or not"

METHOD 3: Cron Job (Linux/Mac)
-------------------------------
Add to crontab:
    */5 * * * * cd /path/to/crypto_trader && python3 tpsl_guardian_monitor.py

================================================================================
4. PROTECTION RULES
================================================================================

DEFAULT TP/SL LEVELS:
• Take Profit: 2.5% from entry (profitable)
• Stop Loss: 1.5% from entry (risk limit)

Example for ETH at $2,000:
• Entry: $2,000
• TP: $2,050 (+2.5%)
• SL: $1,970 (-1.5%)

================================================================================
5. ALERT SYSTEM
================================================================================

When TP/SL is added, the guardian sends:
1. Console log (visible in terminal)
2. Log file entry (guardian_monitor.log)
3. Telegram alert (if bot token is valid)

================================================================================
6. MONITORING OUTPUT
================================================================================

Example output:

    [2026-02-27 08:50:00] 🛡️ TP/SL GUARDIAN - 5 MINUTE CHECK
    [2026-02-27 08:50:01] [>>] Found 2 open position(s)
    [2026-02-27 08:50:02] 
    [2026-02-27 08:50:02]   [POS] DOGE/USDT:USDT LONG
    [2026-02-27 08:50:02]      Entry: 0.0941 | Size: 105.0
    [2026-02-27 08:50:02]      [OK] Already protected
    [2026-02-27 08:50:03] 
    [2026-02-27 08:50:03]   [POS] ADA/USDT:USDT LONG
    [2026-02-27 08:50:03]      Entry: 0.2831 | Size: 209.0
    [2026-02-27 08:50:03]      [OK] Already protected
    [2026-02-27 08:50:04] 
    [2026-02-27 08:50:04] [SUMMARY]
    [2026-02-27 08:50:04]   Total: 2
    [2026-02-27 08:50:04]   Protected: 2
    [2026-02-27 08:50:04]   Fixed: 0
    [2026-02-27 08:50:04]   Errors: 0
    [2026-02-27 08:50:04] [>>] Sleeping 5 minutes...

================================================================================
7. INTEGRATION WITH EXISTING SYSTEM
================================================================================

This works alongside your existing:
✅ bybit_ensure_tp_sl.py (manual check)
✅ TP/SL Guardian cron jobs
✅ Agent33 autonomous manager

The 5-minute monitor provides CONTINUOUS protection between cron checks.

================================================================================
8. TROUBLESHOOTING
================================================================================

Problem: Monitor won't start
Solution: Check Python is installed: python --version

Problem: API errors
Solution: Verify API keys in .env file

Problem: No Telegram alerts
Solution: Check bot token is valid (may need renewal)

Problem: Positions not found
Solution: Verify defaultType is 'swap' (futures, not spot)

================================================================================
9. CURRENT STATUS (Feb 27, 2026)
================================================================================

✅ All existing positions have TP/SL protection
✅ Guardian monitor script created
✅ Windows launcher created
✅ Ready to run continuously

NEXT STEPS:
1. Double-click start_guardian_monitor.bat
2. Or set up as Windows service
3. Let it run 24/7 for continuous protection

================================================================================
✅ YOUR POSITIONS ARE NOW PROTECTED 24/7
================================================================================
