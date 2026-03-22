# Hourly Report Script
# Run with: python hourly_report.py

import ccxt
import requests
import time
from datetime import datetime

# Config
BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

def get_balance():
    """Get Bybit balance"""
    try:
        bybit = ccxt.bybit({
            'apiKey': BYBIT_API_KEY,
            'secret': BYBIT_SECRET,
            'enableRateLimit': True,
        })
        balance = bybit.fetch_balance()
        return balance['USDT']['total']
    except Exception as e:
        return f"Error: {e}"

def send_report(message):
    """Send Telegram report"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def main():
    print("Starting hourly reporter...")
    
    while True:
        try:
            # Get balance
            balance = get_balance()
            now = datetime.now().strftime("%H:%M")
            
            message = f"""
*AI Trading Hourly Report*

Time: {now}
Balance: ${balance}

AI System: Running
Next report in 1 hour
"""
            print(message)
            send_report(message)
            
        except Exception as e:
            print(f"Error: {e}")
        
        # Sleep 1 hour
        time.sleep(3600)

if __name__ == "__main__":
    main()
