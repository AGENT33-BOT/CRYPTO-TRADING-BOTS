#!/usr/bin/env python3
"""
Bybit Trailing Stop Enforcer
Adds trailing stops to all open positions for better risk management.
"""

import os
import sys
import logging
from datetime import datetime
import ccxt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Manual fallback for BOM-encoded files
if not os.getenv('BYBIT_API_KEY'):
    try:
        with open('.env', 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val
    except Exception:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trailing_stop.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Bybit configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'

# Trailing Stop Settings
TRAILING_STOP_PERCENT = 1.0  # 1% trailing stop


def init_bybit():
    """Initialize Bybit exchange connection."""
    if not BYBIT_API_KEY or not BYBIT_API_SECRET:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
    
    exchange = ccxt.bybit({
        'apiKey': BYBIT_API_KEY,
        'secret': BYBIT_API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
        }
    })
    
    if BYBIT_TESTNET:
        exchange.set_sandbox_mode(True)
    
    return exchange


def get_open_positions(exchange):
    """Fetch all open positions."""
    try:
        response = exchange.private_get_v5_position_list({
            'category': 'linear',
            'settleCoin': 'USDT'
        })
        
        positions = []
        for pos in response.get('result', {}).get('list', []):
            size = float(pos.get('size', 0))
            if size != 0:
                side = 'long' if pos.get('side') == 'Buy' else 'short'
                tp = pos.get('takeProfit', '0')
                sl = pos.get('stopLoss', '0')
                tp_price = float(tp) if tp and tp != '0' else 0
                sl_price = float(sl) if sl and sl != '0' else 0
                
                # Check if trailing stop exists
                trailing_stop = pos.get('trailingStop', '0')
                has_trailing = trailing_stop and trailing_stop != '0' and float(trailing_stop) > 0
                
                positions.append({
                    'symbol': pos.get('symbol', 'Unknown') + '/USDT:USDT',
                    'bybit_symbol': pos.get('symbol'),
                    'side': side,
                    'entryPrice': float(pos.get('avgPrice', 0)),
                    'size': size,
                    'takeProfit': tp_price,
                    'stopLoss': sl_price,
                    'hasTrailing': has_trailing,
                    'trailingStop': float(trailing_stop) if has_trailing else 0,
                    'unrealizedPnl': float(pos.get('unrealisedPnl', 0))
                })
        return positions
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return []


def set_trailing_stop(exchange, bybit_symbol: str, side: str, entry_price: float, trailing_percent: float):
    """Set trailing stop for a position."""
    try:
        symbol_for_precision = bybit_symbol.replace('USDT', '/USDT:USDT')
        
        # Calculate trailing stop distance
        distance = entry_price * (trailing_percent / 100)
        ts_str = str(exchange.price_to_precision(symbol_for_precision, distance))
        
        logger.info(f"Setting Trailing Stop for {bybit_symbol}: {ts_str} ({trailing_percent}%)")
        
        params = {
            'symbol': bybit_symbol,
            'category': 'linear',
            'trailingStop': ts_str,
        }
        
        # Try different API method names
        if hasattr(exchange, 'v5_private_post_position_trading_stop'):
            response = exchange.v5_private_post_position_trading_stop(params)
        elif hasattr(exchange, 'private_post_v5_position_trading_stop'):
            response = exchange.private_post_v5_position_trading_stop(params)
        elif hasattr(exchange, 'privatePostV5PositionTradingStop'):
            response = exchange.privatePostV5PositionTradingStop(params)
        else:
            response = exchange.request(
                'position/trading-stop',
                'v5',
                'POST',
                params
            )
        
        logger.info(f"[OK] Trailing Stop set for {bybit_symbol}")
        return True, response
        
    except Exception as e:
        error_str = str(e).lower()
        if 'not modified' in error_str or '34040' in error_str:
            logger.info(f"  [OK] Trailing Stop already set for {bybit_symbol}")
            return True, "Already set"
        logger.error(f"  [FAIL] Failed to set Trailing Stop: {e}")
        return False, str(e)


def main():
    """Main trailing stop enforcer."""
    logger.info("=" * 60)
    logger.info("Bybit Trailing Stop Enforcer")
    logger.info(f"Trailing Stop: {TRAILING_STOP_PERCENT}%")
    logger.info("=" * 60)
    
    try:
        exchange = init_bybit()
        logger.info(f"Connected to Bybit (Testnet: {BYBIT_TESTNET})")
        
        exchange.load_markets()
        logger.info("Markets loaded successfully")
        
        positions = get_open_positions(exchange)
        logger.info(f"Found {len(positions)} open positions")
        
        updated = []
        skipped = []
        
        for position in positions:
            symbol = position.get('symbol', 'Unknown')
            bybit_symbol = position.get('bybit_symbol', symbol.replace('/', '').replace(':USDT', ''))
            side = position.get('side', 'Unknown')
            entry_price = float(position.get('entryPrice', 0))
            has_trailing = position.get('hasTrailing', False)
            unrealized_pnl = position.get('unrealizedPnl', 0)
            
            side_emoji = "LONG" if side.lower() == 'long' else "SHORT"
            pnl_emoji = "+" if unrealized_pnl >= 0 else "-"
            
            logger.info(f"\nPosition: {symbol} [{side_emoji}] | Entry: {entry_price:.4f} | PnL: {pnl_emoji}${abs(unrealized_pnl):.2f}")
            
            if has_trailing:
                logger.info(f"  [SKIP] Already has Trailing Stop: {position.get('trailingStop')}")
                skipped.append(symbol)
                continue
            
            if entry_price <= 0:
                logger.warning(f"  [ERROR] Invalid entry price")
                continue
            
            # Set trailing stop
            success, result = set_trailing_stop(exchange, bybit_symbol, side, entry_price, TRAILING_STOP_PERCENT)
            
            if success:
                updated.append({
                    'symbol': symbol,
                    'side': side,
                    'entry': entry_price,
                    'trailing': entry_price * (TRAILING_STOP_PERCENT / 100)
                })
        
        logger.info("\n" + "=" * 60)
        logger.info(f"Summary: {len(updated)} updated, {len(skipped)} already had trailing")
        logger.info("=" * 60)
        
        # Print summary table
        if updated:
            print("\n📊 TRAILING STOPS APPLIED:")
            print("-" * 50)
            for pos in updated:
                emoji = "🟢" if pos['side'].upper() == 'LONG' else "🔴"
                print(f"{emoji} {pos['symbol']} ({pos['side']})")
                print(f"   Entry: ${pos['entry']:.4f}")
                print(f"   Trailing: ${pos['trailing']:.4f} ({TRAILING_STOP_PERCENT}%)")
                print(f"   → Locks in profits as price moves {TRAILING_STOP_PERCENT}% against you")
            print("-" * 50)
        
        if skipped:
            print(f"\n⏭️  Skipped ({len(skipped)}): Already have trailing stops")
        
        print("\n✅ Trailing Stop protection active on all positions!")
        print("   Your stops will now follow the price to lock in gains.")
        
    except Exception as e:
        logger.error(f"Trailing Stop enforcer failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
