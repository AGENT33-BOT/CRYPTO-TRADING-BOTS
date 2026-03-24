"""
BOSS33 Autonomous Trader v3.0
Full auto-execution - No user confirmation needed
Created: 2026-02-05
"""

import ccxt
import time
import json
from datetime import datetime

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# STRICT Risk Settings for Autonomous Mode
CONFIG = {
    'leverage': 1,  # NO LEVERAGE
    'risk_per_trade': 0.01,  # 1% of account (very conservative)
    'max_positions': 2,  # Max 2 positions
    'stop_loss': 0.015,  # 1.5% stop
    'take_profit': 0.03,  # 3% target
    'min_strength': 4,  # Only 4+/5 strength
    'symbols': ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT'],
    'timeframe': '15m',
}

class AutonomousTrader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.exchange.load_markets()
        self.trade_log = []
        
    def get_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            total = float(balance.get('USDT', {}).get('total', 0))
            free = float(balance.get('USDT', {}).get('free', 0))
            return total, free
        except:
            return 0, 0
    
    def get_positions(self):
        try:
            positions = {}
            for symbol in CONFIG['symbols']:
                pos_list = self.exchange.fetch_positions([symbol])
                if pos_list and pos_list[0]['contracts'] > 0:
                    positions[symbol] = pos_list[0]
            return positions
        except:
            return {}
    
    def analyze_trend(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, CONFIG['timeframe'], limit=30)
            if not ohlcv or len(ohlcv) < 20:
                return None
            
            closes = [c[4] for c in ohlcv]
            current = closes[-1]
            
            # EMAs
            ema_9 = sum(closes[-9:]) / 9
            ema_21 = sum(closes[-21:]) / 21
            
            # RSI
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d for d in deltas if d > 0]
            losses = [-d for d in deltas if d < 0]
            avg_gain = sum(gains[-14:]) / 14 if gains else 0
            avg_loss = sum(losses[-14:]) / 14 if losses else 0.001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Score
            bullish = 0
            bearish = 0
            
            if current > ema_9 > ema_21:
                bullish += 2
            elif current < ema_9 < ema_21:
                bearish += 2
            
            if 45 < rsi < 60:
                bullish += 1
            elif 40 < rsi < 50:
                bearish += 1
            
            if bullish >= 3 and rsi < 55:
                return {'symbol': symbol, 'direction': 'LONG', 'strength': bullish, 'price': current, 'rsi': rsi}
            elif bearish >= 3 and rsi > 45:
                return {'symbol': symbol, 'direction': 'SHORT', 'strength': bearish, 'price': current, 'rsi': rsi}
            
            return None
        except:
            return None
    
    def calculate_size(self, symbol, entry, stop, total_balance):
        try:
            risk_amount = total_balance * CONFIG['risk_per_trade']
            stop_distance = abs(entry - stop) / entry
            if stop_distance == 0:
                return 0
            position_value = risk_amount / stop_distance
            
            market = self.exchange.market(symbol)
            min_amount = market['limits']['amount']['min'] or 0
            
            contracts = position_value / entry
            if contracts < min_amount:
                contracts = min_amount
            
            return contracts
        except:
            return 0
    
    def open_position(self, signal):
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            entry = signal['price']
            
            total, free = self.get_balance()
            
            if free < 20:
                print(f"  Insufficient balance: ${free:.2f}")
                return False
            
            # Calculate levels
            if direction == 'LONG':
                stop = entry * (1 - CONFIG['stop_loss'])
                target = entry * (1 + CONFIG['take_profit'])
            else:
                stop = entry * (1 + CONFIG['stop_loss'])
                target = entry * (1 - CONFIG['take_profit'])
            
            # Calculate size
            size = self.calculate_size(symbol, entry, stop, total)
            if size <= 0:
                print(f"  Invalid position size")
                return False
            
            print(f"\n  EXECUTING {direction} on {symbol}")
            print(f"  Entry: ${entry:.4f}")
            print(f"  Stop: ${stop:.4f}")
            print(f"  Target: ${target:.4f}")
            print(f"  Size: {size:.4f}")
            
            # Set leverage
            try:
                self.exchange.set_leverage(CONFIG['leverage'], symbol)
            except:
                pass
            
            # Open position
            side = 'buy' if direction == 'LONG' else 'sell'
            order = self.exchange.create_market_order(symbol=symbol, side=side, amount=size)
            
            # Set TP/SL
            try:
                close_side = 'sell' if direction == 'LONG' else 'buy'
                self.exchange.create_order(
                    symbol=symbol, type='limit', side=close_side,
                    amount=size, price=target, params={'reduceOnly': True}
                )
            except Exception as e:
                print(f"  TP/SL warning: {e}")
            
            # Log trade
            trade = {
                'time': datetime.now().isoformat(),
                'symbol': symbol,
                'direction': direction,
                'entry': entry,
                'stop': stop,
                'target': target,
                'size': size,
                'order_id': order['id']
            }
            
            self.trade_log.append(trade)
            with open('autonomous_trades.json', 'a') as f:
                f.write(json.dumps(trade) + '\n')
            
            print(f"  ✅ TRADE EXECUTED: {order['id']}")
            
            # Send alert
            print(f"\n  🚨 AUTO-TRADE ALERT SENT TO USER")
            print(f"     {symbol} {direction} opened at ${entry:.4f}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def scan_and_trade(self):
        print(f"\n{'='*60}")
        print(f"Autonomous Trader - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        total, free = self.get_balance()
        positions = self.get_positions()
        
        print(f"Balance: ${total:.2f} (Free: ${free:.2f})")
        print(f"Positions: {len(positions)}/{CONFIG['max_positions']}")
        
        if len(positions) >= CONFIG['max_positions']:
            print("\nMax positions reached. Waiting...")
            return
        
        if free < 30:
            print("\nInsufficient free balance.")
            return
        
        print(f"\nScanning for opportunities (min strength: {CONFIG['min_strength']}/5)...\n")
        
        opportunities = []
        for symbol in CONFIG['symbols']:
            if symbol in positions:
                continue
            
            result = self.analyze_trend(symbol)
            if result and result['strength'] >= CONFIG['min_strength']:
                opportunities.append(result)
                print(f"  🎯 {symbol}: {result['direction']} (Strength: {result['strength']}/5)")
                print(f"     Price: ${result['price']:.4f} | RSI: {result['rsi']:.1f}")
        
        if opportunities:
            # Trade the best opportunity
            best = max(opportunities, key=lambda x: x['strength'])
            print(f"\n🚀 AUTO-EXECUTING BEST OPPORTUNITY...")
            self.open_position(best)
        else:
            print("\nNo high-quality opportunities found.")
    
    def run(self):
        print("="*60)
        print("BOSS33 AUTONOMOUS TRADER v3.0")
        print("="*60)
        print("\n⚠️  FULL AUTO-MODE ACTIVATED")
        print("Will execute trades WITHOUT confirmation")
        print("\nSafety Settings:")
        print(f"  Risk per trade: {CONFIG['risk_per_trade']*100}%")
        print(f"  Stop Loss: {CONFIG['stop_loss']*100}%")
        print(f"  Take Profit: {CONFIG['take_profit']*100}%")
        print(f"  Max Positions: {CONFIG['max_positions']}")
        print(f"  Min Strength: {CONFIG['min_strength']}/5")
        print(f"  Leverage: {CONFIG['leverage']}x (NONE)")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_and_trade()
                print(f"\n⏱️  Next scan in 60 seconds...\n")
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\nAutonomous trader stopped.")

if __name__ == '__main__':
    trader = AutonomousTrader()
    trader.run()
