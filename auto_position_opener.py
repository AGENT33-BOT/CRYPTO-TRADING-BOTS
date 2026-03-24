"""
Auto Position Opener Bot
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

# Trading config
MAX_POSITIONS = 5
RISK_PER_TRADE = 5  # $5 max loss per position
LEVERAGE = 3
TP_PERCENT = 1.5
SL_PERCENT = 2.0
MIN_CONFIDENCE = 80

def calculate_signal_score(symbol, ohlcv):
    """Calculate trading signal score 0-100"""
    if len(ohlcv) < 20:
        return 0
    
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
    
    # EMA 9 vs 21
    ema9 = sum(closes[-9:]) / 9
    ema21 = sum(closes[-21:]) / 21 if len(closes) >= 21 else ema9
    
    # Volume trend
    vol_avg = sum(volumes[-5:]) / 5
    vol_current = volumes[-1]
    
    # Score components
    score = 50  # Base score
    
    # Trend score
    if ema9 > ema21:
        score += 15
    else:
        score -= 15
    
    # RSI score (prefer 40-60 range for mean reversion, or trending)
    if 30 < rsi < 70:
        score += 10
    elif rsi < 30:  # Oversold - potential bounce
        score += 20
    elif rsi > 70:  # Overbought - potential pullback
        score -= 10
    
    # Volume score
    if vol_current > vol_avg * 1.2:
        score += 15
    
    # Price momentum
    price_change_5 = (closes[-1] - closes[-5]) / closes[-5] * 100
    if 0.5 < price_change_5 < 5:  # Moderate uptrend
        score += 10
    elif -5 < price_change_5 < -0.5:  # Moderate downtrend
        score -= 10
    
    return max(0, min(100, score))

def scan_for_opportunities(exchange):
    """Scan all pairs for trading opportunities"""
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 
               'XRP/USDT:USDT', 'ADA/USDT:USDT', 'LINK/USDT:USDT',
               'NEAR/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT',
               'DOGE/USDT:USDT', 'UNI/USDT:USDT', 'ATOM/USDT:USDT']
    
    opportunities = []
    
    for symbol in symbols:
        try:
            # Get OHLCV data
            ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=30)
            if len(ohlcv) < 20:
                continue
            
            score = calculate_signal_score(symbol, ohlcv)
            current_price = ohlcv[-1][4]
            
            if score >= MIN_CONFIDENCE:
                opportunities.append({
                    'symbol': symbol,
                    'score': score,
                    'price': current_price,
                    'side': 'buy' if score > 60 else 'sell'
                })
                
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
    
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

def open_position(exchange, symbol, side, score):
    """Open a new position with TP/SL"""
    try:
        # Get current price
        ticker = exchange.fetch_ticker(symbol)
        entry_price = ticker['last']
        
        # Calculate position size based on risk
        # Risk $5 with 3x leverage, 2% stop loss
        risk_amount = RISK_PER_TRADE
        stop_loss_pct = SL_PERCENT
        position_value = risk_amount / (stop_loss_pct / 100)
        
        # Adjust for leverage
        margin_needed = position_value / LEVERAGE
        
        # Get symbol info
        market = exchange.market(symbol)
        contract_size = market.get('contractSize', 1)
        
        # Calculate contracts
        contracts = position_value / entry_price / contract_size
        contracts = round(contracts, market.get('precision', {}).get('amount', 0))
        
        if contracts < 1:
            contracts = 1
        
        logger.info(f"Opening {side.upper()} position on {symbol}")
        logger.info(f"Entry: ${entry_price:.4f}, Contracts: {contracts}")
        logger.info(f"Signal Score: {score}%")
        
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
        order = exchange.create_market_buy_order(symbol, contracts) if side == 'buy' else exchange.create_market_sell_order(symbol, contracts)
        
        # Calculate TP/SL prices
        if side == 'buy':
            tp_price = entry_price * (1 + TP_PERCENT / 100)
            sl_price = entry_price * (1 - SL_PERCENT / 100)
        else:
            tp_price = entry_price * (1 - TP_PERCENT / 100)
            sl_price = entry_price * (1 + SL_PERCENT / 100)
        
        # Set TP/SL
        try:
            exchange.create_order(symbol, 'limit', 'sell' if side == 'buy' else 'buy', contracts, tp_price, {'reduceOnly': True})
            exchange.create_order(symbol, 'stop_market', 'sell' if side == 'buy' else 'buy', contracts, None, {'stopPrice': sl_price, 'reduceOnly': True})
            logger.info(f"TP set at ${tp_price:.4f}, SL set at ${sl_price:.4f}")
        except Exception as e:
            logger.error(f"Error setting TP/SL: {e}")
        
        # Send alert
        send_alert(f"Position opened: {symbol} {side.upper()}\nEntry: ${entry_price:.4f}\nContracts: {contracts}\nScore: {score}%\nTP: ${tp_price:.4f}\nSL: ${sl_price:.4f}")
        
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
    logger.info("AUTO POSITION OPENER BOT STARTED")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Max Positions: {MAX_POSITIONS}")
    logger.info(f"Risk per Trade: ${RISK_PER_TRADE}")
    logger.info(f"Leverage: {LEVERAGE}x")
    logger.info(f"Min Confidence: {MIN_CONFIDENCE}%")
    logger.info("="*60)
    
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    send_alert("Auto Position Opener Bot STARTED")
    
    scan_count = 0
    while True:
        try:
            scan_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Get position count
            pos_count = get_open_positions_count(exchange)
            
            logger.info(f"[{current_time}] Scan #{scan_count} | Positions: {pos_count}/{MAX_POSITIONS}")
            
            if pos_count >= MAX_POSITIONS:
                logger.info("Max positions reached, skipping scan")
                time.sleep(30)
                continue
            
            # Scan for opportunities
            opportunities = scan_for_opportunities(exchange)
            
            if opportunities:
                best = opportunities[0]
                logger.info(f"Best opportunity: {best['symbol']} | Score: {best['score']}% | Side: {best['side']}")
                
                if best['score'] >= MIN_CONFIDENCE:
                    logger.info(f"Opening position on {best['symbol']}")
                    open_position(exchange, best['symbol'], best['side'], best['score'])
                else:
                    logger.info(f"Score too low ({best['score']}%), skipping")
            else:
                logger.info("No opportunities found")
            
            # Wait before next scan
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
