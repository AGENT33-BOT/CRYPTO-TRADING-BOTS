# Telegram Alert System for Crypto Trading
# Sends automatic alerts for every update

import requests
import time
import json
from datetime import datetime

# Telegram Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"  # We'll need to set this up
CHAT_ID = "5804173449"  # Your Telegram ID

def send_alert(message):
    """Send alert to Telegram"""
    try:
        # For now, just print (will integrate with actual bot later)
        print(f"\n{'='*70}")
        print(f"TELEGRAM ALERT - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        print(message)
        print(f"{'='*70}\n")
        return True
    except Exception as e:
        print(f"Alert error: {e}")
        return False

def alert_scan_summary(pairs_data):
    """Alert after every market scan"""
    message = f"""
🔍 <b>MARKET SCAN COMPLETE</b>

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 Balance: $50.00 USDT
📊 Positions: 0 Open

<b>PAIR STATUS:</b>
"""
    for pair, data in pairs_data.items():
        status_emoji = "🟢" if data['score'] >= 60 else "🟡" if data['score'] >= 40 else "🔴"
        message += f"\n{status_emoji} <b>{pair}</b>"
        message += f"\n   Price: ${data['price']:,.2f}"
        message += f"\n   RSI: {data['rsi']:.1f} {'📉 OVERSOLD!' if data['rsi'] < 30 else ''}"
        message += f"\n   Score: {data['score']}/100 - {data['status']}"
    
    message += f"""

<b>ACTION:</b> {"🟢 READY TO TRADE!" if any(d['score'] >= 60 for d in pairs_data.values()) else "⏳ WAITING FOR SETUP"}

Next scan in: 5 minutes
"""
    send_alert(message)

def alert_position_opened(symbol, entry, amount, stop_loss, take_profit, score):
    """Alert when position opened"""
    message = f"""
🟢 <b>POSITION OPENED - EXECUTED TRADE!</b>

⏰ Time: {datetime.now().strftime('%H:%M:%S')}
💱 Pair: <code>{symbol}</code>
💵 Entry: ${entry:,.2f}
📊 Amount: {amount:.6f}
🛑 Stop Loss: ${stop_loss:,.2f} ({-4:.0f}%)
🎯 Take Profit: ${take_profit:,.2f} (+{8:.0f}%)
⭐ Confidence Score: {score}/100

<b>Risk Management:</b>
• Risk: 4% (${amount * entry * 0.04:.2f})
• Reward: 8% (${amount * entry * 0.08:.2f})
• Risk/Reward: 1:2

Position will auto-close at stop or target.
"""
    send_alert(message)

def alert_position_closed(symbol, entry, exit_price, pnl, reason, win_rate):
    """Alert when position closed"""
    profit_emoji = "🟢" if pnl > 0 else "🔴"
    profit_text = f"+${pnl:.2f}" if pnl > 0 else f"-${abs(pnl):.2f}"
    
    message = f"""
{profit_emoji} <b>POSITION CLOSED - TRADE COMPLETE!</b>

⏰ Time: {datetime.now().strftime('%H:%M:%S')}
💱 Pair: <code>{symbol}</code>
📈 Entry: ${entry:,.2f}
📉 Exit: ${exit_price:,.2f}
💰 PnL: <b>{profit_text}</b>
📋 Reason: {reason}

<b>Performance:</b>
• Total Trades: Updated
• Win Rate: {win_rate:.1f}%
• Daily PnL: Updated

{'✅ Winner! Great setup execution.' if pnl > 0 else '❌ Stop loss hit. Protecting capital.'}
"""
    send_alert(message)

def alert_daily_summary(balance, daily_pnl, total_trades, win_rate, open_positions):
    """Daily summary alert"""
    pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
    pnl_text = f"+${daily_pnl:.2f}" if daily_pnl >= 0 else f"-${abs(daily_pnl):.2f}"
    
    message = f"""
{pnl_emoji} <b>DAILY TRADING SUMMARY</b>

📅 Date: {datetime.now().strftime('%Y-%m-%d')}
💰 Current Balance: ${balance:.2f}
📊 Daily PnL: <b>{pnl_text}</b>
📈 Total Trades: {total_trades}
🎯 Win Rate: {win_rate:.1f}%
📂 Open Positions: {open_positions}

<b>24h Activity:</b>
• Scans Completed: ~288
• Opportunities Found: Variable
• Trades Executed: {total_trades}

{'✅ Profitable day!' if daily_pnl > 0 else '⏳ Building for tomorrow.' if daily_pnl == 0 else '⚠️ Protecting capital.'}
"""
    send_alert(message)

def alert_waiting_status(what_we_need):
    """Alert explaining what we're waiting for"""
    message = f"""
⏳ <b>WAITING FOR TRADE SETUP</b>

Current Market: Stable/Neutral
Action: Holding $50 USDT

<b>NEED THESE CONDITIONS:</b>

1️⃣ RSI Below 30 (Oversold)
   Current: ~37-40 ❌
   ➜ Need: Panic selling

2️⃣ Near Lower Bollinger Band (<20%)
   Current: ~40-48% ❌
   ➜ Need: Price at support

3️⃣ EMA Uptrend (9 > 21)
   Current: Down ❌
   ➜ Need: Trend reversal

4️⃣ Score >= 60/100
   Current: 40-50 ❌
   ➜ Need: All stars align

<b>WHEN THIS HAPPENS:</b>
🟢 INSTANT BUY ALERT
🤖 AUTO-EXECUTE TRADE
📱 YOU GET NOTIFIED

<b>Patience = Profits</b>
Only buying fear, not greed.
"""
    send_alert(message)

# Test alerts
if __name__ == "__main__":
    print("Testing alert system...")
    
    # Test scan summary
    test_data = {
        'BTC/USDT': {'price': 78364, 'rsi': 39.8, 'score': 40, 'status': 'WATCHING'},
        'ETH/USDT': {'price': 2315, 'rsi': 36.3, 'score': 50, 'status': 'WATCHING'},
        'SOL/USDT': {'price': 103, 'rsi': 38.6, 'score': 40, 'status': 'WATCHING'},
        'XRP/USDT': {'price': 1.61, 'rsi': 39.8, 'score': 40, 'status': 'WATCHING'}
    }
    
    alert_scan_summary(test_data)
