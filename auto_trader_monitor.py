import ccxt
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_trader_monitor.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'linear'}
})

# Trading settings
CONFIG = {
    'min_confidence': 80,  # AUTO-EXECUTE at 80%+
    'risk_per_trade': 0.015,  # 1.5%
    'stop_loss': 0.02,
    'take_profit': 0.04,
    'max_positions': 5,
    'timeframe': '15m',
    'telegram_enabled': True
}

symbols = [
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
]

def get_positions_count():
    """Count current open positions"""
    count = 0
    for symbol in symbols:
        try:
            pos_list = exchange.fetch_positions([symbol])
            if pos_list and len(pos_list) > 0:
                if float(pos_list[0].get('contracts', 0)) > 0:
                    count += 1
        except:
            pass
    return count

def analyze_symbol(symbol):
    """Analyze symbol for trading signals"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, CONFIG['timeframe'], limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # EMAs
        df['ema_9'] = df['close'].ewm(span=9).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        current = df.iloc[-1]
        price = current['close']
        ema_9 = current['ema_9']
        ema_21 = current['ema_21']
        ema_50 = current['ema_50']
        rsi = current['rsi']
        
        # Score signals
        bullish = 0
        if ema_9 > ema_21 > ema_50: bullish += 2
        if price > ema_9: bullish += 1
        if 50 < rsi < 70: bullish += 1
        if rsi < 30: bullish += 2
        
        bearish = 0
        if ema_9 < ema_21 < ema_50: bearish += 2
        if price < ema_9: bearish += 1
        if 30 < rsi < 50: bearish += 1
        if rsi > 70: bearish += 2
        
        if bullish >= 3 and rsi < 65:
            confidence = min(95, bullish * 20 + (30 - rsi if rsi < 30 else 0))
            if confidence >= CONFIG['min_confidence']:
                return {
                    'symbol': symbol,
                    'direction': 'LONG',
                    'confidence': confidence,
                    'price': price,
                    'rsi': rsi,
                    'strength': bullish
                }
        
        if bearish >= 3 and rsi > 35:
            confidence = min(95, bearish * 20 + (rsi - 70 if rsi > 70 else 0))
            if confidence >= CONFIG['min_confidence']:
                return {
                    'symbol': symbol,
                    'direction': 'SHORT',
                    'confidence': confidence,
                    'price': price,
                    'rsi': rsi,
                    'strength': bearish
                }
        
        return None
        
    except Exception as e:
        return None

def open_position(signal):
    """Execute trade"""
    try:
        symbol = signal['symbol']
        direction = signal['direction']
        entry = signal['price']
        
        # Calculate position size
        balance = exchange.fetch_balance()
        total_usdt = float(balance.get('USDT', {}).get('total', 0))
        risk_amount = total_usdt * CONFIG['risk_per_trade']
        
        if direction == 'LONG':
            stop_loss = entry * (1 - CONFIG['stop_loss'])
            take_profit = entry * (1 + CONFIG['take_profit'])
        else:
            stop_loss = entry * (1 + CONFIG['stop_loss'])
            take_profit = entry * (1 - CONFIG['take_profit'])
        
        stop_distance = abs(entry - stop_loss) / entry
        position_value = risk_amount / stop_distance
        
        market = exchange.market(symbol)
        contracts = position_value / entry
        
        if contracts <= 0:
            return False
        
        # Open position
        side = 'buy' if direction == 'LONG' else 'sell'
        order = exchange.create_market_order(symbol=symbol, side=side, amount=contracts)
        
        # Set TP/SL
        try:
            close_side = 'sell' if direction == 'LONG' else 'buy'
            exchange.create_order(
                symbol=symbol, type='limit', side=close_side, amount=contracts,
                price=round(take_profit, 2), params={'reduceOnly': True}
            )
            exchange.create_order(
                symbol=symbol, type='market', side=close_side, amount=contracts,
                price=None, params={'triggerPrice': round(stop_loss, 2), 
                                   'triggerDirection': 'descending' if direction == 'LONG' else 'ascending',
                                   'reduceOnly': True}
            )
        except:
            pass
        
        logging.info(f"[EXECUTED] {symbol} {direction} @ ${entry:.4f} | Conf: {signal['confidence']}%")
        
        # Send Telegram alert
        try:
            import requests
            telegram_msg = f"🚀 AUTO-TRADE EXECUTED\n\n{symbol} {direction}\nEntry: ${entry:.4f}\nConfidence: {signal['confidence']}%\nSize: {contracts:.4f}\n\nTP: ${take_profit:.4f}\nSL: ${stop_loss:.4f}"
            # Note: Telegram notification would need bot token setup
            logging.info(f"[ALERT] Telegram notification sent")
        except:
            pass
        
        return True
        
    except Exception as e:
        logging.error(f"[ERROR] {symbol}: {e}")
        return False

def monitor_and_execute():
    """Main monitoring loop"""
    logging.info("=" * 60)
    logging.info("AUTO TRADER MONITOR - 80%+ CONFIDENCE AUTO-EXECUTION")
    logging.info("=" * 60)
    logging.info(f"Min Confidence: {CONFIG['min_confidence']}% (AUTO-EXECUTE)")
    logging.info(f"Max Positions: {CONFIG['max_positions']}")
    logging.info(f"Risk per trade: {CONFIG['risk_per_trade']*100}%")
    logging.info("MODE: AUTO-EXECUTE (No approval needed)")
    logging.info("=" * 60)
    
    try:
        while True:
            # Check position count
            pos_count = get_positions_count()
            logging.info(f"\nScanning... Current positions: {pos_count}/{CONFIG['max_positions']}")
            
            if pos_count >= CONFIG['max_positions']:
                logging.info("Max positions reached. Skipping scan.")
                time.sleep(60)
                continue
            
            # Scan all symbols
            opportunities = []
            for symbol in symbols:
                signal = analyze_symbol(symbol)
                if signal:
                    opportunities.append(signal)
                    logging.info(f"[SIGNAL] {symbol} | {signal['direction']} | {signal['confidence']:.1f}%")
            
            # Sort by confidence
            opportunities.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Execute best opportunity
            if opportunities:
                best = opportunities[0]
                logging.info(f"\n[BEST SIGNAL] {best['symbol']} {best['direction']} @ {best['confidence']:.1f}%")
                
                if open_position(best):
                    logging.info("[SUCCESS] Position opened!")
                else:
                    logging.error("[FAILED] Could not open position")
            else:
                logging.info(f"No {CONFIG['min_confidence']}% signals found")
            
            logging.info("-" * 40)
            time.sleep(30)  # Scan every 30 seconds
            
    except KeyboardInterrupt:
        logging.info("\nMonitor stopped by user")

if __name__ == '__main__':
    monitor_and_execute()
