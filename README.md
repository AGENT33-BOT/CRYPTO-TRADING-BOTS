# Crypto Trader

Automated cryptocurrency trading system with Bybit and Alpaca integration.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables (optional but recommended):**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

3. **Run P&L check:**
   ```bash
   python pnl_check.py
   ```

## Environment Variables

The system supports environment variables for secure credential management:

| Variable | Description | Required |
|----------|-------------|----------|
| `BYBIT_API_KEY` | Bybit API key | Yes |
| `BYBIT_API_SECRET` | Bybit API secret | Yes |
| `ALPACA_API_KEY` | Alpaca API key | Yes (for Alpaca) |
| `ALPACA_SECRET_KEY` | Alpaca API secret | Yes (for Alpaca) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | No |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | No |

**Note:** If environment variables are not set, the system falls back to hardcoded values in `pnl_check.py` (not recommended for production).

## Scripts

- `pnl_check.py` - Display current P&L summary
- `check_bybit_status.py` - Check Bybit account status
- `bybit_tp_sl_guardian.py` - Monitor and set TP/SL for positions

## Security Best Practices

1. Never commit `.env` files with real credentials
2. Use environment variables instead of hardcoded credentials
3. Rotate API keys regularly
4. Use IP whitelisting on exchange APIs when possible

## Troubleshooting

**"unauthorized" error:** Check that your API keys are valid and have the correct permissions.

**"requires apiKey credential" error:** The API keys are not being loaded. Check your `.env` file or the hardcoded values.
