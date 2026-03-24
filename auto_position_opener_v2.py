"""
Auto Position Opener Bot - IMPROVED
Scans for high-probability setups and opens positions automatically
"""
import ccxt
import time
import random
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_opener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

# Trading config - MORE AGGRESSIVE
MAX_POSITIONS = 5
RISK_PER_TRADE = 5  # $5 max loss per position
LEVERAGE = 3
TP_PERCENT = 1.5
SL_PERCENT = 2.0
MIN_CONFIDENCE = 65  # LOWERED from 80 to 65

def calculate_signal_score(symbol, ohlcv):
    """Calculate trading signal score 0-100 - IMPROVED ALGORITHM"""
    if len(ohlcv) < 20:
        return 0, "Not enough data"
    
    closes = [c[4] for c in ohlcv[-20:]]
    highs = [c[2] for c in ohlcv[-20:]]
    lows = [c[3] for c in ohlcv[-20:]]
    volumes = [c[5] for c in ohlcv[-20:]]
    
    current_price = closes[-1]
    
    # RSI calculation
    gains = []
    losses = []
    for i in range(1, min(15, len(closes))):
        change = closes[-i] - closes[-i-1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))
    
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0.001
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # EMA calculation
    ema9 = sum(closes[-9:]) / 9
    ema21 = sum(closes[-21:]) / 21 if len(closes) >= 21 else ema9
    
    # Volume analysis
    vol_avg = sum(volumes[-5:]) / 5
    vol_current = volumes[-1]
    
    # Price momentum (multiple timeframes)
    change_3 = (closes[-1] - closes[-3]) / closes[-3] * 100
    change_5 = (closes[-1] - closes[-5]) / closes[-5] * 100
    change_10 = (closes[-1] - closes[-10]) / closes[-10] * 100 if len(closes) >= 10 else 0
    
    # SCORING ALGORITHM
    score = 50  # Base score
    reasons = []
    
    # Trend analysis (stronger weight)
    if ema9 > ema21 * 1.001:  # Uptrend
        score += 20
        reasons.append("Uptrend")
    elif ema9 < ema21 * 0.999:  # Downtrend
        score -= 10
        reasons.append("Downtrend")
    
    # RSI analysis (more nuanced)
    if 40 < rsi < 60:  # Neutral zone - good for continuation
        score += 15
        reasons.append("RSI neutral")
    elif rsi < 35:  # Oversold - bounce opportunity
        score += 25
        reasons.append("RSI oversold")
    elif rsi > 65:  # Overbought
        score -= 5
        reasons.append("RSI overbought")
    
    # Volume spike (strong signal)
    vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
    if vol_ratio > 1.5:
        score += 20
        reasons.append(f"Volume spike {vol_ratio:.1f}x")
    elif vol_ratio > 1.2:
        score += 10
        reasons.append(f"High volume {vol_ratio:.1f}x")
    
    # Momentum (multi-timeframe)
    if change_3 > 1 and change_5 > 0.5:
        score += 15
        reasons.append("Strong momentum")
    elif change_3 < -1 and change_5 < -0.5:
        score -= 5
        reasons.append("Negative momentum")
    
    # Volatility check (avoid flat markets)
    price_range = (max(highs[-10:]) - min(lows[-10:])) / current_price * 100
    if price_range < 0.5:  # Too flat
        score -= 20
        reasons.append("Flat market")
    elif price_range > 2:  # Good volatility
        score += 10
        reasons.append("Good volatility")
    
    final_score = max(0, min(100, score))
    reason_str = ", ".join(reasons) if reasons else "No strong signals"
    
    return final_score, reason_str

def scan_for_opportunities(exchange):
    """Scan all pairs for trading opportunities - FIXED SYMBOLS"""
    # MATIC/USDT REMOVED - not available on Bybit
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT',
               'XRP/USDT:USDT', 'ADA/USDT:USDT', 'LINK/USDT:USDT',
               'NEAR/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT',
               'UNI/USDT:USDT', 'ATOM/USDT:USDT', 'APT/USDT:USDT',
               'FIL/USDT:USDT', 'ETC/USDT:USDT', 'BCH/USDT:USDT']
    
    opportunities = []
    
    for symbol in symbols:
        try:
            # Get OHLCV data
            ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=30)
            if len(ohlcv) < 20:
                continue
            
            score, reasons = calculate_signal_score(symbol, ohlcv)
            current_price = ohlcv[-1][4]
            
            # Log all scores for debugging
            if score >= 50:  # Log potential candidates
                logger.info(f"  {symbol}: Score {score}/100 - {reasons}")
            
            if score >= MIN_CONFIDENCE:
                # Determine direction
                ema9 = sum([c[4] for c in ohlcv[-9:]]) / 9
                ema21 = sum([c[4] for c in ohlcv[-21:]]) / 21 if len(ohlcv) >= 21 else ema9
                
                side = 'buy' if ema9 > ema21 else 'sell'
                
                opportunities.append({
                    'symbol': symbol,
                    'score': score,
                    'price': current_price,
                    'side': side,
                    'reasons': reasons
                })
                logger.info(f"*** OPPORTUNITY: {symbol} {side.upper()} | Score: {score}/100")
                
        except Exception as e:
            # Silently skip errors
            pass
    
    # Sort by score
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    return opportunities

