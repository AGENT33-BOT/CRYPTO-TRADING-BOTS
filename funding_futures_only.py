"""
Funding Rate Capture Bot for Bybit (FUTURES ONLY - NO SPOT)
Strategy: Short perpetual when funding is positive to earn funding payments
NO SPOT TRADING - Only futures/perpetual positions
"""

import ccxt
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('funding_futures_only.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

CONFIG = {
    'min_funding_rate': 0.0001,    # 0.01% minimum to trade
    'max_funding_rate': 0.01,      # Skip if >1% (too volatile)
    'position_size': 20,           # USDT per position
    'leverage': 3,                 # Use leverage for better capital efficiency
    'check_interval': 300,         # Check every 5 minutes
    'pairs': [                     # Pairs to monitor
        'BTC/USDT:USDT',
        'ETH/USDT:USDT', 
        'SOL/USDT:USDT',
        'XRP/USDT:USDT',
        'ADA/USDT:USDT',
        'DOGE/USDT:USDT',
        'LINK/USDT:USDT',
    ]
}

class FundingFuturesOnly:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}  # FUTURES ONLY - NO SPOT
        })
        
        self.exchange.load_markets()
        self.active_positions = {}  # Track open short positions
        
    def get_funding_rate(self, symbol):
        """Get current funding rate for perpetual"""
        try:
            funding_info = self.exchange.fetch_funding_rate(symbol)
            funding_rate = funding_info.get('fundingRate', 0)
            next_funding_time = funding_info.get('fundingTimestamp', 0)
            
            return funding_rate, next_funding_time
        except Exception as e:
            logging.error(f"Funding rate fetch error for {symbol}: {e}")
            return None, None
    
    def get_price(self, symbol):
        """Get current price"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logging.error(f"Price fetch error for {symbol}: {e}")
            return None
    
    def check_opportunity(self, symbol):
        """Check if funding capture opportunity exists"""
        funding_rate, next_funding = self.get_funding_rate(symbol)
        price = self.get_price(symbol)
        
        if funding_rate is None or price is None:
            return None
        
        funding_pct = funding_rate * 100
        
        opportunity = {
            'symbol': symbol,
            'funding_rate': funding_rate,
            'funding_pct': funding_pct,
            'price': price,
            'next_funding': next_funding,
            'action': 'short' if funding_rate > 0 else None  # Only short when positive funding
        }
        
        return opportunity
    
    def open_short(self, symbol):
        """Open short position to capture positive funding"""
        try:
            price = self.get_price(symbol)
            if not price:
                return False
            
            # Calculate position size with leverage
            position_value = CONFIG['position_size'] * CONFIG['leverage']
            amount = position_value / price
            
            logging.info(f"Opening SHORT on {symbol} to capture funding")
            logging.info(f"Price: ${price:.4f}, Amount: {amount:.6f}, Size: ${position_value:.2f}")
            
            # Set leverage
            try:
                self.exchange.set_leverage(CONFIG['leverage'], symbol)
            except:
                pass
            
            # Open short
            order = self.exchange.create_market_sell_order(symbol, amount)
            logging.info(f"SHORT OPENED: {order['id']}")
            
            self.active_positions[symbol] = {
                'amount': amount,
                'entry_price': price,
                'entry_time': datetime.now()
            }
            
            return True
            
        except Exception as e:
            logging.error(f"Error opening short: {e}")
            return False
    
    def close_short(self, symbol):
        """Close short position"""
        try:
            if symbol not in self.active_positions:
                return
            
            pos = self.active_positions[symbol]
            amount = pos['amount']
            
            logging.info(f"Closing SHORT on {symbol}")
            order = self.exchange.create_market_buy_order(symbol, amount)
            logging.info(f"SHORT CLOSED: {order['id']}")
            
            del self.active_positions[symbol]
            
        except Exception as e:
            logging.error(f"Error closing short: {e}")
    
    def scan_opportunities(self):
        """Scan all pairs for funding opportunities"""
        logging.info("\n" + "=" * 60)
        logging.info("FUNDING CAPTURE SCAN (FUTURES ONLY)")
        logging.info("=" * 60)
        
        for symbol in CONFIG['pairs']:
            opp = self.check_opportunity(symbol)
            if not opp:
                continue
            
            funding_pct = opp['funding_pct']
            action = opp['action']
            
            # Display funding info
            emoji = "🟢" if opp['funding_rate'] > 0 else "🔴"
            logging.info(f"{emoji} {symbol:<15} Funding: {funding_pct:+.4f}%  Price: ${opp['price']:,.4f}")
            
            # Check if we should open position
            if action == 'short' and CONFIG['min_funding_rate'] <= opp['funding_rate'] <= CONFIG['max_funding_rate']:
                if symbol not in self.active_positions:
                    logging.info(f"  ➡️  OPENING SHORT to capture funding")
                    self.open_short(symbol)
                else:
                    logging.info(f"  ✓  Already short, earning funding")
            
            # Check if we should close (funding turned negative)
            elif opp['funding_rate'] < 0 and symbol in self.active_positions:
                logging.info(f"  ➡️  Funding turned negative, closing short")
                self.close_short(symbol)
        
        logging.info(f"\nActive shorts: {len(self.active_positions)}")
        for sym in self.active_positions:
            logging.info(f"  • {sym}: Short position open")
    
    def run(self):
        """Main loop"""
        logging.info("=" * 60)
        logging.info("FUNDING CAPTURE BOT - FUTURES ONLY")
        logging.info("NO SPOT TRADING - SHORT PERPETUAL ONLY")
        logging.info("=" * 60)
        logging.info(f"Min funding rate: {CONFIG['min_funding_rate']*100:.3f}%")
        logging.info(f"Position size: ${CONFIG['position_size']} with {CONFIG['leverage']}x leverage")
        logging.info(f"Monitoring {len(CONFIG['pairs'])} pairs")
        logging.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_opportunities()
                
                logging.info(f"Sleeping {CONFIG['check_interval']}s...\n")
                time.sleep(CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            logging.info("\nStopping funding capture bot...")
            # Close all positions
            for symbol in list(self.active_positions.keys()):
                self.close_short(symbol)
            logging.info("Funding capture bot stopped")

if __name__ == '__main__':
    bot = FundingFuturesOnly()
    bot.run()
