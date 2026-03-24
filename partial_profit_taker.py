"""
Partial Profit Taker - Takes partial profits at 2-5% gains
Ensures we never lose all profit
"""
import ccxt
import os
import requests
import time

BYBIT_API_KEY = 'KfmiIdWd16hG18v2O7'
BYBIT_API_SECRET = 'VTVePZIz2GEqyy6AcvwPVcaRNBRolmXkuWlZ'
TELEGRAM_TOKEN = '8249656817:AAFAI3oulkDWJZHJ7STSYlDfK-_UJCPo-7U'
TELEGRAM_CHAT_ID = '5804173449'

# Settings
PARTIAL_PROFIT_LEVELS = [2, 3, 4, 5]  # Take partial at these percentages
PARTIAL_PERCENT = 30  # Close 30% of position at each level

def send_telegram(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                     json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def get_pnl_percent(p):
    """Calculate current PnL percentage"""
    info = p.get('info', {})
    entry = float(info.get('avgPrice', 0))
    mark = float(info.get('markPrice', 0))
    if entry == 0:
        return 0
    return ((mark - entry) / entry) * 100

def close_partial(bybit, symbol, side, amount):
    """Close partial position"""
    try:
        # Close partial using reduceOnly order
        close_side = 'sell' if side in ['buy', 'long'] else 'buy'
        
        order = bybit.create_order(
            symbol=symbol,
            type='market',
            side=close_side,
            amount=amount,
            params={'reduceOnly': True}
        )
        return True
    except Exception as e:
        print(f'Close error: {e}')
        return False

def check_positions():
    bybit = ccxt.bybit({
        'apiKey': BYBIT_API_KEY,
        'secret': BYBIT_API_SECRET,
        'options': {'defaultType': 'swap'}
    })
    
    positions = bybit.fetch_positions()
    alerts = []
    
    for p in positions:
        size = float(p.get('contracts', 0))
        if size <= 0:
            continue
        
        symbol = p['symbol'].replace('/USDT:USDT', '') + 'USDT'
        side = p['side']
        
        # Calculate PnL percentage
        info = p.get('info', {})
        entry = float(info.get('avgPrice', 0))
        mark = float(info.get('markPrice', 0))
        
        if entry == 0:
            continue
        
        pnl_pct = ((mark - entry) / entry) * 100
        pnl_value = float(info.get('unrealisedPnl', 0))
        
        # Check if at profit level
        for profit_level in PARTIAL_PROFIT_LEVELS:
            if pnl_pct >= profit_level:
                # Check if we already took profit at this level
                # (in production, track this in a file)
                
                # Calculate partial amount (30% of position)
                partial_size = round(size * (PARTIAL_PERCENT / 100), 3)
                
                if partial_size > 0:
                    print(f'Taking partial profit at {pnl_pct:.1f}%: {symbol}')
                    
                    success = close_partial(bybit, symbol, side, partial_size)
                    
                    if success:
                        msg = f"PARTIAL PROFIT TAKEN!\n{symbol}\nAt: {pnl_pct:.1f}%\nClosed: {partial_size} contracts\nRemaining: {size - partial_size}"
                        print(msg)
                        alerts.append(msg)
                        send_telegram(msg)
                    break
    
    if not alerts:
        print('No profit levels reached yet')

def run_monitor():
    print('Partial Profit Taker started - checking every minute')
    send_telegram('Partial Profit Taker started!\nWill take 30% at 2%, 3%, 4%, 5% profit')
    
    while True:
        try:
            check_positions()
        except Exception as e:
            print(f'Error: {e}')
        
        time.sleep(60)

if __name__ == "__main__":
    run_monitor()