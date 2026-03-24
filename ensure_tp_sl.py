#!/usr/bin/env python3
"""
Bybit TP/SL Guardian
Ensures all open positions have take profit and stop loss set.
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
        logging.FileHandler('tp_sl_guardian.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Bybit configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'

# TP/SL Settings
TP_PERCENT = 2.5  # 2.5% profit target
SL_PERCENT = 1.5  # 1.5% stop loss
TRAILING_STOP_PERCENT = 1.0  # 1% trailing stop - locks in profits as price moves


def send_telegram_alert(message: str):
    """Send alert to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured, skipping alert")
        return
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram alert sent successfully")
        else:
            logger.error(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")


def init_bybit():
    """Initialize Bybit exchange connection."""
    if not BYBIT_API_KEY or not BYBIT_API_SECRET:
        raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set")
    
    exchange = ccxt.bybit({
        'apiKey': BYBIT_API_KEY,
        'secret': BYBIT_API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',  # Use USDT Perpetual
        }
    })
    
    if BYBIT_TESTNET:
        exchange.set_sandbox_mode(True)
    
    return exchange


def get_open_positions(exchange):
    """Fetch all open positions using raw API for accurate TP/SL data."""
    try:
        # Use raw Bybit v5 API to get TP/SL info (ccxt doesn't parse these fields correctly)
        response = exchange.private_get_v5_position_list({
            'category': 'linear',
            'settleCoin': 'USDT'  # Get all USDT-margined positions
        })
        
        positions = []
        for pos in response.get('result', {}).get('list', []):
            size = float(pos.get('size', 0))
            if size != 0:
                # Parse side from Bybit format
                side = 'long' if pos.get('side') == 'Buy' else 'short'
                # Parse TP/SL from raw data
                tp = pos.get('takeProfit', '0')
                sl = pos.get('stopLoss', '0')
                tp_price = float(tp) if tp and tp != '0' else 0
                sl_price = float(sl) if sl and sl != '0' else 0
                
                positions.append({
                    'symbol': pos.get('symbol', 'Unknown') + '/USDT:USDT',
                    'bybit_symbol': pos.get('symbol'),
                    'side': side,
                    'entryPrice': float(pos.get('avgPrice', 0)),
                    'size': size,
                    'takeProfit': tp_price,
                    'stopLoss': sl_price,
                    'tpslMode': pos.get('tpslMode'),
                    'unrealizedPnl': float(pos.get('unrealisedPnl', 0))
                })
        return positions
    except Exception as e:
        logger.error(f"Error fetching positions from raw API: {e}")
        # Fallback to ccxt (without TP/SL data)
        try:
            positions = exchange.fetch_positions()
            return [p for p in positions if float(p.get('contracts', 0)) != 0]
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
            return []


def calculate_tp_sl(entry_price: float, side: str, tp_percent: float, sl_percent: float):
    """
    Calculate TP and SL prices based on entry price and side.
    
    LONG: TP above entry, SL below entry
    SHORT: TP below entry, SL above entry
    """
    if side.upper() == 'LONG' or side.lower() == 'buy':
        tp_price = entry_price * (1 + tp_percent / 100)
        sl_price = entry_price * (1 - sl_percent / 100)
    else:  # SHORT
        tp_price = entry_price * (1 - tp_percent / 100)
        sl_price = entry_price * (1 + sl_percent / 100)
    
    return tp_price, sl_price


def calculate_trailing_stop(entry_price: float, side: str, trailing_percent: float):
    """
    Calculate trailing stop distance.
    
    Trailing stop follows the price at a fixed distance, locking in profits
    as the market moves in your favor.
    
    Args:
        entry_price: Position entry price
        side: 'LONG' or 'SHORT'
        trailing_percent: Distance from peak/trough as percentage
    
    Returns:
        Trailing stop distance in price terms
    """
    # Trailing stop is the distance from the peak (for longs) or trough (for shorts)
    # that triggers the stop. It's calculated as a percentage of entry price.
    distance = entry_price * (trailing_percent / 100)
    return distance


