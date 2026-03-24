import ccxt
import json
import time
import logging
from datetime import datetime
import requests

# Telegram config
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'
TELEGRAM_CHAT_ID = '5804173449'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('boss33_alerts.log'),
        logging.StreamHandler()
    ]
)

def send_telegram_alert(message):
    """Send alert to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logging.error(f"Failed to send Telegram alert: {e}")

def check_positions_and_alert():
    """Monitor positions and send alerts on changes"""
    API_KEY = 'bsK06QDhsagOWwFsXQ'
    API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
    
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'linear'}
    })
    
    # Track previous state
    prev_positions = {}
    
    logging.info("🔔 BOSS33 Alert Monitor Started")
    
    while True:
        try:
            # Get current positions
            current_positions = {}
            total_pnl = 0
            
            for symbol in ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT']:
                try:
                    pos_list = exchange.fetch_positions([symbol])
                    if pos_list and len(pos_list) > 0:
                        pos = pos_list[0]
                        contracts = float(pos.get('contracts', 0))
                        if contracts > 0:
                            entry = float(pos.get('entryPrice', 0))
                            mark = float(pos.get('markPrice', 0))
                            pnl = float(pos.get('unrealizedPnl', 0))
                            side = pos['side']
                            current_positions[symbol] = {
                                'side': side,
                                'contracts': contracts,
                                'entry': entry,
                                'mark': mark,
                                'pnl': pnl
                            }
                            total_pnl += pnl
                except:
                    pass
            
            # Check for new positions
            for symbol, pos in current_positions.items():
                if symbol not in prev_positions:
                    # New position opened!
                    emoji = "🟢" if pos['side'] == 'long' else "🔴"
                    alert = f"""{emoji} <b>BOSS33 NEW POSITION</b>

<b>{symbol}</b> | {pos['side'].upper()}
Size: {pos['contracts']:.4f}
Entry: ${pos['entry']:.2f}
Mark: ${pos['mark']:.2f}"""
                    send_telegram_alert(alert)
                    logging.info(f"New position alert sent: {symbol}")
            
            # Check for closed positions
            for symbol, pos in prev_positions.items():
                if symbol not in current_positions:
                    # Position closed!
                    alert = f"""⚪ <b>BOSS33 POSITION CLOSED</b>

<b>{symbol}</b> | {pos['side'].upper()}
Result: ${pos['pnl']:+.2f}"""
                    send_telegram_alert(alert)
                    logging.info(f"Position closed alert sent: {symbol}")
            
            # Check for significant PnL changes (>5% move)
            for symbol, pos in current_positions.items():
                if symbol in prev_positions:
                    pnl_change = pos['pnl'] - prev_positions[symbol]['pnl']
                    if abs(pnl_change) > 5:  # $5+ move
                        emoji = "📈" if pnl_change > 0 else "📉"
                        alert = f"""{emoji} <b>BOSS33 PnL Update</b>

<b>{symbol}</b> | {pos['side'].upper()}
PnL: ${pos['pnl']:+.2f}
Change: ${pnl_change:+.2f}"""
                        send_telegram_alert(alert)
            
            # Update previous state
            prev_positions = current_positions.copy()
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logging.error(f"Error in monitor loop: {e}")
            time.sleep(60)

if __name__ == '__main__':
    check_positions_and_alert()
