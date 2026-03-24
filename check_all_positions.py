#!/usr/bin/env python3
import ccxt.async_support as ccxt
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def check_all():
    # Check main Bybit account
    print('=== BYBIT (Main) ===')
    exchange = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY', ''),
        'secret': os.getenv('BYBIT_API_SECRET', ''),
        'options': {'defaultType': 'linear'},
    })
    try:
        positions = await exchange.fetch_positions(None, {'category': 'linear'})
        open_pos = [p for p in positions if p.get('contracts', 0) != 0]
        print(f'Linear positions: {len(open_pos)}')
        for p in open_pos:
            tp = p.get('takeProfit', 'N/A') or 'N/A'
            sl = p.get('stopLoss', 'N/A') or 'N/A'
            print(f"  {p['symbol']} {p['side']} | Entry: {p.get('entryPrice', 'N/A')} | TP: {tp} | SL: {sl}")
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await exchange.close()
    
    # Check Bybit2 account
    print('\n=== BYBIT2 ===')
    exchange2 = ccxt.bybit({
        'apiKey': os.getenv('BYBIT_API_KEY_2', ''),
        'secret': os.getenv('BYBIT_API_SECRET_2', ''),
        'options': {'defaultType': 'linear'},
    })
    try:
        positions = await exchange2.fetch_positions(None, {'category': 'linear'})
        open_pos = [p for p in positions if p.get('contracts', 0) != 0]
        print(f'Linear positions: {len(open_pos)}')
        for p in open_pos:
            tp = p.get('takeProfit', 'N/A') or 'N/A'
            sl = p.get('stopLoss', 'N/A') or 'N/A'
            print(f"  {p['symbol']} {p['side']} | Entry: {p.get('entryPrice', 'N/A')} | TP: {tp} | SL: {sl}")
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await exchange2.close()

asyncio.run(check_all())
