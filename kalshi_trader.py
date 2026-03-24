"""
Kalshi Trading Bot
Event-based prediction market trading with RSA authentication
"""

import os
import json
import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kalshi_trader')

class KalshiAPI:
    """Kalshi API client with RSA authentication"""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    def __init__(self, key_id: str, private_key_path: str):
        self.key_id = key_id
        self.private_key_path = private_key_path
        self.private_key = self._load_private_key()
        self.session = requests.Session()
        
    def _load_private_key(self):
        """Load RSA private key from PEM file"""
        try:
            with open(self.private_key_path, 'rb') as f:
                key_data = f.read()
            private_key = serialization.load_pem_private_key(key_data, password=None)
            logger.info("✅ RSA private key loaded successfully")
            return private_key
        except Exception as e:
            logger.error(f"❌ Failed to load private key: {e}")
            raise
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate RSA-PSS signature for authentication (Kalshi official format)"""
        message = f"{timestamp}{method}{path}{body}"
        logger.debug(f"Signing message: {message}")
        signature = self.private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        sig_b64 = base64.b64encode(signature).decode('utf-8')
        logger.debug(f"Signature: {sig_b64[:50]}...")
        return sig_b64
    
    def _get_headers(self, method: str, path: str, body: str = "") -> dict:
        """Generate authentication headers"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(timestamp, method, path, body)
        
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
    
    def get_balance(self) -> dict:
        """Get account balance"""
        path = "/portfolio/balance"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get balance: {e}")
            return None
    
    def get_markets(self, status: str = "open", limit: int = 100) -> dict:
        """Get available markets"""
        path = f"/markets?status={status}&limit={limit}"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", "/markets")
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get markets: {e}")
            return None
    
    def get_market(self, ticker: str) -> dict:
        """Get specific market details"""
        path = f"/markets/{ticker}"
        url = urljoin(self.BASE_URL, path)
        headers = self._get_headers("GET", path)
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get market {ticker}: {e}")
            return None
    
    def get_orderbook(self, ticker: str) -> dict:
        """Get orderbook for a market"""
        path = f"/markets/{ticker}/orderbook"
        url = urljoin(self.BASE_URL, path)
        headers = self._get_headers("GET", path)
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get orderbook for {ticker}: {e}")
            return None
    
    def place_order(self, ticker: str, side: str, count: int, price: int = None, 
                   expiration_time: str = None, client_order_id: str = None) -> dict:
        """
        Place an order
        
        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            count: Number of contracts
            price: Price in cents (0-100), or None for market order
            expiration_time: ISO 8601 timestamp for order expiration
            client_order_id: Optional client order ID
        """
        path = "/portfolio/orders"
        url = urljoin(self.BASE_URL, path)
        
        order_data = {
            "ticker": ticker,
            "side": side,
            "count": count
        }
        
        if price is not None:
            order_data["price"] = price
        else:
            order_data["buy_max_cost"] = count * 100  # Market order
            
        if expiration_time:
            order_data["expiration_time"] = expiration_time
        if client_order_id:
            order_data["client_order_id"] = client_order_id
        
        body = json.dumps(order_data)
        headers = self._get_headers("POST", path, body)
        
        try:
            response = self.session.post(url, headers=headers, data=body)
            response.raise_for_status()
            logger.info(f"✅ Order placed: {side.upper()} {count} {ticker}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to place order: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return None
    
    def get_positions(self) -> dict:
        """Get current positions"""
        path = "/portfolio/positions"
        url = urljoin(self.BASE_URL, path)
        headers = self._get_headers("GET", path)
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return None
    
    def get_orders(self, status: str = None) -> dict:
        """Get orders"""
        path = "/portfolio/orders"
        if status:
            path += f"?status={status}"
        url = urljoin(self.BASE_URL, path)
        headers = self._get_headers("GET", path.split('?')[0])
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return None


class KalshiTrader:
    """Kalshi trading strategies"""
    
    def __init__(self, api: KalshiAPI, paper_trading: bool = True):
        self.api = api
        self.paper_trading = paper_trading
        self.positions = {}
        
    def scan_opportunities(self, min_volume: int = 1000, max_spread: int = 5):
        """Scan for trading opportunities"""
        logger.info("🔍 Scanning Kalshi markets for opportunities...")
        
        markets = self.api.get_markets(status="open", limit=100)
        if not markets or 'markets' not in markets:
            logger.warning("No markets found")
            return []
        
        opportunities = []
        
        for market in markets['markets']:
            ticker = market.get('ticker')
            volume = market.get('volume', 0)
            
            if volume < min_volume:
                continue
            
            # Get orderbook for spread analysis
            orderbook = self.api.get_orderbook(ticker)
            if not orderbook:
                continue
            
            yes_bid = orderbook.get('orderbook', {}).get('yes', [{}])[0].get('price', 0)
            yes_ask = orderbook.get('orderbook', {}).get('yes', [{}, {}])[1].get('price', 100)
            
            spread = yes_ask - yes_bid
            
            if spread <= max_spread:
                opportunities.append({
                    'ticker': ticker,
                    'title': market.get('title', ''),
                    'yes_bid': yes_bid,
                    'yes_ask': yes_ask,
                    'spread': spread,
                    'volume': volume,
                    'category': market.get('category', '')
                })
        
        return sorted(opportunities, key=lambda x: x['volume'], reverse=True)
    
    def momentum_strategy(self, ticker: str, lookback_minutes: int = 30):
        """
        Simple momentum strategy based on recent price movement
        """
        market = self.api.get_market(ticker)
        if not market:
            return None
        
        # Get current price
        orderbook = self.api.get_orderbook(ticker)
        if not orderbook:
            return None
        
        yes_price = orderbook.get('orderbook', {}).get('yes', [{}])[0].get('price', 50)
        
        # Simple logic: if price > 60, momentum is up
        # if price < 40, momentum is down
        if yes_price > 60:
            return {'side': 'yes', 'confidence': yes_price / 100}
        elif yes_price < 40:
            return {'side': 'no', 'confidence': (100 - yes_price) / 100}
        
        return None
    
    def mean_reversion_strategy(self, ticker: str):
        """
        Mean reversion strategy - bet on prices returning to 50
        """
        orderbook = self.api.get_orderbook(ticker)
        if not orderbook:
            return None
        
        yes_price = orderbook.get('orderbook', {}).get('yes', [{}])[0].get('price', 50)
        
        # If price is extreme, bet on reversion to mean
        if yes_price > 80:
            return {'side': 'no', 'confidence': (yes_price - 50) / 50}
        elif yes_price < 20:
            return {'side': 'yes', 'confidence': (50 - yes_price) / 50}
        
        return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Kalshi Trading Bot')
    parser.add_argument('--key-id', required=True, help='Kalshi API Key ID')
    parser.add_argument('--key-path', default='kalshi_key.pem', help='Path to RSA private key')
    parser.add_argument('--action', choices=['balance', 'markets', 'positions', 'scan', 'trade'], 
                       default='balance', help='Action to perform')
    parser.add_argument('--ticker', help='Market ticker for specific actions')
    parser.add_argument('--side', choices=['yes', 'no'], help='Order side')
    parser.add_argument('--count', type=int, default=1, help='Number of contracts')
    parser.add_argument('--price', type=int, help='Price in cents (0-100)')
    
    args = parser.parse_args()
    
    # Initialize API
    api = KalshiAPI(args.key_id, args.key_path)
    
    if args.action == 'balance':
        balance = api.get_balance()
        if balance:
            print(f"Balance: ${balance.get('balance', 0) / 100:.2f}")
            print(f"Available: ${balance.get('available_balance', 0) / 100:.2f}")
            print(f"Held: ${balance.get('held_balance', 0) / 100:.2f}")
    
    elif args.action == 'markets':
        markets = api.get_markets(limit=20)
        if markets and 'markets' in markets:
            print("Top Markets:")
            for m in markets['markets'][:10]:
                print(f"  {m['ticker']}: {m['title'][:60]}... (Vol: {m.get('volume', 0)})")
    
    elif args.action == 'positions':
        positions = api.get_positions()
        if positions and 'positions' in positions:
            print("Positions:")
            for p in positions['positions']:
                print(f"  {p['ticker']}: {p['position']} contracts")
    
    elif args.action == 'scan':
        trader = KalshiTrader(api)
        opportunities = trader.scan_opportunities()
        print("Trading Opportunities:")
        for opp in opportunities[:10]:
            print(f"  {opp['ticker']}: {opp['title'][:50]}...")
            print(f"    Bid: {opp['yes_bid']}c | Ask: {opp['yes_ask']}c | Spread: {opp['spread']}c | Vol: {opp['volume']}")
    
    elif args.action == 'trade':
        if not args.ticker or not args.side:
            print("Error: --ticker and --side required for trading")
            return
        
        result = api.place_order(
            ticker=args.ticker,
            side=args.side,
            count=args.count,
            price=args.price
        )
        if result:
            print(f"Order placed: {result}")


if __name__ == "__main__":
    main()
