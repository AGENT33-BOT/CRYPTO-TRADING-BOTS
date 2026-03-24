import asyncio
import sys
sys.path.insert(0, '.')
from bybit import bybit

async def check():
    b = bybit()
    w = await b.get_wallet_balance()
    print(f"Balance: {w}")
    
    # Get position info
    p = await b.get_positions()
    print(f"Positions: {p}")

asyncio.run(check())