def get_open_positions_count(exchange):
    """Get count of open positions"""
    try:
        positions = exchange.fetch_positions()
        return sum(1 for p in positions if (p.get('contracts', 0) or 0) > 0)
    except:
        return 0

def open_position(exchange, symbol, side, score, reasons):
    """Open a new position with TP/SL"""
    try:
        # Get current price
        ticker = exchange.fetch_ticker(symbol)
        entry_price = ticker['last']
        
        # Calculate position size based on risk
        risk_amount = RISK_PER_TRADE
        stop_loss_pct = SL_PERCENT
        position_value = risk_amount / (stop_loss_pct / 100)
        
        # Get symbol info
        market = exchange.market(symbol)
        contract_size = market.get('contractSize', 1)
        
        # Calculate contracts
        contracts = position_value / entry_price / contract_size
        contracts = int(round(contracts))  # FIX: Convert to int
        
        if contracts < 1:
            contracts = 1
        
        logger.info(f"OPENING {side.upper()} position on {symbol}")
        logger.info(f"  Entry: ${entry_price:.4f}, Contracts: {contracts}")
        logger.info(f"  Score: {score}/100, Reasons: {reasons}")
        
        # Set leverage
        try:
            exchange.set_leverage(LEVERAGE, symbol)
        except:
            pass
        
        # Set margin mode to ISOLATED
        try:
            exchange.set_margin_mode('ISOLATED', symbol)
        except:
            pass
        
        # Open position
        if side == 'buy':
            order = exchange.create_market_buy_order(symbol, contracts)
        else:
            order = exchange.create_market_sell_order(symbol, contracts)
        
        # Calculate TP/SL prices
        if side == 'buy':
            tp_price = entry_price * (1 + TP_PERCENT / 100)
            sl_price = entry_price * (1 - SL_PERCENT / 100)
        else:
            tp_price = entry_price * (1 - TP_PERCENT / 100)
            sl_price = entry_price * (1 + SL_PERCENT / 100)
        
        # Set TP/SL
        try:
            if side == 'buy':
                exchange.create_order(symbol, 'limit', 'sell', contracts, tp_price, {'reduceOnly': True})
                exchange.create_order(symbol, 'stop_market', 'sell', contracts, None, {'stopPrice': sl_price, 'reduceOnly': True})
            else:
                exchange.create_order(symbol, 'limit', 'buy', contracts, tp_price, {'reduceOnly': True})
                exchange.create_order(symbol, 'stop_market', 'buy', contracts, None, {'stopPrice': sl_price, 'reduceOnly': True})
            
            logger.info(f"  TP: ${tp_price:.4f}, SL: ${sl_price:.4f}")
        except Exception as e:
            logger.error(f"  Error setting TP/SL: {e}")
        
        # Send alert
        send_alert(f"Position opened: {symbol} {side.upper()}\nEntry: ${entry_price:.4f}\nContracts: {contracts}\nScore: {score}/100\nReasons: {reasons}\nTP: ${tp_price:.4f}\nSL: ${sl_price:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error opening position: {e}")
        return False

def send_alert(message):
    """Send Telegram alert"""
    try:
        import requests
        bot_token = "8586893914:AAEIuNFlGNbhDeUQ-eXUOmTm0KHw_-aOtuI"
        chat_id = "5804173449"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': f"[Auto Opener] {message}"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def main():
    """Main loop"""
    logger.info("="*60)
    logger.info("AUTO POSITION OPENER BOT STARTED - IMPROVED v2")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Max Positions: {MAX_POSITIONS}")
    logger.info(f"Risk per Trade: ${RISK_PER_TRADE}")
    logger.info(f"Leverage: {LEVERAGE}x")
    logger.info(f"Min Confidence: {MIN_CONFIDENCE}%")
    logger.info(f"TP: {TP_PERCENT}%, SL: {SL_PERCENT}%")
    logger.info("="*60)
    
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    send_alert("Auto Position Opener Bot STARTED (v2 - More Aggressive)")
    
    scan_count = 0
    last_status_time = time.time()
    
    while True:
        try:
            scan_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Get position count
            pos_count = get_open_positions_count(exchange)
            
            # Log status every 5 minutes or when positions change
            if time.time() - last_status_time > 300 or scan_count == 1:
                logger.info(f"[{current_time}] Scan #{scan_count} | Positions: {pos_count}/{MAX_POSITIONS}")
                last_status_time = time.time()
            
            if pos_count >= MAX_POSITIONS:
                logger.info("Max positions reached, skipping scan")
                time.sleep(30)
                continue
            
            # Scan for opportunities
            opportunities = scan_for_opportunities(exchange)
            
            if opportunities:
                best = opportunities[0]
                logger.info(f"Best opportunity: {best['symbol']} | Score: {best['score']}% | Side: {best['side']}")
                logger.info(f"  Reasons: {best['reasons']}")
                
                if best['score'] >= MIN_CONFIDENCE:
                    logger.info(f"OPENING position on {best['symbol']}")
                    open_position(exchange, best['symbol'], best['side'], best['score'], best['reasons'])
                else:
                    logger.info(f"Score too low ({best['score']}%), skipping")
            else:
                if scan_count % 10 == 0:  # Log every 10 scans
                    logger.info("No opportunities found (scanning...)")
            
            # Wait before next scan
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