def set_position_mode(exchange, bybit_symbol: str):
    """Set position mode to One-way for TP/SL support."""
    try:
        # Set position mode to One-way (0)
        mode_params = {
            'symbol': bybit_symbol,
            'category': 'linear',
            'mode': 0,  # 0 = One-way mode, 3 = Hedge mode
        }
        
        # Try to set position mode to one-way
        try:
            # Try different method names
            if hasattr(exchange, 'v5_private_post_position_switch_mode'):
                exchange.v5_private_post_position_switch_mode(mode_params)
            elif hasattr(exchange, 'private_post_v5_position_switch_mode'):
                exchange.private_post_v5_position_switch_mode(mode_params)
            elif hasattr(exchange, 'privatePostV5PositionSwitchMode'):
                exchange.privatePostV5PositionSwitchMode(mode_params)
            else:
                exchange.request('position/switch-mode', 'v5', 'POST', mode_params)
            logger.debug(f"  Switched {bybit_symbol} to One-way mode")
            return True
        except Exception as e:
            error_str = str(e).lower()
            # Ignore "already in mode" errors
            if 'not modified' in error_str or 'already' in error_str:
                logger.debug(f"Position mode already set: {e}")
                return True
            logger.warning(f"Position mode switch warning: {e}")
            return True  # Continue anyway
            
    except Exception as e:
        logger.warning(f"Could not set position mode: {e}")
        return True  # Continue anyway


def set_trading_stop(exchange, bybit_symbol: str, side: str, tp_price: float, sl_price: float, trailing_stop: float = None):
    """
    Set TP/SL and optional Trailing Stop for a position using Bybit's setTradingStop endpoint.
    
    Args:
        trailing_stop: Distance (in price) for trailing stop. If None, no trailing stop is set.
    """
    try:
        symbol_for_precision = bybit_symbol.replace('USDT', '/USDT:USDT')
        
        # Round prices to proper precision
        tp_str = str(exchange.price_to_precision(symbol_for_precision, tp_price))
        sl_str = str(exchange.price_to_precision(symbol_for_precision, sl_price))
        
        logger.info(f"Setting TP/SL for {bybit_symbol} ({side}): TP={tp_str}, SL={sl_str}")
        
        params = {
            'symbol': bybit_symbol,
            'category': 'linear',  # USDT Perpetual
            'takeProfit': tp_str,
            'stopLoss': sl_str,
            'tpTriggerBy': 'LastPrice',
            'slTriggerBy': 'LastPrice',
            'tpslMode': 'Full',  # Required parameter
        }
        
        # Add trailing stop if specified
        if trailing_stop and trailing_stop > 0:
            ts_str = str(exchange.price_to_precision(symbol_for_precision, trailing_stop))
            params['trailingStop'] = ts_str
            logger.info(f"  Adding Trailing Stop: {ts_str}")
        
        # Try different API method names
        if hasattr(exchange, 'v5_private_post_position_trading_stop'):
            response = exchange.v5_private_post_position_trading_stop(params)
        elif hasattr(exchange, 'private_post_v5_position_trading_stop'):
            response = exchange.private_post_v5_position_trading_stop(params)
        elif hasattr(exchange, 'privatePostV5PositionTradingStop'):
            response = exchange.privatePostV5PositionTradingStop(params)
        else:
            # Use raw request via ccxt
            response = exchange.request(
                'position/trading-stop',
                'v5',
                'POST',
                params
            )
        
        logger.info(f"[OK] TP/SL set successfully for {bybit_symbol}")
        return True, response
        
    except Exception as e:
        error_str = str(e).lower()
        # Handle "not modified" error - means TP/SL is already set to these values
        if 'not modified' in error_str or '34040' in error_str:
            logger.info(f"  [OK] TP/SL already set for {bybit_symbol} (not modified)")
            return True, "Already set"
        logger.error(f"  [FAIL] Failed to set TP/SL for {bybit_symbol}: {e}")
        return False, str(e)


