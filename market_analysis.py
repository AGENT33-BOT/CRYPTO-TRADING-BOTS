from pybit.unified_trading import HTTP
import ccxt
import pandas as pd

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

print("MARKET ANALYSIS — FINDING OPPORTUNITY")
print("=" * 60)

# Get tickers for major pairs
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'NEARUSDT']

print("\nCurrent Prices & 24h Change:")
print("-" * 60)

market_bias = []

for sym in symbols:
    try:
        ticker = session.get_tickers(category='linear', symbol=sym)
        data = ticker['result']['list'][0]
        price = float(data['lastPrice'])
        change = float(data['price24hPcnt']) * 100
        volume = float(data['turnover24h'])
        
        direction = "UP" if change > 0 else "DOWN"
        market_bias.append(change)
        
        print(f"{sym:<12} ${price:>10.2f} | {change:+.2f}% | {direction} | Vol: ${volume/1e6:.1f}M")
    except:
        pass

# Market bias
avg_change = sum(market_bias) / len(market_bias) if market_bias else 0
print("\n" + "=" * 60)
print(f"MARKET BIAS: {avg_change:+.2f}% (Avg 24h change)")

if avg_change > 2:
    print("TREND: STRONG BULLISH — Look for LONG entries on dips")
    rec = "LONG"
elif avg_change > 0.5:
    print("TREND: BULLISH — Consider LONG on pullbacks")
    rec = "LONG_ON_DIP"
elif avg_change < -2:
    print("TREND: STRONG BEARISH — Look for SHORT entries on bounces")
    rec = "SHORT"
elif avg_change < -0.5:
    print("TREND: BEARISH — Consider SHORT on relief rallies")
    rec = "SHORT_ON_BOUNCE"
else:
    print("TREND: CHOPPY/NEUTRAL — Grid trading or scalp range")
    rec = "CHOP"

print(f"\nRECOMMENDATION: {rec}")

# Check funding rates for additional context
print("\n" + "=" * 60)
print("FUNDING RATES (Predicts sentiment):")
print("-" * 60)

try:
    funding = session.get_funding_rate(category='linear', symbol='BTCUSDT')
    btc_funding = float(funding['result']['list'][0]['fundingRate']) * 100
    print(f"BTC Funding: {btc_funding:.4f}% (Positive = Longs pay shorts)")
    
    if btc_funding > 0.01:
        print("→ High long interest — potential for squeeze")
    elif btc_funding < -0.01:
        print("→ High short interest — potential for short squeeze")
except:
    print("Could not fetch funding")

print("\n" + "=" * 60)
