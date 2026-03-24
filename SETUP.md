# Crypto Trading Bot Setup

## 🚀 Features Added

### 1. Trade Notifications (Telegram)
Get instant Telegram alerts when:
- ✅ A trade is opened (with entry, TP, SL)
- ✅ A trade is closed (with PnL and reason)
- ⚠️ Errors occur

### 2. Performance Dashboard
Web-based dashboard showing:
- 💰 Total balance
- 📈 Total trades & win rate
- 💵 Daily PnL
- 📊 Active positions for both bots
- 📋 Real-time activity log

---

## 📱 Setting Up Telegram Notifications

### Step 1: Create a Telegram Bot
1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the **API token** provided

### Step 2: Get Your Chat ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your ID (e.g., `5804173449`)

### Step 3: Configure the Notifier
Edit `trade_notifier.py`:

```python
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
```

Or create `telegram_config.json`:
```json
{
    "token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
}
```

---

## 📊 Running the Dashboard

### Option 1: Simple Python Server (Recommended)

```bash
cd crypto_trader
python dashboard_server.py
```

Then open: http://localhost:8080

### Option 2: Open HTML Directly

Simply double-click `dashboard.html` in your file explorer.

---

## 🔄 Restarting Bots with New Features

The bots need to be restarted to load the notification module:

### Windows PowerShell:
```powershell
# Stop existing bots
Get-Process python | Where-Object { $_.CommandLine -like "*trader*" } | Stop-Process -Force

# Start Trendline Bot
cd C:\Users\digim\clawd\crypto_trader
Start-Process python -ArgumentList "trendline_trader.py" -WindowStyle Hidden

# Start Bybit Bot
Start-Process python -ArgumentList "bybit_trader_clean.py" -WindowStyle Hidden
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `trade_notifier.py` | Telegram notification module |
| `dashboard.html` | Web dashboard UI |
| `dashboard_server.py` | Simple HTTP server for dashboard |
| `SETUP.md` | This file |

---

## 🔧 Troubleshooting

### Notifications Not Working
1. Check `trade_notifier.py` has correct token and chat ID
2. Make sure you started a conversation with your bot on Telegram
3. Check logs for errors

### Dashboard Not Loading
1. Try opening `dashboard.html` directly in browser
2. For server: make sure port 8080 is available
3. Try a different port: `python dashboard_server.py` then edit port number

### Bots Won't Start After Changes
1. Clear Python cache: `Remove-Item -Path "__pycache__" -Recurse -Force`
2. Check for syntax errors in the Python files
3. Review logs for import errors

---

## 📝 Next Steps

- [ ] Configure Telegram bot token
- [ ] Start the dashboard server
- [ ] Restart both trading bots
- [ ] Wait for next trade to test notifications!

---

## 🎨 Dashboard Preview

The dashboard includes:
- **Dark theme** optimized for trading
- **Auto-refresh** every 30 seconds
- **Mobile responsive** design
- **Real-time PnL** tracking
- **Position tables** with TP/SL levels
