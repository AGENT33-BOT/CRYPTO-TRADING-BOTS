import sys
sys.path.insert(0, r'C:\Users\digim\clawd\crypto_trader')
from config import get_exchange
import asyncio

async def quick_pnl():
    ex = await get_exchange()
    positions = await ex.fetch_positions()
    print(f'=== POSITIONS: {len(positions)} ===')
    total_pnl = 0
    for p in positions:
        if float(p.get('contracts', 0)) != 0:
            symbol = p['symbol']
            side = p['side']
            contracts = float(p['contracts'])
            entry = float(p['entryPrice'])
            pnl = float(p['unrealizedPnl'])
            mark = float(p['markPrice'])
            total_pnl += pnl
            print(f'{symbol} {side.upper()}: {contracts} @ ${entry:.4f} | Mark: ${mark:.4f} | P&L: ${pnl:.2f}')
    print(f'=== TOTAL UNREALIZED P&L: ${total_pnl:.2f} ===')
    await ex.close()

asyncio.run(quick_pnl())