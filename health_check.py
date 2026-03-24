"""
Health Check Script for Agent33 Trading System
Quick diagnostic of all system components.
"""

import subprocess
import json
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

BOT_SCRIPTS = [
    ('Grid Trading Bot', 'grid_trader.py'),
    ('Funding Arbitrage Bot', 'funding_arbitrage.py'),
    ('Mean Reversion Bot', 'mean_reversion_trader.py'),
    ('Momentum Bot', 'momentum_trader.py'),
    ('Scalping Bot', 'scalping_bot.py'),
    ('Auto Position Opener', 'auto_position_opener.py'),
]


def check_process(script_name):
    """Check if a Python process is running"""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             f'Get-Process python -ErrorAction SilentlyContinue | Where-Object {{ $_.CommandLine -like "*{script_name}*" }} | Select-Object -First 1 Id'],
            capture_output=True, text=True
        )
        output = result.stdout.strip()
        if output and output.isdigit():
            return int(output)
        return None
    except Exception:
        return None


def check_api_connectivity():
    """Check if Bybit API is accessible"""
    try:
        import ccxt
        from dotenv import load_dotenv
        load_dotenv('.env.bybit')
        
        exchange = ccxt.bybit({
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
        })
        exchange.load_markets()
        return True, "Connected"
    except Exception as e:
        return False, str(e)


def get_positions_summary():
    """Get summary of open positions"""
    try:
        import ccxt
        from dotenv import load_dotenv
        load_dotenv('.env.bybit')
        
        exchange = ccxt.bybit({
            'apiKey': os.getenv('BYBIT_API_KEY'),
            'secret': os.getenv('BYBIT_API_SECRET'),
            'options': {'defaultType': 'swap'}
        })
        
        positions = exchange.fetch_positions()
        active = [p for p in positions if float(p.get('contracts', 0)) > 0]
        
        total_pnl = sum(float(p.get('unrealisedPnl', 0)) for p in active)
        
        return {
            'count': len(active),
            'total_pnl': total_pnl,
            'positions': active
        }
    except Exception as e:
        return {'count': 0, 'total_pnl': 0, 'positions': [], 'error': str(e)}


def main():
    print("=" * 60)
    print("AGENT33 TRADING SYSTEM - HEALTH CHECK")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ET")
    print("=" * 60)
    print()
    
    # Check bot processes
    print("🤖 BOT STATUS")
    print("-" * 40)
    all_running = True
    bot_status = []
    
    for name, script in BOT_SCRIPTS:
        pid = check_process(script)
        if pid:
            print(f"✅ {name}: RUNNING (PID {pid})")
            bot_status.append((name, True, pid))
        else:
            print(f"❌ {name}: STOPPED")
            bot_status.append((name, False, None))
            all_running = False
    
    print()
    
    # Check API
    print("🔌 API CONNECTIVITY")
    print("-" * 40)
    api_ok, api_msg = check_api_connectivity()
    if api_ok:
        print(f"✅ Bybit API: {api_msg}")
    else:
        print(f"❌ Bybit API: {api_msg}")
    
    print()
    
    # Check positions
    print("📊 POSITIONS")
    print("-" * 40)
    pos_summary = get_positions_summary()
    
    if 'error' in pos_summary:
        print(f"❌ Error: {pos_summary['error']}")
    else:
        print(f"Active Positions: {pos_summary['count']}")
        print(f"Total Unrealized P&L: ${pos_summary['total_pnl']:.2f}")
        
        for p in pos_summary['positions'][:5]:
            symbol = p['symbol']
            side = p['side']
            pnl = float(p.get('unrealisedPnl', 0))
            status = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            print(f"  {status} {symbol} {side}: ${pnl:+.2f}")
    
    print()
    
    # Overall status
    print("=" * 60)
    if all_running and api_ok:
        print("✅ OVERALL: ALL SYSTEMS OPERATIONAL")
    elif not all_running:
        print("⚠️  OVERALL: SOME BOTS STOPPED")
    else:
        print("❌ OVERALL: API CONNECTIVITY ISSUE")
    print("=" * 60)
    
    # Return summary for programmatic use
    return {
        'timestamp': datetime.now().isoformat(),
        'bots_running': all_running,
        'bot_status': bot_status,
        'api_ok': api_ok,
        'positions': pos_summary
    }


if __name__ == "__main__":
    result = main()
    
    # Save to file for other scripts
    with open('health_check_result.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
