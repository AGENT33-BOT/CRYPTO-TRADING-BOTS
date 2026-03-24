# Continuous Monitor with Telegram Alerts
# Watches trading activity and sends alerts

import time
import os
from datetime import datetime

def log_monitor():
    """Monitor trading log and send alerts"""
    log_file = 'bybit_trading.log'
    last_position = 0
    
    print(f"Starting monitor at {datetime.now()}")
    print("Watching for trading activity...")
    print("="*70)
    
    while True:
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                    
                    for line in new_lines:
                        line = line.strip()
                        
                        # Check for position opened
                        if 'POSITION OPENED' in line:
                            print(f"\n{'='*70}")
                            print(f"🟢 ALERT: POSITION OPENED!")
                            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
                            print(f"{'='*70}")
                            # Here we would send Telegram alert
                            
                        # Check for position closed
                        elif 'POSITION CLOSED' in line:
                            print(f"\n{'='*70}")
                            print(f"🔴 ALERT: POSITION CLOSED!")
                            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
                            print(f"{'='*70}")
                            # Here we would send Telegram alert
                            
                        # Check for scan complete
                        elif 'Scanning markets' in line:
                            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning markets...")
                            
                        # Check for opportunities
                        elif 'opportunities found' in line or 'No high-confidence' in line:
                            if 'No high-confidence' in line:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] No trade setup yet. Waiting...")
                            else:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")
                                
                        # Print balance updates
                        elif 'Balance:' in line:
                            print(f"💰 {line}")
                            
            # Check every 10 seconds
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\nMonitor stopped")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    log_monitor()
