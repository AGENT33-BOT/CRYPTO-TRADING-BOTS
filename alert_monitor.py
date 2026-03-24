# Trading Bot Alert Monitor
# Checks logs and sends Telegram alerts

import os
import re
import time
from datetime import datetime

# Log files
TRENDLINE_LOG = "C:/Users/digim/clawd/crypto_trader/trendline_trading.log"
ORIGINAL_LOG = "C:/Users/digim/clawd/crypto_trader/bybit_trading.log"

# Track last positions in files
last_trendline_pos = 0
last_original_pos = 0

def send_alert(message):
    """Send alert via OpenClaw messaging"""
    # This will be called by the monitoring script
    print(f"ALERT: {message}")
    return message

def check_log_file(log_file, last_pos, bot_name):
    """Check log file for new entries"""
    alerts = []
    
    if not os.path.exists(log_file):
        return last_pos, alerts
    
    with open(log_file, 'r') as f:
        f.seek(last_pos)
        new_lines = f.readlines()
        new_pos = f.tell()
    
    for line in new_lines:
        # Check for trade entries
        if "POSITION OPENED" in line:
            alerts.append(f"🟢 {bot_name}: Trade OPENED")
        elif "POSITION CLOSED" in line:
            alerts.append(f"🔴 {bot_name}: Trade CLOSED")
        elif "ERROR" in line.upper() or "FAILED" in line.upper():
            alerts.append(f"⚠️ {bot_name}: ERROR - {line.strip()}")
    
    return new_pos, alerts

def monitor_loop():
    """Main monitoring loop"""
    global last_trendline_pos, last_original_pos
    
    print("Starting Trading Bot Monitor...")
    print(f"Monitoring: {TRENDLINE_LOG}")
    print(f"Monitoring: {ORIGINAL_LOG}")
    
    # Initialize file positions
    for log_file, pos_var in [(TRENDLINE_LOG, 'trendline'), (ORIGINAL_LOG, 'original')]:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                f.seek(0, 2)  # End of file
                if pos_var == 'trendline':
                    last_trendline_pos = f.tell()
                else:
                    last_original_pos = f.tell()
    
    while True:
        try:
            # Check Trendline Trader
            last_trendline_pos, trendline_alerts = check_log_file(
                TRENDLINE_LOG, last_trendline_pos, "Trendline Trader"
            )
            
            # Check Original Trader
            last_original_pos, original_alerts = check_log_file(
                ORIGINAL_LOG, last_original_pos, "Original Trader"
            )
            
            # Send all alerts
            all_alerts = trendline_alerts + original_alerts
            for alert in all_alerts:
                send_alert(alert)
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_loop()
