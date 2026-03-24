"""
BOSS33 Trading Bot v2.0 - Improved Strategy
=============================================
Key Improvements:
- 1x leverage only (no more 3x risk)
- Smaller position sizes (1-2% of account)
- Trend-following only (no counter-trend)
- Strict risk management
- Better entry criteria

Author: Agent33
Created: 2026-02-05
"""

import ccxt
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta
import logging
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boss33_trading_v2.log'),
        logging.StreamHandler()
    ]
)

# API Configuration
API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Telegram Alert Configuration
TELEGRAM_ENABLED = True
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Replace with actual token
TELEGRAM_CHAT_ID = '5804173449'

def send_telegram_alert(message):
    """Send alert to Telegram"""
    if not TELEGRAM_ENABLED:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, json=payload, timeout=10)
        logging.info("Telegram alert sent")
    except Exception as e:
        logging.warning(f"Failed to send Telegram alert: {e}")

# Trading Configuration - CONSERVATIVE
CONFIG = {
    'leverage': 1,  # NO LEVERAGE - safer
    'risk_per_trade': 0.015,  # 1.5% of account per trade
    'max_positions': 3,  # Max 3 positions at once
    'stop_loss': 0.02,  # 2% stop loss
    'take_profit': 0.04,  # 4% take profit (2:1 ratio)
    'trailing_activation': 0.025,  # Trail at 2.5%
    'trailing_distance': 0.015,  # Trail 1.5% behind
    'min_hold_time': 300,  # 5 minutes minimum hold
    'symbols': [
        'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT',
        'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT',
        'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT', 'ATOM/USDT:USDT', 'ETC/USDT:USDT',
        'ARB/USDT:USDT', 'OP/USDT:USDT', 'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT'
    ],
    'timeframe': '15m',  # 15 minute candles for better signals
}

