import os
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv('.env.bybit')
s = HTTP(api_key=os.getenv('BYBIT_API_KEY'), api_secret=os.getenv('BYBIT_API_SECRET'))

tickers = ['SOLUSDT', 'NEARUSDT', 'XRPUSDT', 'DOGEUSDT', 'ETHUSDT']
for sym in tickers:
    r = s.get_tickers(category='linear', symbol=sym)
    if r['retCode'] == 0:
        t = r['result']['list'][0]
        print(f"{sym}: ${t['lastPrice']} ({float(t['price24hPcnt'])*100:+.1f}%)")
