# Auto-Alert System - ASCII Version (No Unicode)
import time
from datetime import datetime

def send_alert(update_type, details):
    """Send alert without unicode"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("\n" + "="*70)
    print(f"ALERT: {update_type}")
    print("="*70)
    print(f"Time: {timestamp}")
    print(details)
    print("="*70 + "\n")

def demo_alerts():
    """Show what alerts look like"""
    
    # Alert 1
    send_alert("MARKET SCAN UPDATE", """
Balance: $50.00 USDT
Positions: 0 Open

PAIR ANALYSIS:
  BTC/USDT: $78,364 | RSI: 39.8 | Score: 40/100 | WATCHING
  ETH/USDT: $2,315  | RSI: 36.3 | Score: 50/100 | WATCHING  
  SOL/USDT: $103    | RSI: 38.6 | Score: 40/100 | WATCHING
  XRP/USDT: $1.61   | RSI: 39.8 | Score: 40/100 | WATCHING

ACTION: WAITING FOR SETUP
Need: RSI <30, Near lower BB, EMA up

Next scan: 5 minutes
""")
    
    time.sleep(1)
    
    # Alert 2
    send_alert("POSITION OPENED - TRADE EXECUTED!", """
BUY SIGNAL TRIGGERED!

Pair: BTC/USDT
Entry Price: $72,500.00
Amount: 0.000165 BTC ($12.00)
Stop Loss: $69,600.00 (-4%)
Take Profit: $78,300.00 (+8%)
Confidence: 75/100

TRADE DETAILS:
• Risk: $0.48 (4% of position)
• Reward: $0.96 (8% of position)
• Risk/Reward: 1:2

Position will auto-close at stop or target.
""")
    
    time.sleep(1)
    
    # Alert 3
    send_alert("POSITION CLOSED - TRADE COMPLETE!", """
BTC/USDT POSITION CLOSED

Entry: $72,500.00
Exit: $78,300.00
PnL: +$0.96 (+8%)
Reason: TAKE PROFIT HIT!

Winner! Target reached.

Performance:
• Total Trades: 1
• Win Rate: 100%
• Daily PnL: +$0.96

Balance updated: $50.96
""")

if __name__ == "__main__":
    print("Demo of alert system (ASCII version)")
    print("In production, these send to Telegram instantly\n")
    demo_alerts()
