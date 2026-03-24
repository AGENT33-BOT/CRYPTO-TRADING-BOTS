from bybit_api import get_positions, close_position
import asyncio
import json

async def check_and_close():
    positions = await get_positions()
    print("Current positions:")
    print(json.dumps(positions, indent=2))
    
    # Look for SHORT positions to close
    for pos in positions.get('list', []):
        if pos.get('side') == 'Sell':  # SHORT
            symbol = pos.get('symbol')
            print(f"\n⚠️ Closing SHORT: {symbol}")
            result = await close_position(symbol.replace('USDT:USDT', ''), 'SHORT')
            print(f"Result: {result}")

asyncio.run(check_and_close())
