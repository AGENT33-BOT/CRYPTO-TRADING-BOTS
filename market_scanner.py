"""
BOSS33 Market Opportunity Scanner
Scans multiple pairs for trend-following entries
Created: 2026-02-05
"""

import ccxt
import time
import json
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Watchlist
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT']
CHECK_INTERVAL = 60  # Check every 60 seconds

class OpportunityScanner:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.exchange.load_markets()
        self.signals_found = []
        
    def analyze_trend(self, symbol):
        """Analyze trend for a symbol"""
        try:
            # Fetch OHLCV (15min candles)
            ohlcv = self.exchange.fetch_ohlcv(symbol, '15m', limit=30)
            
            if not ohlcv or len(ohlcv) < 20:
                return None
            
            # Calculate indicators
            closes = [c[4] for c in ohlcv]
            highs = [c[2] for c in ohlcv]
            lows = [c[3] for c in ohlcv]
            volumes = [c[5] for c in ohlcv]
            
            current_price = closes[-1]
            
            # Simple EMA
            ema_short = sum(closes[-9:]) / 9
            ema_long = sum(closes[-21:]) / 21
            
            # RSI calculation
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d for d in deltas if d > 0]
            losses = [-d for d in deltas if d < 0]
            
            avg_gain = sum(gains[-14:]) / 14 if gains else 0
            avg_loss = sum(losses[-14:]) / 14 if losses else 0.001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Volume trend
            recent_vol = sum(volumes[-5:]) / 5
            older_vol = sum(volumes[-10:-5]) / 5
            volume_increasing = recent_vol > older_vol * 1.2
            
            # Determine trend
            bullish_score = 0
            bearish_score = 0
            
            # Price vs EMAs
            if current_price > ema_short > ema_long:
                bullish_score += 2
            elif current_price < ema_short < ema_long:
                bearish_score += 2
            
            # RSI
            if 40 < rsi < 65:
                bullish_score += 1
            elif 35 < rsi < 50:
                bearish_score += 1
            
            # Volume
            if volume_increasing:
                if bullish_score > bearish_score:
                    bullish_score += 1
                elif bearish_score > bullish_score:
                    bearish_score += 1
            
            # Trend direction
            if bullish_score >= 3 and rsi < 60:
                return {
                    'symbol': symbol,
                    'direction': 'LONG',
                    'strength': bullish_score,
                    'price': current_price,
                    'rsi': rsi,
                    'ema_short': ema_short,
                    'ema_long': ema_long
                }
            elif bearish_score >= 3 and rsi > 40:
                return {
                    'symbol': symbol,
                    'direction': 'SHORT',
                    'strength': bearish_score,
                    'price': current_price,
                    'rsi': rsi,
                    'ema_short': ema_short,
                    'ema_long': ema_long
                }
            
            return None
            
        except Exception as e:
            return None
    
    def scan_all(self):
        """Scan all symbols for opportunities"""
        print(f"\n{'='*60}")
        print(f"Market Scanner - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        opportunities = []
        
        for symbol in SYMBOLS:
            result = self.analyze_trend(symbol)
            if result and result['strength'] >= 3:
                opportunities.append(result)
                
                direction = result['direction']
                strength = result['strength']
                price = result['price']
                rsi = result['rsi']
                
                icon = "🟢" if direction == 'LONG' else "🔴"
                print(f"{icon} {symbol}: {direction} (Strength: {strength}/5)")
                print(f"   Price: ${price:,.4f} | RSI: {rsi:.1f}")
                
                # Calculate potential entry
                if direction == 'LONG':
                    entry = price
                    sl = entry * 0.98  # 2% stop
                    tp = entry * 1.04  # 4% target
                else:
                    entry = price
                    sl = entry * 1.02  # 2% stop
                    tp = entry * 0.96  # 4% target
                
                print(f"   Suggested: Entry ${entry:,.2f} | SL ${sl:,.2f} | TP ${tp:,.2f}")
                print()
        
        if not opportunities:
            print("No high-quality opportunities found.")
            print("Market still unstable or no clear trends.")
        else:
            # Save opportunities
            with open('opportunities_log.json', 'a') as f:
                for opp in opportunities:
                    opp['time'] = datetime.now().isoformat()
                    f.write(json.dumps(opp) + '\n')
            
            # Alert if new high-quality opportunity
            best = max(opportunities, key=lambda x: x['strength'])
            if best['strength'] >= 4 and best['symbol'] not in [s['symbol'] for s in self.signals_found]:
                print(f"\n{'!'*60}")
                print(f"🎯 HIGH QUALITY OPPORTUNITY DETECTED!")
                print(f"   {best['symbol']} {best['direction']}")
                print(f"   Strength: {best['strength']}/5")
                print(f"   Price: ${best['price']:,.4f}")
                print(f"\n   Reply 'OPEN {best['symbol']}' to enter!")
                print(f"{'!'*60}\n")
                self.signals_found.append(best)
        
        return opportunities
    
    def run(self):
        print("="*60)
        print("BOSS33 Market Opportunity Scanner")
        print("="*60)
        print("\nMonitoring: BTC, ETH, SOL, ADA, DOGE")
        print("Strategy: Trend-following only")
        print("Requirement: Strength 3+/5 to alert")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_all()
                print(f"\nNext scan in {CHECK_INTERVAL} seconds...\n")
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\nScanner stopped.")

if __name__ == '__main__':
    scanner = OpportunityScanner()
    scanner.run()
