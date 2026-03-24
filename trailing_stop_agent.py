#!/usr/bin/env python3
"""
Auto Trailing Stop Agent for Bybit Futures
Monitors positions and automatically trails stops when profit threshold is reached.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import ccxt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Also try loading from .env.bybit for backward compatibility
if os.path.exists('.env.bybit'):
    load_dotenv('.env.bybit')

# Manual fallback for BOM-encoded files or missing vars
if not os.getenv('BYBIT_API_KEY'):
    try:
        for env_file in ['.env', '.env.bybit']:
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8-sig') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, val = line.strip().split('=', 1)
                            if key.strip() and not os.getenv(key.strip()):
                                os.environ[key.strip()] = val.strip()
    except Exception as e:
        logger.warning(f"Could not manually load env: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trailing_stop_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'

# Trailing Stop Settings
PROFIT_THRESHOLD_USD = 1.0  # Activate trailing when position P&L >= $1
TRAIL_DISTANCE_PERCENT = 0.8  # Trail 0.8% behind current price
MIN_TRAIL_MOVE_PERCENT = 0.3  # Only move stop if price moved 0.3% in our favor
BREAKEVEN_THRESHOLD_USD = 0.5  # Move to breakeven when P&L >= $0.50

# State file to track trailing positions
STATE_FILE = 'trailing_stop_state.json'


class TrailingStopAgent:
    """Automated trailing stop manager for Bybit futures positions."""
    
    def __init__(self):
        self.exchange = None
        self.state = self.load_state()
        
    def init_exchange(self):
        """Initialize Bybit connection."""
        if not BYBIT_API_KEY or not BYBIT_API_SECRET:
            raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
        
        self.exchange = ccxt.bybit({
            'apiKey': BYBIT_API_KEY,
            'secret': BYBIT_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
            }
        })
        
        if BYBIT_TESTNET:
            self.exchange.set_sandbox_mode(True)
            
        logger.info(f"Connected to Bybit (Testnet: {BYBIT_TESTNET})")
        
    def load_state(self) -> Dict:
        """Load trailing state from file."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
        return {}
    
    def save_state(self):
        """Save trailing state to file."""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
            
    def get_open_positions(self) -> List[Dict]:
        """Fetch all open positions with P&L info."""
        try:
            positions = self.exchange.fetch_positions()
            open_positions = []
            
            for p in positions:
                size = float(p.get('contracts', 0) or p.get('size', 0) or 0)
                if size == 0:
                    continue
                    
                symbol = p.get('symbol', '')
                side = p.get('side', 'LONG')
                entry_price = float(p.get('entryPrice', 0) or p.get('average', 0) or 0)
                mark_price = float(p.get('markPrice', 0) or p.get('lastPrice', 0) or 0)
                unrealized_pnl = float(p.get('unrealizedPnl', 0) or p.get('unrealisedPnl', 0) or 0)
                current_sl = float(p.get('stopLoss', 0) or 0)
                current_tp = float(p.get('takeProfit', 0) or 0)
                
                # Calculate distance from entry
                if entry_price > 0:
                    price_change_pct = ((mark_price - entry_price) / entry_price) * 100
                    if side.upper() == 'SHORT':
                        price_change_pct = -price_change_pct
                else:
                    price_change_pct = 0
                
                open_positions.append({
                    'symbol': symbol,
                    'side': side.upper(),
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'size': size,
                    'unrealized_pnl': unrealized_pnl,
                    'current_sl': current_sl,
                    'current_tp': current_tp,
                    'price_change_pct': price_change_pct
                })
                
            return open_positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def calculate_trailing_stop(self, position: Dict) -> Optional[float]:
        """
        Calculate new trailing stop price based on current position.
        Returns new SL price or None if no adjustment needed.
        """
        symbol = position['symbol']
        side = position['side']
        entry = position['entry_price']
        mark = position['mark_price']
        current_sl = position['current_sl']
        pnl = position['unrealized_pnl']
        pos_key = f"{symbol}_{side}"
        
        # Get or initialize trailing state for this position
        if pos_key not in self.state:
            self.state[pos_key] = {
                'highest_pnl': pnl,
                'highest_price': mark if side == 'LONG' else mark,
                'trailing_active': False,
                'breakeven_set': False,
                'activation_price': 0
            }
            
        trail_state = self.state[pos_key]
        
        # Update highest P&L tracked
        if pnl > trail_state['highest_pnl']:
            trail_state['highest_pnl'] = pnl
            
        # Phase 1: Move to breakeven when P&L >= $0.50
        if not trail_state['breakeven_set'] and pnl >= BREAKEVEN_THRESHOLD_USD:
            new_sl = entry * 1.001 if side == 'LONG' else entry * 0.999  # Small buffer
            if current_sl == 0 or (side == 'LONG' and new_sl > current_sl) or (side == 'SHORT' and new_sl < current_sl):
                trail_state['breakeven_set'] = True
                logger.info(f"🛡️ {symbol}: Moving stop to breakeven (+${pnl:.2f} P&L)")
                return new_sl
        
        # Phase 2: Activate trailing when P&L >= $1.00
        if not trail_state['trailing_active'] and pnl >= PROFIT_THRESHOLD_USD:
            trail_state['trailing_active'] = True
            trail_state['activation_price'] = mark
            trail_state['highest_price'] = mark
            logger.info(f"🚀 {symbol}: Trailing stop ACTIVATED at ${pnl:.2f} profit")
            
        # Phase 3: Trail the stop
        if trail_state['trailing_active']:
            # Track highest favorable price
            if side == 'LONG':
                if mark > trail_state['highest_price']:
                    trail_state['highest_price'] = mark
                    
                # Calculate new trailing stop
                trail_price = trail_state['highest_price'] * (1 - TRAIL_DISTANCE_PERCENT / 100)
                
                # Only move if significant improvement (avoid micro-adjustments)
                min_move = entry * (MIN_TRAIL_MOVE_PERCENT / 100)
                if current_sl == 0 or (trail_price > current_sl and trail_price - current_sl >= min_move):
                    logger.info(f"📈 {symbol}: Trailing LONG stop to {trail_price:.4f} (was {current_sl:.4f})")
                    return trail_price
                    
            else:  # SHORT
                if mark < trail_state['highest_price']:
                    trail_state['highest_price'] = mark
                    
                # Calculate new trailing stop
                trail_price = trail_state['highest_price'] * (1 + TRAIL_DISTANCE_PERCENT / 100)
                
                # Only move if significant improvement
                min_move = entry * (MIN_TRAIL_MOVE_PERCENT / 100)
                if current_sl == 0 or (trail_price < current_sl and current_sl - trail_price >= min_move):
                    logger.info(f"📉 {symbol}: Trailing SHORT stop to {trail_price:.4f} (was {current_sl:.4f})")
                    return trail_price
        
        return None
    
    def set_trading_stop(self, symbol: str, side: str, sl_price: float, tp_price: float = 0) -> bool:
        """Set or update stop loss for a position."""
        try:
            # Round prices to proper precision
            sl_str = str(self.exchange.price_to_precision(symbol, sl_price))
            tp_str = str(self.exchange.price_to_precision(symbol, tp_price)) if tp_price > 0 else ""
            
            # Prepare parameters
            bybit_symbol_clean = symbol.replace('/', '').replace(':USDT', '')
            params = {
                'symbol': bybit_symbol_clean,
                'category': 'linear',
                'stopLoss': sl_str,
                'slTriggerBy': 'LastPrice',
                'tpslMode': 'Full',
            }
            
            if tp_str:
                params['takeProfit'] = tp_str
                params['tpTriggerBy'] = 'LastPrice'
            
            # Try different API methods
            try:
                if hasattr(self.exchange, 'v5_private_post_position_trading_stop'):
                    response = self.exchange.v5_private_post_position_trading_stop(params)
                elif hasattr(self.exchange, 'private_post_v5_position_trading_stop'):
                    response = self.exchange.private_post_v5_position_trading_stop(params)
                elif hasattr(self.exchange, 'privatePostV5PositionTradingStop'):
                    response = self.exchange.privatePostV5PositionTradingStop(params)
                else:
                    response = self.exchange.request(
                        'position/trading-stop',
                        'v5',
                        'POST',
                        params
                    )
                    
                logger.info(f"✅ Set SL for {symbol}: {sl_str}")
                return True
                
            except Exception as api_error:
                error_str = str(api_error)
                # Check if it's "not modified" error - this means SL is already set correctly
                if '34040' in error_str or 'not modified' in error_str.lower():
                    logger.debug(f"{symbol}: SL already at target (not modified)")
                    return True
                raise
                
        except Exception as e:
            logger.error(f"❌ Failed to set SL for {symbol}: {e}")
            return False
    
    def clean_old_state(self, current_symbols: List[str]):
        """Remove state for closed positions."""
        keys_to_remove = []
        for key in self.state.keys():
            symbol = key.rsplit('_', 1)[0]  # Remove _LONG or _SHORT suffix
            if symbol not in current_symbols:
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.state[key]
            logger.info(f"Cleaned up state for closed position: {key}")
    
    def run_cycle(self):
        """Run one monitoring cycle."""
        try:
            positions = self.get_open_positions()
            current_symbols = [p['symbol'] for p in positions]
            
            # Clean up old state
            self.clean_old_state(current_symbols)
            
            if not positions:
                logger.info("No open positions to monitor")
                return
                
            logger.info(f"\n{'='*60}")
            logger.info(f"Monitoring {len(positions)} position(s)")
            logger.info(f"{'='*60}")
            
            for pos in positions:
                symbol = pos['symbol']
                side = pos['side']
                pnl = pos['unrealized_pnl']
                current_sl = pos['current_sl']
                
                logger.info(f"\n{symbol} {side}: P&L=${pnl:.2f}, SL={current_sl:.4f}")
                
                # Calculate new trailing stop
                new_sl = self.calculate_trailing_stop(pos)
                
                if new_sl:
                    # Keep existing TP if set
                    tp = pos['current_tp'] if pos['current_tp'] > 0 else 0
                    success = self.set_trading_stop(symbol, side, new_sl, tp)
                    if success:
                        self.save_state()
                else:
                    pos_key = f"{symbol}_{side}"
                    trail_state = self.state.get(pos_key, {})
                    if trail_state.get('trailing_active'):
                        logger.info(f"  ↳ Trailing active, highest P&L: ${trail_state['highest_pnl']:.2f}")
                    elif trail_state.get('breakeven_set'):
                        logger.info(f"  ↳ Breakeven protection set")
                    else:
                        logger.info(f"  ↳ Monitoring (need ${PROFIT_THRESHOLD_USD} to trail)")
                        
        except Exception as e:
            logger.error(f"Cycle error: {e}")
    
    def run(self):
        """Main loop - runs continuously."""
        logger.info("="*60)
        logger.info("Auto Trailing Stop Agent Starting...")
        logger.info(f"Profit threshold: ${PROFIT_THRESHOLD_USD}")
        logger.info(f"Trail distance: {TRAIL_DISTANCE_PERCENT}%")
        logger.info(f"Breakeven threshold: ${BREAKEVEN_THRESHOLD_USD}")
        logger.info("="*60)
        
        self.init_exchange()
        
        while True:
            try:
                self.run_cycle()
                logger.info(f"\n💤 Sleeping 30 seconds...\n")
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("\n👋 Agent stopped by user")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(60)  # Wait longer on error


if __name__ == '__main__':
    agent = TrailingStopAgent()
    agent.run()
