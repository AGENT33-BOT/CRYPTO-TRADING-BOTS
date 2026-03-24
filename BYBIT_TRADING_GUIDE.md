# Bybit Trading Bot - Complete Setup Guide

## Quick Start

```python
import ccxt

bybit = ccxt.bybit({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_API_SECRET',
    'options': {'defaultType': 'swap'}
})
```

## Get Open Positions

```python
positions = bybit.fetch_positions()
for p in positions:
    if float(p.get('contracts', 0)) > 0:
        print(p['symbol'], p['side'], p['contracts'])
```

## Check TP/SL (Important!)

Bybit stores TP/SL in the `info` dict, not top-level:

```python
positions = bybit.fetch_positions()
for p in positions:
    if float(p.get('contracts', 0)) > 0:
        info = p.get('info', {})
        tp = info.get('takeProfit', '0')
        sl = info.get('stopLoss', '0')
        trail = info.get('trailingStop', '0')
        print(f"{p['symbol']} | TP: {tp} | SL: {sl} | Trail: {trail}")
```

## Set TP/SL + Trailing Stop (v5 API)

```python
def set_tpsl(symbol, side, entry_price):
    """
    Set TP 2.5%, SL 2.5%, Trailing 1% (activates after 1% profit)
    """
    clean_sym = symbol.replace('/USDT', '')  # LINK/USDT -> LINKUSDT
    
    if side in ['buy', 'long']:
        tp = round(entry_price * 1.025, 4)      # 2.5% profit
        sl = round(entry_price * 0.975, 4)      # 2.5% loss
        trail = round(entry_price * 0.01, 4)    # 1% trailing
        active = round(entry_price * 1.01, 4)   # Activate after 1% profit
    else:  # sell/short
        tp = round(entry_price * 0.975, 4)
        sl = round(entry_price * 1.025, 4)
        trail = round(entry_price * 0.01, 4)
        active = round(entry_price * 0.99, 4)
    
    result = bybit.privatePostV5PositionTradingStop({
        'category': 'linear',
        'symbol': clean_sym,
        'takeProfit': str(tp),
        'stopLoss': str(sl),
        'trailingStop': str(trail),
        'activePrice': str(active),
        'tpslMode': 'Full'
    })
    
    if result.get('retCode') == 0:
        print(f"Success! TP: {tp}, SL: {sl}")
    else:
        print(f"Error: {result.get('retMsg')}")
```

## Complete Position Monitor Script

```python
"""
TP/SL Monitor - Run every minute via cron
"""
import ccxt

bybit = ccxt.bybit({
    'apiKey': 'KfmiIdWd16hG18v2O7',
    'secret': 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ',
    'options': {'defaultType': 'swap'}
})

positions = bybit.fetch_positions()

for p in positions:
    size = float(p.get('contracts', 0))
    if size > 0:
        info = p.get('info', {})
        tp = info.get('takeProfit', '0')
        sl = info.get('stopLoss', '0')
        
        if tp == '0' or sl == '0':
            # No protection - set it!
            symbol = p['symbol'].split(':')[0]  # Remove :USDT
            side = p['side']
            entry = float(p['entryPrice'])
            set_tpsl(symbol, side, entry)
            print(f"Fixed {symbol}")
        else:
            print(f"Protected: {p['symbol']}")
```

## OpenClaw Cron Jobs (jobs.json)

```json
[
  {
    "id": "tpsl-monitor",
    "schedule": {"kind": "cron", "expr": "*/1 * * * *"},
    "enabled": true,
    "name": "TP/SL Monitor",
    "payload": {"kind": "systemEvent", "text": "python /path/to/tpsl_monitor_check.py"},
    "sessionTarget": "main",
    "wakeMode": "now"
  },
  {
    "id": "position-report",
    "schedule": {"kind": "cron", "expr": "*/30 * * * *"},
    "enabled": true,
    "name": "Position Report",
    "payload": {"kind": "systemEvent", "text": "python /path/to/position_report.py"},
    "sessionTarget": "main",
    "wakeMode": "now"
  }
]
```

## Settings

| Parameter | Value |
|-----------|-------|
| TP (Take Profit) | 2.5% |
| SL (Stop Loss) | 2.5% |
| Trailing Stop | 1% (activates at 1% profit) |
| Max Positions | 3 |
| Position Size | 10% of balance |

## Common Errors

- **retCode 10004**: Signature error - check param order
- **retCode 34040**: Not modified - TP/SL already set
- **retCode 0**: Success!

## Telegram Alerts

```python
import requests

TELEGRAM_TOKEN = "BOT_TOKEN"
TELEGRAM_CHAT_ID = "CHAT_ID"

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
```