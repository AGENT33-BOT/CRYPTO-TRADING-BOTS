"""
AGGRESSIVE Signal Scanner - Runs every 15 seconds
Reports any 75%+ confidence signals immediately
"""

import ccxt
import time
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

PAIRS = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
]

MIN_CONFIDENCE = 75  # AGGRESSIVE: Lowered from 80%
SCAN_INTERVAL = 15   # AGGRESSIVE: 15 seconds (was 30)

print("=" * 70)
print("AGGRESSIVE SIGNAL SCANNER - 75%+ CONFIDENCE")
print("Scanning every 15 seconds - Press Ctrl+C to stop")
print("=" * 70)

signal_count = 0
scan_count = 0

try:
    while True:
        scan_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        signals_found = []
        
        for symbol in PAIRS:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=50)
                if len(ohlcv) < 30:
                    continue
                
                closes = [c[4] for c in ohlcv]
                highs = [c[2] for c in ohlcv]
                lows = [c[3] for c in ohlcv]
                current = closes[-1]
                
                # RSI
                gains = []
                losses = []
                for i in range(1, 15):
                    change = closes[-i] - closes[-(i+1)]
                    gains.append(max(change, 0))
                    losses.append(abs(min(change, 0)))
                
                avg_gain = sum(gains) / 14
                avg_loss = sum(losses) / 14
                rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))
                
                # Trend
                sma20 = sum(closes[-20:]) / 20
                sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma20
                
                # Support/Resistance
                support = sorted(lows[-20:], reverse=True)[:3]
                resistance = sorted(highs[-20:])[:3]
                
                # Signals
                if rsi < 65 and rsi > 40 and current > sma20:
                    if support and abs(current - max(support)) / current < 0.01:
                        confidence = 75 + (65 - rsi) * 0.5
                        if confidence >= MIN_CONFIDENCE:
                            signals_found.append({
                                'symbol': symbol.replace('/USDT:USDT', ''),
                                'signal': 'LONG',
                                'confidence': min(confidence, 99),
                                'price': current,
                                'rsi': rsi
                            })
                
                elif rsi > 35 and rsi < 60 and current < sma50:
                    if resistance and abs(min(resistance) - current) / current < 0.01:
                        confidence = 75 + (rsi - 35) * 0.5
                        if confidence >= MIN_CONFIDENCE:
                            signals_found.append({
                                'symbol': symbol.replace('/USDT:USDT', ''),
                                'signal': 'SHORT',
                                'confidence': min(confidence, 99),
                                'price': current,
                                'rsi': rsi
                            })
                            
            except Exception as e:
                pass
        
        # Report
        if signals_found:
            signal_count += len(signals_found)
            signals_found.sort(key=lambda x: x['confidence'], reverse=True)
            
            print(f"\n[{timestamp}] SCAN #{scan_count} - SIGNALS FOUND!")
            print("=" * 70)
            for sig in signals_found:
                print(f"🎯 {sig['symbol']} {sig['signal']} - {sig['confidence']:.1f}% confidence")
                print(f"   Price: ${sig['price']:.4f} | RSI: {sig['rsi']:.1f}")
            print("=" * 70)
            print("Auto-trader will execute highest confidence signal!")
            
        else:
            if scan_count % 20 == 0:  # Print status every 20 scans (5 minutes)
                print(f"[{timestamp}] Scan #{scan_count} - No 75%+ signals (monitoring...)")
        
        time.sleep(SCAN_INTERVAL)
        
except KeyboardInterrupt:
    print(f"\n\nMonitoring stopped.")
    print(f"Total scans: {scan_count} | Signals found: {signal_count}")