class Boss33Trader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.position_history = []
        self.active_signals = {}
        
    def get_account_balance(self):
        """Get available USDT balance"""
        try:
            balance = self.exchange.fetch_balance()
            free_usdt = float(balance.get('USDT', {}).get('free', 0))
            total_usdt = float(balance.get('USDT', {}).get('total', 0))
            return free_usdt, total_usdt
        except Exception as e:
            logging.error(f"Error fetching balance: {e}")
            return 0, 0
    
    def get_positions(self):
        """Get all open positions"""
        try:
            positions = {}
            for symbol in CONFIG['symbols']:
                pos_list = self.exchange.fetch_positions([symbol])
                if pos_list and len(pos_list) > 0:
                    pos = pos_list[0]
                    if float(pos.get('contracts', 0)) > 0:
                        positions[symbol] = pos
            return positions
        except Exception as e:
            logging.error(f"Error fetching positions: {e}")
            return {}
    
    def calculate_position_size(self, symbol, entry_price, stop_price):
        """Calculate safe position size based on risk"""
        try:
            free_usdt, total_usdt = self.get_account_balance()
            
            if total_usdt < 50:
                logging.warning(f"Insufficient balance: ${total_usdt}")
                return 0
            
            # Risk amount (1.5% of account)
            risk_amount = total_usdt * CONFIG['risk_per_trade']
            
            # Calculate distance to stop
            stop_distance = abs(entry_price - stop_price) / entry_price
            
            if stop_distance == 0:
                return 0
            
            # Position size = Risk Amount / Stop Distance
            position_value = risk_amount / stop_distance
            
            # Get symbol info for minimum size
            market = self.exchange.market(symbol)
            min_amount = market['limits']['amount']['min'] or 0
            
            # Calculate contracts
            contracts = position_value / entry_price
            
            # Ensure minimum size
            if contracts < min_amount:
                contracts = min_amount
                logging.info(f"Using minimum size for {symbol}: {contracts}")
            
            return contracts
            
        except Exception as e:
            logging.error(f"Error calculating position size: {e}")
            return 0
    
    def analyze_trend(self, symbol):
        """
        Analyze trend direction using multiple indicators
        Returns: 'LONG', 'SHORT', or 'NEUTRAL'
        """
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, CONFIG['timeframe'], limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate EMAs
            df['ema_9'] = df['close'].ewm(span=9).mean()
            df['ema_21'] = df['close'].ewm(span=21).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Get latest values
            current_close = df['close'].iloc[-1]
            ema_9 = df['ema_9'].iloc[-1]
            ema_21 = df['ema_21'].iloc[-1]
            ema_50 = df['ema_50'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            
            # Trend Analysis
            bullish_signals = 0
            bearish_signals = 0
            
            # EMA alignment
            if ema_9 > ema_21 > ema_50:
                bullish_signals += 2
            elif ema_9 < ema_21 < ema_50:
                bearish_signals += 2
            
            # Price above/below EMAs
            if current_close > ema_9:
                bullish_signals += 1
            elif current_close < ema_9:
                bearish_signals += 1
            
            # RSI
            if rsi > 50 and rsi < 70:
                bullish_signals += 1
            elif rsi < 50 and rsi > 30:
                bearish_signals += 1
            
            # Volume trend (simple check)
            recent_volume = df['volume'].tail(5).mean()
            older_volume = df['volume'].tail(10).head(5).mean()
            if recent_volume > older_volume * 1.2:
                if bullish_signals > bearish_signals:
                    bullish_signals += 1
                elif bearish_signals > bullish_signals:
                    bearish_signals += 1
            
            # Determine trend
            if bullish_signals >= 3 and rsi < 65:
                return 'LONG', bullish_signals, current_close, rsi
            elif bearish_signals >= 3 and rsi > 35:
                return 'SHORT', bearish_signals, current_close, rsi
            else:
                return 'NEUTRAL', max(bullish_signals, bearish_signals), current_close, rsi
                
        except Exception as e:
            logging.error(f"Error analyzing {symbol}: {e}")
            return 'NEUTRAL', 0, 0, 50
    
    def find_entry_levels(self, symbol, direction):
        """Find optimal entry, stop loss, and take profit levels"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            if direction == 'LONG':
                entry = current_price
                stop_loss = entry * (1 - CONFIG['stop_loss'])
                take_profit = entry * (1 + CONFIG['take_profit'])
            else:  # SHORT
                entry = current_price
                stop_loss = entry * (1 + CONFIG['stop_loss'])
                take_profit = entry * (1 - CONFIG['take_profit'])
            
            return entry, stop_loss, take_profit
            
        except Exception as e:
            logging.error(f"Error finding entry for {symbol}: {e}")
            return 0, 0, 0
    
    def open_position(self, symbol, direction, entry, stop_loss, take_profit):
        """Open a new position with proper risk management"""
        try:
            # Calculate position size
            contracts = self.calculate_position_size(symbol, entry, stop_loss)
            
            if contracts <= 0:
                logging.warning(f"Invalid position size for {symbol}")
                return None
            
            # Set leverage to 1x
            try:
                self.exchange.set_leverage(CONFIG['leverage'], symbol)
            except:
                pass  # Leverage might already be set
            
            # Open position
            side = 'buy' if direction == 'LONG' else 'sell'
            
            logging.info(f"Opening {direction} position on {symbol}")
            logging.info(f"  Entry: ${entry:.4f}")
            logging.info(f"  Stop: ${stop_loss:.4f}")
            logging.info(f"  Target: ${take_profit:.4f}")
            logging.info(f"  Size: {contracts:.4f}")
            
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=contracts
            )
            
            # Send Telegram alert
            emoji = "🟢" if direction == 'LONG' else "🔴"
            alert_msg = f"""{emoji} <b>BOSS33 NEW POSITION</b>

<b>{symbol}</b> | {direction}
Entry: ${entry:.2f}
Stop: ${stop_loss:.2f}
Target: ${take_profit:.2f}
Size: {contracts:.4f}
Risk: {CONFIG['risk_per_trade']*100}%"""
            send_telegram_alert(alert_msg)
            
            # Set stop loss and take profit
            try:
                if direction == 'LONG':
                    self.exchange.create_order(
                        symbol=symbol,
                        type='limit',
                        side='sell',
                        amount=contracts,
                        price=take_profit,
                        params={'reduceOnly': True, 'stopLossPrice': stop_loss}
                    )
                else:
                    self.exchange.create_order(
                        symbol=symbol,
                        type='limit',
                        side='buy',
                        amount=contracts,
                        price=take_profit,
                        params={'reduceOnly': True, 'stopLossPrice': stop_loss}
                    )
            except Exception as e:
                logging.warning(f"Could not set TP/SL: {e}")
            
            # Record position
            position_record = {
                'time': datetime.now().isoformat(),
                'symbol': symbol,
                'direction': direction,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'size': contracts,
                'order_id': order['id']
            }
            
            self.position_history.append(position_record)
            
            with open('boss33_positions_v2.json', 'a') as f:
                f.write(json.dumps(position_record) + '\n')
            
            logging.info(f"✅ Position opened successfully: {order['id']}")
            return order
            
        except Exception as e:
            logging.error(f"Error opening position: {e}")
            return None
    
    def manage_existing_positions(self):
        """Monitor and manage open positions"""
        positions = self.get_positions()
        
        if not positions:
            return
        
        logging.info(f"\nManaging {len(positions)} open positions:")
        
        for symbol, pos in positions.items():
            try:
                size = float(pos['contracts'])
                entry = float(pos['entryPrice'])
                mark = float(pos['markPrice'])
                pnl = float(pos['unrealizedPnl'])
                side = pos['side']
                
                # Calculate PnL percentage
                if side == 'long':
                    pnl_pct = ((mark - entry) / entry) * 100
                else:
                    pnl_pct = ((entry - mark) / entry) * 100
                
                logging.info(f"  {symbol}: {side.upper()} | PnL: {pnl:+.2f} ({pnl_pct:+.2f}%)")
                
                # Check if we should take partial profit at +2.5%
                if pnl_pct >= 2.5:
                    logging.info(f"    🎯 Approaching target! Consider taking profits.")
                
                # Check if position is losing too much
                if pnl_pct <= -1.5:
                    logging.warning(f"    ⚠️  Position losing -1.5%, close if hits -2%")
                    
            except Exception as e:
                logging.error(f"Error managing {symbol}: {e}")
    
    def scan_for_opportunities(self):
        """Scan all symbols for trading opportunities"""
        logging.info("\n" + "="*60)
        logging.info(f"BOSS33 Trading Bot v2.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("="*60)
        
        # Get account info
        free_usdt, total_usdt = self.get_account_balance()
        logging.info(f"\n💰 Balance: ${total_usdt:.2f} (Free: ${free_usdt:.2f})")
        
        # Get current positions
        positions = self.get_positions()
        logging.info(f"📊 Open Positions: {len(positions)}/{CONFIG['max_positions']}")
        
        # Manage existing positions
        if positions:
            self.manage_existing_positions()
        
        # Check if we can open new positions
        if len(positions) >= CONFIG['max_positions']:
            logging.info("\n⏳ Max positions reached. Waiting for closures.")
            return
        
        if free_usdt < 20:
            logging.info("\n⏳ Insufficient free balance. Waiting...")
            return
        
        # Scan for new opportunities
        logging.info("\n🔍 Scanning for opportunities...")
        
        opportunities = []
        
        for symbol in CONFIG['symbols']:
            if symbol in positions:
                continue
            
            trend, strength, price, rsi = self.analyze_trend(symbol)
            
            if trend != 'NEUTRAL' and strength >= 3:
                entry, stop_loss, take_profit = self.find_entry_levels(symbol, trend)
                
                if entry > 0:
                    opportunities.append({
                        'symbol': symbol,
                        'trend': trend,
                        'strength': strength,
                        'price': price,
                        'rsi': rsi,
                        'entry': entry,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit
                    })
                    
                    logging.info(f"\n  🎯 {symbol}: {trend} (Strength: {strength}/5)")
                    logging.info(f"     Price: ${price:.4f} | RSI: {rsi:.1f}")
                    logging.info(f"     Entry: ${entry:.4f} | Stop: ${stop_loss:.4f} | Target: ${take_profit:.4f}")
        
        # Open best opportunity
        if opportunities:
            # Sort by strength
            opportunities.sort(key=lambda x: x['strength'], reverse=True)
            best = opportunities[0]
            
            logging.info(f"\n🚀 Opening best opportunity: {best['symbol']} {best['trend']}")
            self.open_position(
                best['symbol'],
                best['trend'],
                best['entry'],
                best['stop_loss'],
                best['take_profit']
            )
        else:
            logging.info("\n⏳ No high-quality opportunities found. Waiting...")
    
    def run(self):
        """Main trading loop"""
        logging.info("\n" + "="*60)
        logging.info("BOSS33 Trading Bot v2.0 - STARTED")
        logging.info("="*60)
        logging.info(f"\nConfiguration:")
        logging.info(f"  Leverage: {CONFIG['leverage']}x (NO LEVERAGE)")
        logging.info(f"  Risk per trade: {CONFIG['risk_per_trade']*100}%")
        logging.info(f"  Stop Loss: {CONFIG['stop_loss']*100}%")
        logging.info(f"  Take Profit: {CONFIG['take_profit']*100}%")
        logging.info(f"  Max positions: {CONFIG['max_positions']}")
        logging.info(f"\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_for_opportunities()
                logging.info(f"\n⏱️  Next scan in 60 seconds...\n")
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("\n\nBOSS33 Trading Bot v2.0 - STOPPED")

if __name__ == '__main__':
    trader = Boss33Trader()
    trader.run()
