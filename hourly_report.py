# Hourly Report - Fixed version
import ccxt
import requests
import time

BYBIT_API_KEY = "KfmiIdWd16hG18v2O7"
BYBIT_SECRET = "VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ"
TELEGRAM_TOKEN = "8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U"
TELEGRAM_CHAT_ID = "5804173449"

def get_balance():
    try:
        bybit = ccxt.bybit({
            'apiKey': BYBIT_API_KEY,
            'secret': BYBIT_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        time.sleep(1)  # Rate limit
        balance = bybit.fetch_balance()
        return balance['USDT']['total']
    except Exception as e:
        return f"Error: {e}"

def get_positions():
    try:
        bybit = ccxt.bybit({
            'apiKey': BYBIT_API_KEY,
            'secret': BYBIT_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        time.sleep(1)
        positions = bybit.fetch_positions()
        
        result = []
        for p in positions:
            if float(p.get('contracts', 0)) > 0:
                info = p.get('info', {})
                name = p['symbol'].split(':')[0]
                entry = float(info.get('avgPrice', 0))
                mark = float(info.get('markPrice', 0))
                pnl = float(info.get('unrealisedPnl', 0))
                pnl_pct = ((mark - entry) / entry * 100) if entry > 0 else 0
                result.append({
                    'name': name,
                    'pnl_pct': pnl_pct,
                    'pnl': pnl
                })
        return result
    except Exception as e:
        return []

def send_report(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
    except:
        pass

def main():
    print("Generating report...")
    
    balance = get_balance()
    positions = get_positions()
    
    pos_text = ""
    total_pnl = 0
    for p in positions:
        pos_text += f"\n{p['name']}: {p['pnl_pct']:.1f}% ${p['pnl']:.2f}"
        total_pnl += p['pnl']
    
    if not pos_text:
        pos_text = "\nNo open positions"
    
    message = f"""
*AI Trading Report*

Balance: ${balance}
Open Positions: {len(positions)}{pos_text}

Total PnL: ${total_pnl:.2f}

AI System: Running
"""
    print(message)
    send_report(message)

if __name__ == "__main__":
    main()