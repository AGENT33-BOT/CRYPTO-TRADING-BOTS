import os
from pathlib import Path
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env.bybit'
load_dotenv(ENV_PATH)

session = HTTP(
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_API_SECRET'),
    testnet=False
)

# Get ETH price
eth_ticker = session.get_tickers(category="linear", symbol="ETHUSDT")
eth_price = float(eth_ticker['result']['list'][0]['lastPrice'])
print(f"ETH price: ${eth_price}")

# Get SOL price
sol_ticker = session.get_tickers(category="linear", symbol="SOLUSDT")
sol_price = float(sol_ticker['result']['list'][0]['lastPrice'])
print(f"SOL price: ${sol_price}")

# Open ETH LONG
eth_order = session.place_order(
    category="linear",
    symbol="ETHUSDT",
    side="Buy",
    orderType="Market",
    qty="0.04"
)
print(f"ETH order: {eth_order}")

# Open SOL LONG
sol_order = session.place_order(
    category="linear",
    symbol="SOLUSDT",
    side="Buy",
    orderType="Market",
    qty="0.1"
)
print(f"SOL order: {sol_order}")
