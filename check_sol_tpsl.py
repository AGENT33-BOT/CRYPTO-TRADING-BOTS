import ccxt
import os
from dotenv import load_dotenv
load_dotenv()

bybit = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_SECRET'),
    'testnet': False
})

# Check SOL position
pos = bybit.fetch_position('SOL/USDT:USDT')
print(f'Symbol: {pos["symbol"]}')
print(f'Side: {pos["side"]}')
print(f'Entry: {pos["entryPrice"]}')
print(f'Size: {pos["contracts"]}')
print(f'TP: {pos.get("takeProfit", "NOT SET")}')
print(f'SL: {pos.get("stopLoss", "NOT SET")}')
