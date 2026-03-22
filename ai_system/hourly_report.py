# -*- coding: utf-8 -*-
"""
AI Trading System - Status Reporter
Sends hourly reports to Telegram
"""

import asyncio
import requests
import sys
import os
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# Telegram config
TELEGRAM_BOT_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

# Bybit config
API_KEY = "KfmiIdWd16hG18v2O7"
API_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"


def get_bybit_data():
    """Get open positions and balance from Bybit"""
    import hmac
    import hashlib
    import time
    import json
    
    ts = str(int(time.time() * 1000))
    
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": ts,
        "Content-Type": "application/json"
    }
    
    try:
        # Get tickers
        r = requests.get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "linear", "limit": 20},
            timeout=10
        )
        
        tickers = r.json().get("result", {}).get("list", [])
        
        # Get wallet
        endpoint = "/v5/account/wallet-balance"
        params = {"accountType": "UNIFIED"}
        msg = ts + API_KEY + endpoint + json.dumps(params)
        sign = hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
        headers["X-BAPI-SIGN"] = sign
        
        r2 = requests.get(
            "https://api.bybit.com" + endpoint,
            params=params,
            headers=headers,
            timeout=10
        )
        
        balance_data = r2.json().get("result", {}).get("list", [{}])
        equity = float(balance_data.get("totalEquity", 0)) if balance_data else 0
            
        return {
            "positions": len(tickers),
            "equity": equity,
            "status": "running"
        }
    except Exception as e:
        return {"positions": 0, "equity": 0, "status": f"error: {e}"}


def send_telegram(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass


def generate_report():
    """Generate hourly trading report"""
    
    # Get system status
    data = get_bybit_data()
    
    # Format message
    now = datetime.now().strftime("%H:%M")
    
    message = f"""
*AI Trading Report*

Time: {now}
Status: {data['status']}

Equity: ${data['equity']:.2f}
Open Positions: {data['positions']}

AI System: Active
"""
    
    return message


def main():
    """Main reporter loop"""
    print("Starting hourly reporter...")
    
    while True:
        try:
            report = generate_report()
            print(report)
            send_telegram(report)
        except Exception as e:
            print(f"Error: {e}")
        
        # Wait 1 hour
        import time
        time.sleep(3600)


if __name__ == "__main__":
    main()