def main():
    """Main guardian logic."""
    logger.info("=" * 60)
    logger.info("Bybit TP/SL Guardian - Starting check...")
    logger.info(f"TP Target: {TP_PERCENT}%, SL Limit: {SL_PERCENT}%, Trailing: {TRAILING_STOP_PERCENT}%")
    logger.info("=" * 60)
    
    try:
        # Initialize exchange
        exchange = init_bybit()
        logger.info(f"Connected to Bybit (Testnet: {BYBIT_TESTNET})")
        
        # Load markets (required for price_to_precision)
        exchange.load_markets()
        logger.info("Markets loaded successfully")
        
        # Fetch open positions
        positions = get_open_positions(exchange)
        logger.info(f"Found {len(positions)} open positions")
        
        fixed_positions = []
        
        for position in positions:
            symbol = position.get('symbol', 'Unknown')
            bybit_symbol = position.get('bybit_symbol', symbol.replace('/', '').replace(':USDT', ''))
            side = position.get('side', 'Unknown')
            entry_price = float(position.get('entryPrice', 0) or 0)
            size = float(position.get('size', 0))
            unrealized_pnl = position.get('unrealizedPnl', 0)
            
            # Check existing TP/SL (now properly parsed from raw API)
            tp_price = position.get('takeProfit', 0)
            sl_price = position.get('stopLoss', 0)
            
            # Format side emoji
            side_emoji = "LONG" if side.lower() == 'long' else "SHORT"
            pnl_emoji = "+" if unrealized_pnl >= 0 else "-"
            
            # Format TP/SL display
            tp_display = f"{tp_price:.4f}" if tp_price > 0 else "NOT SET"
            sl_display = f"{sl_price:.4f}" if sl_price > 0 else "NOT SET"
            
            logger.info(f"Position: {symbol} [{side_emoji}] | Size: {size} | Entry: {entry_price:.4f} | PnL: {pnl_emoji}${abs(unrealized_pnl):.2f}")
            logger.info(f"   TP: {tp_display} | SL: {sl_display}")
            
            # Skip if both TP and SL already set
            if tp_price > 0 and sl_price > 0:
                logger.info(f"  [SKIP] {symbol} already has TP/SL set")
                continue
            
            # Calculate new TP/SL if missing
            if entry_price <= 0:
                logger.warning(f"  [ERROR] Cannot calculate TP/SL for {symbol} - invalid entry price")
                continue
            
            new_tp, new_sl = calculate_tp_sl(entry_price, side, TP_PERCENT, SL_PERCENT)
            
            # Use existing values if already set
            final_tp = tp_price if tp_price > 0 else new_tp
            final_sl = sl_price if sl_price > 0 else new_sl
            
            # Calculate trailing stop distance
            trailing_distance = calculate_trailing_stop(entry_price, side, TRAILING_STOP_PERCENT)
            
            logger.info(f"  [SET] Setting TP: {final_tp:.4f}, SL: {final_sl:.4f}, Trailing: {trailing_distance:.4f} ({TRAILING_STOP_PERCENT}%)")
            
            # Set position mode first
            set_position_mode(exchange, bybit_symbol)
            
            # Set TP/SL with trailing stop
            success, result = set_trading_stop(exchange, bybit_symbol, side, final_tp, final_sl, trailing_distance)
            
            if success:
                fixed_positions.append({
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry_price,
                    'tp': final_tp,
                    'sl': final_sl,
                    'action': 'ADDED' if (tp_price == 0 and sl_price == 0) else 'UPDATED'
                })
                logger.info(f"  [OK] Successfully set TP/SL for {symbol}")
            else:
                logger.error(f"  [FAIL] Failed to set TP/SL for {symbol}: {result}")
        
        # Send Telegram summary if positions were fixed
        if fixed_positions:
            alert_msg = "🚨 *Bybit TP/SL Guardian Alert*\n\n"
            alert_msg += f"Found {len(fixed_positions)} position(s) missing TP/SL:\n\n"
            
            for pos in fixed_positions:
                emoji = "🟢" if pos['side'].upper() == 'LONG' else "🔴"
                alert_msg += f"{emoji} *{pos['symbol']}* ({pos['side']})\n"
                alert_msg += f"   Entry: `{pos['entry_price']}`\n"
                alert_msg += f"   TP: `{pos['tp']}` (+{TP_PERCENT}%)\n"
                alert_msg += f"   SL: `{pos['sl']}` (-{SL_PERCENT}%)\n"
                alert_msg += f"   Trailing: `{TRAILING_STOP_PERCENT}%`\n"
                alert_msg += f"   Action: {pos['action']}\n\n"
            
            alert_msg += f"_Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            send_telegram_alert(alert_msg)
        else:
            logger.info("No positions needed fixing - all have TP/SL set")
        
        logger.info("=" * 60)
        logger.info("Check completed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Guardian failed: {e}")
        send_telegram_alert(f"❌ *TP/SL Guardian Error*\n\n```\n{str(e)}\n```")
        sys.exit(1)


if __name__ == '__main__':
    main()
