# Real-time Market Monitor with Detailed Alerts
import ccxt
import pandas as pd
import numpy as np
import talib
import time
from datetime import datetime

API_KEY = "bsK06QDhsagOWwFsXQ"
API_SECRET = "ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa"

def get_exchange():
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    exchange.load_markets()
    return exchange

def analyze_detailed(symbol, exchange):
    """Detailed analysis with reasons"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '4h', limit=50)
        if len(ohlcv) < 30:
            return None
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        current_price = closes[-1]
        
        # RSI
        rsi = talib.RSI(closes, timeperiod=14)[-1]
        
        # MACD
        macd, macdsignal, macdhist = talib.MACD(closes)
        macd_val = macd[-1]
        macd_sig = macdsignal[-1]
        macd_hist = macdhist[-1]
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(closes, timeperiod=20)
        bb_upper = upper[-1]
        bb_lower = lower[-1]
        bb_middle = middle[-1]
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        
        # EMAs
        ema_9 = talib.EMA(closes, timeperiod=9)[-1]
        ema_21 = talib.EMA(closes, timeperiod=21)[-1]
        
        # Calculate score
        score = 0
        reasons = []
        waiting_for = []
        
        # RSI Analysis
        if rsi < 30:
            score += 25
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 70:
            score -= 25
            waiting_for.append(f"RSI to cool down from {rsi:.1f}")
        elif 30 <= rsi <= 40:
            score += 15
            reasons.append(f"RSI approaching oversold ({rsi:.1f})")
            waiting_for.append(f"RSI below 30 for entry")
        else:
            waiting_for.append(f"RSI below 40 (currently {rsi:.1f})")
        
        # MACD Analysis
        if macd_val > macd_sig and macd_hist > 0:
            score += 25
            reasons.append("MACD bullish crossover")
        elif macd_val < macd_sig:
            score -= 15
            waiting_for.append("MACD bullish crossover")
        else:
            waiting_for.append("MACD to turn bullish")
        
        # Bollinger Bands
        if bb_position < 0.2:
            score += 20
            reasons.append(f"Price near lower BB ({bb_position:.1%})")
        elif bb_position > 0.8:
            score -= 20
            waiting_for.append("Price to come down from upper BB")
        elif bb_position < 0.4:
            score += 10
            waiting_for.append("Price closer to lower BB")
        else:
            waiting_for.append(f"Price position {bb_position:.1%} (want <20%)")
        
        # EMA Trend
        if ema_9 > ema_21:
            score += 15
            reasons.append("EMA bullish (9 > 21)")
        else:
            waiting_for.append("EMA 9 to cross above 21")
        
        # Determine status
        if score >= 60:
            status = "READY TO BUY"
            action = "EXECUTE TRADE"
        elif score >= 40:
            status = "WATCHING"
            action = "WAITING FOR CONFIRMATION"
        else:
            status = "HOLDING"
            action = "NO SETUP"
        
        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'macd': macd_val,
            'macd_signal': macd_sig,
            'macd_hist': macd_hist,
            'bb_lower': bb_lower,
            'bb_upper': bb_upper,
            'bb_position': bb_position,
            'ema_9': ema_9,
            'ema_21': ema_21,
            'score': score,
            'status': status,
            'action': action,
            'reasons': reasons,
            'waiting_for': waiting_for
        }
        
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}

def print_monitoring_report():
    """Print detailed monitoring report"""
    exchange = get_exchange()
    pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
    
    print("=" * 70)
    print(f"MARKET MONITORING REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    for pair in pairs:
        analysis = analyze_detailed(pair, exchange)
        if not analysis:
            continue
        
        if 'error' in analysis:
            print(f"{pair}: ERROR - {analysis['error']}")
            continue
        
        print(f"\n{'='*70}")
        print(f"PAIR: {pair}")
        print(f"{'='*70}")
        print(f"Price: ${analysis['price']:,.2f}")
        print(f"Status: {analysis['status']} (Score: {analysis['score']}/100)")
        print(f"Action: {analysis['action']}")
        print()
        print("INDICATORS:")
        print(f"  RSI: {analysis['rsi']:.1f} (want <30, have {analysis['rsi']:.1f})")
        print(f"  MACD: {analysis['macd']:.4f} (Signal: {analysis['macd_signal']:.4f})")
        print(f"  BB Position: {analysis['bb_position']:.1%} (want <20%)")
        print(f"  EMA: 9={analysis['ema_9']:.2f}, 21={analysis['ema_21']:.2f}")
        print()
        
        if analysis['reasons']:
            print("POSITIVE SIGNALS:")
            for reason in analysis['reasons']:
                print(f"  + {reason}")
        
        if analysis['waiting_for']:
            print("\nWAITING FOR:")
            for item in analysis['waiting_for']:
                print(f"  - {item}")
        
        print()
    
    print("=" * 70)
    print("SUMMARY:")
    print("=" * 70)
    print("We need ALL these conditions for a trade:")
    print("  1. RSI below 30 (oversold)")
    print("  2. MACD bullish crossover")
    print("  3. Price near lower Bollinger Band (<20%)")
    print("  4. EMA 9 above EMA 21 (uptrend)")
    print("  5. Minimum score: 60/100")
    print()
    print("Current: Monitoring all pairs every 5 minutes")
    print("Next scan in: ~5 minutes")
    print("=" * 70)

if __name__ == "__main__":
    while True:
        print_monitoring_report()
        print("\n" + "="*70)
        print("Waiting 5 minutes for next update...")
        print("="*70 + "\n")
        time.sleep(300)
