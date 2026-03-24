"""
Conservative Trading Bot for Bybit Futures
Optimized for small accounts ($50-200)
Strategy: Multi-indicator with strict risk management
"""

import ccxt
import time
import logging
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('conservative_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# API Credentials
API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# CONSERVATIVE CONFIG for $60 account
CONFIG = {
    'max_positions': 2,           # Max 2 concurrent positions
    'risk_per_trade': 5.0,        # $5 risk per trade
    'leverage': 2,                # Conservative 2x leverage
    'min_confidence': 75,         # Higher quality signals only
    'tp_percent': 0.03,           # 3% take profit
    'sl_percent': 0.02,           # 2% stop loss
    'check_interval': 60,         # Check every 60 seconds
    'pairs': [
        'BTC/USDT:USDT',          # Major coins only
        'ETH/USDT:USDT',
        'SOL/USDT:USDT',
        'ADA/USDT:USDT',
        'LINK/USDT:USDT'
    ]
}

class ConservativeTrader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.exchange.load_markets()
        self.positions = {}
        
    def get_balance(self):
        """Get USDT balance"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return {
                'total': float(usdt.get('total', 0)),
                'free': float(usdt.get('free', 0)),
                'used': float(usdt.get('used', 0))
            }
        except Exception as e:
            logger.error(f"Balance error: {e}")
            return {'total': 0, 'free': 0, 'used': 0}
    
    def get_positions(self):
        """Get open positions"""
        try:
            positions = self.exchange.fetch_positions()
            open_pos = {}
            for p in positions:
                contracts = float(p.get('contracts', 0))
                if contracts != 0:
                    symbol = p['symbol']
                    open_pos[symbol] = {
                        'side': p.get('side', 'unknown'),
                        'size': contracts,
                        'entry': float(p.get('entryPrice', 0)),
                        'pnl': float(p.get('unrealizedPnl', 0))
                    }
            return open_pos
        except Exception as e:
            logger.error(f"Position error: {e}")
            return {}
    
    def calculate_signal(self, symbol):
        """Calculate trading signal score"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '15m', limit=50)
            if len(ohlcv) < 30:
                return 0, None, None
            
            closes = [c[4] for c in ohlcv]
            highs = [c[2] for c in ohlcv]
            lows = [c[3] for c in ohlcv]
            volumes = [c[5] for c in ohlcv]
            
            current_price = closes[-1]
            
            # Calculate RSI
            gains, losses = [], []
            for i in range(1, min(15, len(closes))):
                change = closes[-i] - closes[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            avg_gain = sum(gains) / len(gains) if gains else 0.001
            avg_loss = sum(losses) / len(losses) if losses else 0.001
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            
            # EMAs
            ema9 = sum(closes[-9:]) / 9
            ema21 = sum(closes[-21:]) / 21 if len(closes) >= 21 else ema9
            
            # Volume
            vol_avg = sum(volumes[-5:]) / 5
            vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
            
            # Momentum
            change_3 = (closes[-1] - closes[-3]) / closes[-3] * 100
            change_5 = (closes[-1] - closes[-5]) / closes[-5] * 100
            
            # Scoring
            score = 50
            direction = None
            
            # Trend
            if ema9 > ema21 * 1.002:
                score += 20
                direction = 'LONG'
            elif ema9 < ema21 * 0.998:
                score += 20
                direction = 'SHORT'
            
            # RSI
            if 40 < rsi < 60:
                score += 15
            elif rsi < 35 and direction == 'LONG':
                score += 15
            elif rsi > 65 and direction == 'SHORT':
                score += 15
            
            # Volume
            if vol_ratio > 1.5:
                score += 15
            elif vol_ratio > 1.2:
                score += 8
            
            # Momentum
            if direction == 'LONG' and change_3 > 0.5:
                score += 10
            elif direction == 'SHORT' and change_3 < -0.5:
                score += 10
            
            score = max(0, min(100, score))
            
            return score, direction, current_price
            
        except Exception as e:
            logger.error(f"Signal error for {symbol}: {e}")
            return 0, None, None
    
    def open_position(self, symbol, side, price):
        """Open a new position"""
        try:
            balance = self.get_balance()
            if balance['free'] < CONFIG['risk_per_trade'] * 2:
                logger.warning(f"Insufficient balance: ${balance['free']:.2f}")
                return False
            
            # Calculate position size
            position_value = CONFIG['risk_per_trade'] * CONFIG['leverage']
            
            # Get market info
            market = self.exchange.market(symbol)
            amount = position_value / price
            
            # Round to precision
            if 'amount' in market['precision']:
                precision = market['precision']['amount']
                amount = round(amount, precision)
            
            # Ensure minimum
            min_amount = market['limits']['amount']['min']
            if min_amount and amount < min_amount:
                logger.warning(f"Amount {amount} below minimum {min_amount}")
                amount = min_amount
            
            # Set margin mode and leverage
            try:
                self.exchange.set_margin_mode('ISOLATED', symbol)
            except:
                pass
            try:
                self.exchange.set_leverage(CONFIG['leverage'], symbol)
            except:
                pass
            
            # Open position
            order_type = 'market'
            side_param = 'buy' if side == 'LONG' else 'sell'
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side_param,
                amount=amount,
                params={'leverage': CONFIG['leverage']}
            )
            
            logger.info(f"Opened {side} position on {symbol}: {amount} contracts @ ${price:.2f}")
            
            # Set TP/SL
            if side == 'LONG':
                tp_price = price * (1 + CONFIG['tp_percent'])
                sl_price = price * (1 - CONFIG['sl_percent'])
            else:
                tp_price = price * (1 - CONFIG['tp_percent'])
                sl_price = price * (1 + CONFIG['sl_percent'])
            
            self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side='sell' if side == 'LONG' else 'buy',
                amount=amount,
                price=tp_price,
                params={'stopLoss': False, 'takeProfit': True, 'reduceOnly': True}
            )
            
            self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side='sell' if side == 'LONG' else 'buy',
                amount=amount,
                price=sl_price,
                params={'stopPrice': sl_price, 'reduceOnly': True}
            )
            
            logger.info(f"Set TP: ${tp_price:.2f} | SL: ${sl_price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Open position error: {e}")
            return False
    
    def scan_and_trade(self):
        """Main trading loop"""
        balance = self.get_balance()
        positions = self.get_positions()
        
        logger.info(f"Balance: ${balance['total']:.2f} | Positions: {len(positions)}/{CONFIG['max_positions']}")
        
        if len(positions) >= CONFIG['max_positions']:
            logger.info("Max positions reached, skipping scan")
            return
        
        for symbol in CONFIG['pairs']:
            if symbol in positions:
                continue
            
            score, direction, price = self.calculate_signal(symbol)
            
            if score >= CONFIG['min_confidence'] and direction:
                logger.info(f"Signal: {symbol} {direction} (Score: {score}/100) @ ${price:.2f}")
                self.open_position(symbol, direction, price)
                break  # Open one at a time
            elif score >= 60:
                logger.debug(f"Weak signal on {symbol}: {direction} ({score}/100)")
    
    def run(self):
        """Main loop"""
        logger.info("="*60)
        logger.info("CONSERVATIVE TRADING BOT STARTED")
        logger.info(f"Max Positions: {CONFIG['max_positions']} | Risk/Trade: ${CONFIG['risk_per_trade']}")
        logger.info(f"Leverage: {CONFIG['leverage']}x | Confidence: {CONFIG['min_confidence']}%+")
        logger.info("="*60)
        
        while True:
            try:
                self.scan_and_trade()
                time.sleep(CONFIG['check_interval'])
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = ConservativeTrader()
    bot.run()
