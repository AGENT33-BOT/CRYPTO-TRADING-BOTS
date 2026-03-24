"""
Enhanced Auto Trader with Built-in TP/SL and Trailing Stops
Opens positions with protection already in place
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_trader_enhanced.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# CONFIGURATION - BALANCED RISK/REWARD (FIXED)
CONFIG = {
    'min_confidence': 80,       # Back to 80% for quality signals
    'stop_loss_pct': 0.01,      # 1% SL (tighter cuts)
    'take_profit_pct': 0.02,    # 2% TP (2:1 reward/risk ratio)
    'partial_profit_pct': 1.0,  # Take 50% profit at 1%
    'trailing_start_pct': 1.5,  # Start trailing at +1.5%
    'trailing_distance_pct': 0.5,  # 0.5% trail
    'breakeven_trigger_pct': 0.75,  # Move to breakeven at +0.75%
    'risk_per_trade': 1.5,      # 1.5% of balance (conservative sizing)
    'max_positions': 7,
    'check_interval': 30,       # 30 seconds (balanced scanning)
    'margin_mode': 'ISOLATED',  # ISOLATED margin
    'leverage': 2,              # 2x leverage (safer)
    'cooldown_minutes': 45,     # 45 min cooldown after position close
}

PAIRS = [
    # Major Pairs
    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
    'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
    'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
    'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
    'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT',
    # Extended Pairs for More Opportunities
    'MATIC/USDT:USDT', 'SHIB1000/USDT:USDT', 'TRX/USDT:USDT', 'FIL/USDT:USDT',
    'ALGO/USDT:USDT', 'VET/USDT:USDT', 'AAVE/USDT:USDT', 'SUSHI/USDT:USDT',
    'INJ/USDT:USDT', 'TIA/USDT:USDT', 'SEI/USDT:USDT', 'STX/USDT:USDT',
    'ORDI/USDT:USDT', 'WLD/USDT:USDT', 'BEAM/USDT:USDT', 'IMX/USDT:USDT',
    'RNDR/USDT:USDT', 'AR/USDT:USDT', 'BLUR/USDT:USDT', 'PEPE1000/USDT:USDT',
    'WIF/USDT:USDT', 'BONK/USDT:USDT', 'FET/USDT:USDT', 'AGIX/USDT:USDT',
    'GRT/USDT:USDT', 'COMP/USDT:USDT', 'MKR/USDT:USDT', 'LDO/USDT:USDT',
    'CRV/USDT:USDT', 'SNX/USDT:USDT', 'YFI/USDT:USDT', '1INCH/USDT:USDT',
    'DYDX/USDT:USDT', 'APE/USDT:USDT', 'GMT/USDT:USDT', 'GALA/USDT:USDT',
    'MANA/USDT:USDT', 'SAND/USDT:USDT', 'AXS/USDT:USDT', 'FLOW/USDT:USDT',
    'ROSE/USDT:USDT', 'KSM/USDT:USDT', 'ZIL/USDT:USDT', 'XTZ/USDT:USDT',
    'NEO/USDT:USDT', 'ICP/USDT:USDT', 'THETA/USDT:USDT', 'ENJ/USDT:USDT',
    'CHZ/USDT:USDT', 'BAT/USDT:USDT', 'ZRX/USDT:USDT', 'KNC/USDT:USDT',
    'CELR/USDT:USDT', 'SKL/USDT:USDT', 'LRC/USDT:USDT', 'QTUM/USDT:USDT',
    'ONT/USDT:USDT', 'IOST/USDT:USDT', 'DASH/USDT:USDT', 'BSV/USDT:USDT',
    'EGLD/USDT:USDT', 'FTM/USDT:USDT', 'HBAR/USDT:USDT', 'ONE/USDT:USDT',
    'CELO/USDT:USDT', 'KAVA/USDT:USDT', 'ANKR/USDT:USDT', 'RVN/USDT:USDT',
    'IOTA/USDT:USDT', 'WAVES/USDT:USDT', 'DUSK/USDT:USDT', 'JASMY/USDT:USDT',
    'LUNC/USDT:USDT', 'COTI/USDT:USDT', 'ZEN/USDT:USDT', 'DENT/USDT:USDT',
    'HOT/USDT:USDT', 'CKB/USDT:USDT', 'SFP/USDT:USDT', 'C98/USDT:USDT',
    'ALPHA/USDT:USDT', 'RSR/USDT:USDT', 'PERP/USDT:USDT', 'KDA/USDT:USDT',
    'MINA/USDT:USDT', 'AUDIO/USDT:USDT', 'STMX/USDT:USDT', 'DGB/USDT:USDT',
    'NKN/USDT:USDT', 'SC/USDT:USDT', 'REEF/USDT:USDT', 'BAKE/USDT:USDT',
]

class EnhancedAutoTrader:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.positions_with_trailing = {}
        self.partial_profits_taken = {}  # Track positions where 50% sold at 1%
        self.last_close_time = {}  # Track when positions were closed per symbol (cooldown)
        
    def get_balance(self):
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['USDT']['free'])
        except:
            return 0
    
    def get_positions_count(self):
        """Count active positions"""
        count = 0
        for symbol in PAIRS:
            try:
                positions = self.exchange.fetch_positions([symbol])
                if positions and len(positions) > 0:
                    if float(positions[0].get('contracts', 0)) > 0:
                        count += 1
            except:
                pass
        return count
    
    def analyze_pair(self, symbol):
        """Analyze a pair for trading signals"""
        try:
            # Fetch OHLCV data
            timeframe = '15m'
            limit = 50
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if len(ohlcv) < 30:
                return None
            
            # Calculate indicators
            closes = [c[4] for c in ohlcv]
            highs = [c[2] for c in ohlcv]
            lows = [c[3] for c in ohlcv]
            
            current_price = closes[-1]
            
            # RSI Calculation
            rsi = self.calculate_rsi(closes)
            
            # Support/Resistance
            support_levels = self.find_support_levels(lows, closes)
            resistance_levels = self.find_resistance_levels(highs, closes)
            
            # Trend Analysis
            sma20 = sum(closes[-20:]) / 20
            sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma20
            
            trend = 'bullish' if sma20 > sma50 else 'bearish'
            
            # Signal Generation
            signal = None
            confidence = 0
            
            # LONG Signal
            if trend == 'bullish' and rsi < 65 and rsi > 40:
                # Price near support
                if support_levels and abs(current_price - max(support_levels)) / current_price < 0.01:
                    signal = 'LONG'
                    confidence = 75 + (65 - rsi) * 0.5
            
            # SHORT Signal
            elif trend == 'bearish' and rsi > 35 and rsi < 60:
                # Price near resistance
                if resistance_levels and abs(min(resistance_levels) - current_price) / current_price < 0.01:
                    signal = 'SHORT'
                    confidence = 75 + (rsi - 35) * 0.5
            
            if signal and confidence >= CONFIG['min_confidence']:
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': min(confidence, 99),
                    'price': current_price,
                    'trend': trend,
                    'rsi': rsi
                }
            
            return None
            
        except Exception as e:
            return None
    
    def calculate_rsi(self, closes, period=14):
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, period + 1):
            change = closes[-i] - closes[-(i+1)]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def find_support_levels(self, lows, closes, lookback=20):
        """Find support levels"""
        recent_lows = lows[-lookback:]
        support = []
        for i in range(1, len(recent_lows) - 1):
            if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i+1]:
                support.append(recent_lows[i])
        return sorted(support, reverse=True)[:3]
    
    def find_resistance_levels(self, highs, closes, lookback=20):
        """Find resistance levels"""
        recent_highs = highs[-lookback:]
        resistance = []
        for i in range(1, len(recent_highs) - 1):
            if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]:
                resistance.append(recent_highs[i])
        return sorted(resistance)[:3]
    
    def open_position_with_protection(self, symbol, side, entry_price, confidence):
        """Open position with TP/SL already set"""
        try:
            # CHECK COOLDOWN - Skip if this symbol is in cooldown
            can_trade, remaining = self.check_cooldown(symbol)
            if not can_trade:
                minutes_left = remaining / 60
                logging.info(f"⏱️  {symbol}: In cooldown ({minutes_left:.1f}min remaining). Skipping.")
                return False
            
            balance = self.get_balance()
            if balance < 10:
                logging.warning(f"Insufficient balance: ${balance:.2f}")
                return False
            
            # Calculate position size
            risk_amount = balance * (CONFIG['risk_per_trade'] / 100)
            stop_distance = entry_price * CONFIG['stop_loss_pct']
            
            if side == 'LONG':
                position_size = risk_amount / stop_distance
            else:
                position_size = risk_amount / stop_distance
            
            # Get market info
            market = self.exchange.market(symbol)
            amount_precision = market['precision']['amount']
            position_size = round(position_size, int(-amount_precision) if amount_precision < 1 else 0)
            
            if position_size < market['limits']['amount']['min']:
                logging.warning(f"Position size {position_size} below minimum")
                return False
            
            # Calculate TP/SL prices
            if side == 'LONG':
                stop_loss = entry_price * (1 - CONFIG['stop_loss_pct'])
                take_profit = entry_price * (1 + CONFIG['take_profit_pct'])
            else:
                stop_loss = entry_price * (1 + CONFIG['stop_loss_pct'])
                take_profit = entry_price * (1 - CONFIG['take_profit_pct'])
            
            logging.info("=" * 60)
            logging.info(f"OPENING {side} POSITION - {symbol}")
            logging.info(f"   Confidence: {confidence:.1f}%")
            logging.info(f"   Entry: ${entry_price:.4f}")
            logging.info(f"   Size: {position_size}")
            logging.info(f"   Leverage: {CONFIG['leverage']}x")
            logging.info(f"   Margin: ISOLATED")
            logging.info(f"   SL: ${stop_loss:.4f} ({CONFIG['stop_loss_pct']*100:.1f}%)")
            logging.info(f"   TP: ${take_profit:.4f} ({CONFIG['take_profit_pct']*100:.1f}%)")
            logging.info("=" * 60)
            
            # Set leverage first
            try:
                self.exchange.set_leverage(CONFIG['leverage'], symbol)
                self.exchange.set_margin_mode('ISOLATED', symbol)
            except Exception as e:
                logging.warning(f"Leverage/Margin setting: {e}")
            
            # Open market position
            order_side = 'buy' if side == 'LONG' else 'sell'
            position_order = self.exchange.create_market_order(
                symbol=symbol,
                side=order_side,
                amount=position_size,
                params={
                    'leverage': CONFIG['leverage'],
                    'marginMode': 'ISOLATED'
                }
            )
            
            actual_entry = float(position_order['average'] or position_order['price'] or entry_price)
            
            # Recalculate TP/SL based on actual entry
            if side == 'LONG':
                stop_loss = actual_entry * (1 - CONFIG['stop_loss_pct'])
                take_profit = actual_entry * (1 + CONFIG['take_profit_pct'])
            else:
                stop_loss = actual_entry * (1 + CONFIG['stop_loss_pct'])
                take_profit = actual_entry * (1 - CONFIG['take_profit_pct'])
            
            # Set Stop Loss
            sl_side = 'sell' if side == 'LONG' else 'buy'
            self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=sl_side,
                amount=position_size,
                params={
                    'triggerPrice': round(stop_loss, 4),
                    'triggerDirection': 'descending' if side == 'LONG' else 'ascending',
                    'reduceOnly': True
                }
            )
            
            # Set Take Profit
            self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=sl_side,
                amount=position_size,
                price=round(take_profit, 4),
                params={'reduceOnly': True}
            )
            
            logging.info(f"✅ {symbol} {side} position opened!")
            logging.info(f"   Entry: ${actual_entry:.4f}")
            logging.info(f"   SL: ${stop_loss:.4f}")
            logging.info(f"   TP: ${take_profit:.4f}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error opening position: {e}")
            return False
    
    def monitor_positions_for_trailing(self):
        """Monitor positions and apply trailing stops"""
        for symbol in PAIRS:
            try:
                positions = self.exchange.fetch_positions([symbol])
                if positions and len(positions) > 0:
                    pos = positions[0]
                    contracts = float(pos.get('contracts', 0))
                    
                    if contracts <= 0:
                        continue
                    
                    entry = float(pos.get('entryPrice', 0))
                    mark = float(pos.get('markPrice', 0))
                    side = pos['side'].upper()
                    pnl = float(pos.get('unrealizedPnl', 0))
                    
                    if entry <= 0:
                        continue
                    
                    # Calculate PnL %
                    if side == 'LONG':
                        pnl_pct = ((mark - entry) / entry) * 100
                    else:
                        pnl_pct = ((entry - mark) / entry) * 100
                    
                    # Get unrealized PnL in USD
                    unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                    
                    # CHECK FOR $1-2 PROFIT TARGET - Close position!
                    if unrealized_pnl >= 1.0:
                        logging.info(f"💰 {symbol}: Profit ${unrealized_pnl:.2f} reached! Closing position...")
                        self.close_position(symbol, f"Profit target ${unrealized_pnl:.2f} reached")
                        continue
                    
                    # Check for partial profit at 1% (sell 50%) - DISABLED (using dollar target instead)
                    # if pnl_pct >= 1.0 and symbol not in self.partial_profits_taken:
                    #     logging.info(f"💰 {symbol}: Profit +{pnl_pct:.2f}% - Taking 50% partial profit!")
                    #     self.take_partial_profit(symbol, entry, contracts, side)
                    #     self.partial_profits_taken[symbol] = True
                    
                    # Check for trailing stop trigger
                    if pnl_pct >= CONFIG['trailing_start_pct']:
                        if symbol not in self.positions_with_trailing:
                            logging.info(f"🎯 {symbol}: Profit +{pnl_pct:.2f}% - Activating trailing stop!")
                            self.positions_with_trailing[symbol] = {
                                'highest_profit': pnl_pct,
                                'entry': entry,
                                'side': side
                            }
                        else:
                            # Update highest profit
                            if pnl_pct > self.positions_with_trailing[symbol]['highest_profit']:
                                self.positions_with_trailing[symbol]['highest_profit'] = pnl_pct
                                logging.info(f"📈 {symbol}: New high +{pnl_pct:.2f}%")
                    
                    # Check if trailing stop should trigger
                    if symbol in self.positions_with_trailing:
                        trailing_data = self.positions_with_trailing[symbol]
                        highest = trailing_data['highest_profit']
                        
                        if pnl_pct < highest - CONFIG['trailing_distance_pct']:
                            logging.info(f"🛑 {symbol}: Trailing stop triggered! Profit pulled back from +{highest:.2f}% to +{pnl_pct:.2f}%")
                            self.close_position(symbol, f"Trailing stop at +{pnl_pct:.2f}%")
                            del self.positions_with_trailing[symbol]
                    
                    # Check for breakeven move
                    elif pnl_pct >= CONFIG['breakeven_trigger_pct'] and symbol not in self.positions_with_trailing:
                        logging.info(f"💚 {symbol}: Profit +{pnl_pct:.2f}% - Moving SL to breakeven!")
                        self.move_stop_to_breakeven(symbol, entry, contracts, side)
                    
            except Exception as e:
                pass
    
    def move_stop_to_breakeven(self, symbol, entry_price, contracts, side):
        """Move stop loss to breakeven"""
        try:
            # Cancel existing SL
            self.exchange.cancel_all_orders(symbol)
            
            # Set new SL at entry (breakeven)
            sl_side = 'sell' if side == 'LONG' else 'buy'
            self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=sl_side,
                amount=contracts,
                params={
                    'triggerPrice': round(entry_price, 4),
                    'triggerDirection': 'descending' if side == 'LONG' else 'ascending',
                    'reduceOnly': True
                }
            )
            
            logging.info(f"✅ {symbol}: SL moved to breakeven ${entry_price:.4f}")
        except Exception as e:
            logging.error(f"❌ Error moving SL: {e}")
    
    def close_position(self, symbol, reason):
        """Close position immediately and start cooldown"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            if positions and len(positions) > 0:
                pos = positions[0]
                contracts = float(pos.get('contracts', 0))
                side = pos['side']
                
                if contracts > 0:
                    close_side = 'buy' if side == 'short' else 'sell'
                    self.exchange.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=contracts,
                        params={'reduceOnly': True}
                    )
                    
                    # Cancel all orders
                    try:
                        self.exchange.cancel_all_orders(symbol)
                    except:
                        pass
                    
                    # START COOLDOWN - Record close time for this symbol
                    self.last_close_time[symbol] = time.time()
                    cooldown_mins = CONFIG['cooldown_minutes']
                    logging.info(f"⏱️  {symbol}: Starting {cooldown_mins}min cooldown before next trade")
                    
                    logging.info(f"✅ {symbol} closed: {reason}")
        except Exception as e:
            logging.error(f"❌ Error closing: {e}")
    
    def check_cooldown(self, symbol):
        """Check if symbol is in cooldown period"""
        if symbol not in self.last_close_time:
            return True, 0  # No cooldown
        
        elapsed = time.time() - self.last_close_time[symbol]
        cooldown_seconds = CONFIG['cooldown_minutes'] * 60
        
        if elapsed >= cooldown_seconds:
            return True, 0  # Cooldown expired
        
        remaining = cooldown_seconds - elapsed
        return False, remaining  # Still in cooldown
    
    def scan_and_trade(self):
        """Main scanning and trading loop"""
        logging.info("=" * 60)
        logging.info("🔍 SCANNING FOR OPPORTUNITIES")
        logging.info("=" * 60)
        
        # Check position count
        pos_count = self.get_positions_count()
        logging.info(f"Active positions: {pos_count}/{CONFIG['max_positions']}")
        
        if pos_count >= CONFIG['max_positions']:
            logging.info("Max positions reached. Skipping scan.")
            return
        
        # Scan each pair
        signals_found = []
        for symbol in PAIRS:
            result = self.analyze_pair(symbol)
            if result:
                signals_found.append(result)
        
        # Sort by confidence
        signals_found.sort(key=lambda x: x['confidence'], reverse=True)
        
        if signals_found:
            logging.info(f"\n📊 Found {len(signals_found)} signals:")
            for sig in signals_found:
                logging.info(f"   {sig['symbol']}: {sig['signal']} ({sig['confidence']:.1f}%) | RSI: {sig['rsi']:.1f} | Trend: {sig['trend']}")
            
            # Execute highest confidence signal
            best = signals_found[0]
            if best['confidence'] >= CONFIG['min_confidence']:
                logging.info(f"\n🚀 EXECUTING: {best['symbol']} {best['signal']} at {best['confidence']:.1f}%")
                self.open_position_with_protection(
                    best['symbol'], 
                    best['signal'], 
                    best['price'], 
                    best['confidence']
                )
        else:
            logging.info("No high-confidence signals found.")
    
    def run(self):
        """Main loop"""
        logging.info("=" * 60)
        logging.info("🤖 ENHANCED AUTO TRADER STARTED")
        logging.info("=" * 60)
        logging.info(f"Min Confidence: {CONFIG['min_confidence']}%")
        logging.info(f"SL: {CONFIG['stop_loss_pct']*100}% | TP: {CONFIG['take_profit_pct']*100}%")
        logging.info(f"Trailing: Starts at +{CONFIG['trailing_start_pct']}%")
        logging.info(f"Breakeven: Move SL at +{CONFIG['breakeven_trigger_pct']}%")
        logging.info("=" * 60)
        
        try:
            while True:
                # Scan for new opportunities
                self.scan_and_trade()
                
                # Monitor existing positions
                self.monitor_positions_for_trailing()
                
                logging.info(f"\n⏱️  Next cycle in {CONFIG['check_interval']}s...\n")
                time.sleep(CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            logging.info("\nAuto trader stopped")

if __name__ == '__main__':
    trader = EnhancedAutoTrader()
    trader.run()
