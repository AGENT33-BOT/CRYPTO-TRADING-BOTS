"""
Funding Rate Arbitrage Bot for Bybit
Strategy: Long spot / Short perpetual (or vice versa) to capture funding payments
Profits from funding rate differentials without directional risk
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
        logging.FileHandler('funding_arbitrage.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

CONFIG = {
    'min_funding_rate': 0.0001,    # 0.01% minimum to trade
    'max_funding_rate': 0.01,      # Skip if >1% (too volatile)
    'position_size': 20,           # USDT per arbitrage
    'leverage': 1,                 # Spot-like risk (no leverage for safety)
    'check_interval': 300,         # Check every 5 minutes
    'pairs': [                     # Pairs to monitor
        'BTC/USDT',
        'ETH/USDT', 
        'SOL/USDT',
        'XRP/USDT',
        'ADA/USDT',
        'DOGE/USDT',
        'LINK/USDT',
    ]
}

class FundingArbitrage:
    def __init__(self):
        self.spot_exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
            'urls': {
                'api': {
                    'public': 'https://api.bytick.com',
                    'private': 'https://api.bytick.com',
                }
            }
        })
        self.futures_exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},
            'urls': {
                'api': {
                    'public': 'https://api.bytick.com',
                    'private': 'https://api.bytick.com',
                }
            }
        })
        
        self.futures_exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        
        self.spot_exchange.load_markets()
        self.futures_exchange.load_markets()
        
        self.active_arbitrages = {}  # Track open positions
        
    def get_funding_rate(self, symbol):
        """Get current funding rate for perpetual"""
        try:
            # Convert to perpetual symbol format
            perp_symbol = symbol.replace('/USDT', '/USDT:USDT')
            
            # Fetch funding rate
            funding_info = self.futures_exchange.fetch_funding_rate(perp_symbol)
            funding_rate = funding_info.get('fundingRate', 0)
            next_funding_time = funding_info.get('fundingTimestamp', 0)
            
            return funding_rate, next_funding_time
        except Exception as e:
            logging.error(f"Funding rate fetch error for {symbol}: {e}")
            return None, None
    
    def get_prices(self, symbol):
        """Get spot and perpetual prices"""
        try:
            spot_ticker = self.spot_exchange.fetch_ticker(symbol)
            perp_symbol = symbol.replace('/USDT', '/USDT:USDT')
            perp_ticker = self.futures_exchange.fetch_ticker(perp_symbol)
            
            spot_price = spot_ticker['last']
            perp_price = perp_ticker['last']
            
            # Calculate spread
            spread = (perp_price - spot_price) / spot_price
            
            return spot_price, perp_price, spread
        except Exception as e:
            logging.error(f"Price fetch error for {symbol}: {e}")
            return None, None, None
    
    def check_arbitrage_opportunity(self, symbol):
        """Check if funding arbitrage is profitable"""
        funding_rate, next_funding = self.get_funding_rate(symbol)
        spot_price, perp_price, spread = self.get_prices(symbol)
        
        if funding_rate is None or spot_price is None:
            return None
        
        # Convert funding rate to percentage
        funding_pct = funding_rate * 100
        
        opportunity = {
            'symbol': symbol,
            'funding_rate': funding_rate,
            'funding_pct': funding_pct,
            'spot_price': spot_price,
            'perp_price': perp_price,
            'spread': spread * 100,
            'next_funding': next_funding
        }
        
        return opportunity
    
    def execute_arbitrage(self, symbol, direction):
        """
        Execute arbitrage trade
        direction: 'positive' = short perp (earn funding) / long spot
                  'negative' = long perp (earn funding) / short spot (if available)
        """
        try:
            perp_symbol = symbol.replace('/USDT', '/USDT:USDT')
            amount = CONFIG['position_size'] / self.get_prices(symbol)[0]
            
            if direction == 'positive':
                # Positive funding: Short perpetual, Long spot
                logging.info(f"Executing POSITIVE arbitrage on {symbol}")
                
                # Long spot
                spot_order = self.spot_exchange.create_market_buy_order(symbol, amount)
                logging.info(f"SPOT LONG: {amount:.6f} {symbol}")
                
                # Short perpetual
                perp_order = self.futures_exchange.create_market_sell_order(perp_symbol, amount)
                logging.info(f"PERP SHORT: {amount:.6f} {perp_symbol}")
                
            else:
                # Negative funding: Long perpetual, Short spot (if margin available)
                logging.info(f"Executing NEGATIVE arbitrage on {symbol}")
                
                # Short spot (requires margin account)
                # Note: Bybit spot margin may not be available for all users
                logging.warning("Negative funding arbitrage requires margin trading - skipping")
                return False
            
            self.active_arbitrages[symbol] = {
                'direction': direction,
                'amount': amount,
                'entry_time': datetime.now()
            }
            
            return True
            
        except Exception as e:
            logging.error(f"Arbitrage execution error: {e}")
            return False
    
    def close_arbitrage(self, symbol):
        """Close arbitrage position"""
        try:
            if symbol not in self.active_arbitrages:
                return
            
            arb = self.active_arbitrages[symbol]
            perp_symbol = symbol.replace('/USDT', '/USDT:USDT')
            amount = arb['amount']
            
            if arb['direction'] == 'positive':
                # Close: Sell spot, Buy perp
                self.spot_exchange.create_market_sell_order(symbol, amount)
                self.futures_exchange.create_market_buy_order(perp_symbol, amount)
            
            del self.active_arbitrages[symbol]
            logging.info(f"Closed arbitrage on {symbol}")
            
        except Exception as e:
            logging.error(f"Close arbitrage error: {e}")
    
    def scan_opportunities(self):
        """Scan all pairs for funding arbitrage opportunities"""
        logging.info("\n" + "=" * 60)
        logging.info("SCANNING FUNDING ARBITRAGE OPPORTUNITIES")
        logging.info("=" * 60)
        
        opportunities = []
        
        for symbol in CONFIG['pairs']:
            opp = self.check_arbitrage_opportunity(symbol)
            if opp:
                opportunities.append(opp)
        
        # Sort by funding rate magnitude
        opportunities.sort(key=lambda x: abs(x['funding_rate']), reverse=True)
        
        # Display results
        logging.info(f"\n{'Symbol':<12} {'Funding %':<12} {'Spread %':<12} {'Spot':<12} {'Perp':<12}")
        logging.info("-" * 60)
        
        for opp in opportunities:
            funding_color = "🟢" if opp['funding_rate'] > 0 else "🔴"
            logging.info(
                f"{opp['symbol']:<12} "
                f"{funding_color} {opp['funding_pct']:+.4f}%  "
                f"{opp['spread']:+.4f}%    "
                f"${opp['spot_price']:,.2f}   "
                f"${opp['perp_price']:,.2f}"
            )
            
            # Check if we should trade
            funding_abs = abs(opp['funding_rate'])
            if CONFIG['min_funding_rate'] <= funding_abs <= CONFIG['max_funding_rate']:
                if opp['symbol'] not in self.active_arbitrages:
                    direction = 'positive' if opp['funding_rate'] > 0 else 'negative'
                    logging.info(f"  ➡️  EXECUTING: {direction} arbitrage on {opp['symbol']}")
                    self.execute_arbitrage(opp['symbol'], direction)
        
        logging.info(f"\nActive arbitrages: {len(self.active_arbitrages)}")
        for sym in self.active_arbitrages:
            logging.info(f"  • {sym}: {self.active_arbitrages[sym]['direction']}")
    
    def run(self):
        """Main loop"""
        logging.info("=" * 60)
        logging.info("FUNDING RATE ARBITRAGE BOT STARTED")
        logging.info("=" * 60)
        logging.info(f"Min funding rate: {CONFIG['min_funding_rate']*100:.3f}%")
        logging.info(f"Position size: ${CONFIG['position_size']} per trade")
        logging.info(f"Monitoring {len(CONFIG['pairs'])} pairs")
        logging.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_opportunities()
                
                # Calculate time until next funding (usually every 8 hours)
                # Bybit funding: 00:00, 08:00, 16:00 UTC
                now = datetime.utcnow()
                hours_until_funding = 8 - (now.hour % 8)
                minutes_until_funding = 60 - now.minute
                
                logging.info(f"\nNext funding in ~{hours_until_funding}h {minutes_until_funding}m")
                logging.info(f"Sleeping {CONFIG['check_interval']}s...\n")
                
                time.sleep(CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            logging.info("\nStopping arbitrage bot...")
            # Close all open arbitrages
            for symbol in list(self.active_arbitrages.keys()):
                self.close_arbitrage(symbol)
            logging.info("Arbitrage bot stopped")

if __name__ == '__main__':
    arb = FundingArbitrage()
    arb.run()
