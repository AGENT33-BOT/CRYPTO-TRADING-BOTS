import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY

print('Testing data fetch...')
client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

request = StockBarsRequest(
    symbol_or_symbols='SPY',
    timeframe=TimeFrame.Day,
    limit=50
)

print('Fetching SPY data...')
bars = client.get_stock_bars(request)
print(f'Got {len(bars.df)} bars')
print(bars.df.head())
