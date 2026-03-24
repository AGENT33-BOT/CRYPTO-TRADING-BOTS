"""
Polymarket Trading Bot - Prediction Market Trader
Trades on event outcomes using Polymarket CLOB API
"""

import requests
import json
import time
import logging
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('polymarket_trader.log'),
        logging.StreamHandler()
    ]
)

class PolymarketTrader:
    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None, paper_trading: bool = True):
        """Initialize Polymarket trader
        
        Args:
            api_key: Polymarket API key
            api_secret: Polymarket API secret
            passphrase: Polymarket API passphrase
            paper_trading: If True, simulates trades without real execution (default: True for safety)
        """
        self.base_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        
        # Trading configuration - TEST MODE (lower thresholds)
        self.config = {
            'max_position_size': 20,  # $20 max per trade for testing
            'max_total_exposure': 100,  # $100 max total
            'min_edge': 0.05,  # 5% minimum edge for testing (was 15%)
            'min_liquidity': 5000,  # $5k minimum liquidity
            'min_volume': 25000,  # $25k minimum volume
        }
        
        # PAPER TRADING MODE - Safety flag (default ON)
        self.paper_trading = paper_trading
        
        # Try to load from config file
        try:
            with open('polymarket_config.json', 'r') as f:
                config = json.load(f)
                pm_config = config.get('polymarket', {})
                self.api_key = api_key or pm_config.get('api_key')
                self.api_secret = api_secret or pm_config.get('api_secret')
                self.passphrase = passphrase or pm_config.get('passphrase')
                # Check config for paper_trading override
                if 'paper_trading' in pm_config:
                    self.paper_trading = pm_config.get('paper_trading', True)
                logging.info("Loaded credentials from config.json")
        except:
            # Use provided credentials
            self.api_key = api_key
            self.api_secret = api_secret
            self.passphrase = passphrase
        
        # Track positions and portfolio
        self.positions = {}  # market_id -> position info
        self.active_orders = {}
        self.daily_pnl = 0
        self.daily_trades = 0
        self.last_trade_date = datetime.now().date()
        
        # Load existing positions
        self.load_positions()
        
        # Alert deduplication tracking
        self.alerted_opportunities = {}  # market_id -> {count, last_alert_time, last_price}
        self.max_alert_count = 3  # Max times to alert same opportunity
        self.alert_cooldown_hours = 4  # Hours between repeat alerts
        self.load_alert_history()
        
        logging.info("=" * 60)
        logging.info("POLYMARKET TRADER INITIALIZED")
        
        if self.paper_trading:
            logging.info("*** PAPER TRADING MODE - NO REAL MONEY AT RISK ***")
            logging.info("Trades will be SIMULATED only")
        elif self.api_key:
            logging.info("*** LIVE TRADING MODE - REAL MONEY AT RISK ***")
            logging.info("API credentials loaded")
            logging.info(f"Max position: ${self.config['max_position_size']}")
            logging.info(f"Max exposure: ${self.config['max_total_exposure']}")
        else:
            logging.info("No API credentials - READ ONLY MODE")
            self.paper_trading = True  # Force paper mode if no credentials
        logging.info("=" * 60)
    
    def load_positions(self):
        """Load existing positions from file"""
        try:
            with open('polymarket_positions.json', 'r') as f:
                self.positions = json.load(f)
                logging.info(f"Loaded {len(self.positions)} existing positions")
        except:
            self.positions = {}
    
    def save_positions(self):
        """Save positions to file"""
        try:
            with open('polymarket_positions.json', 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving positions: {e}")
    
    def load_alert_history(self):
        """Load alert history to prevent spam"""
        try:
            with open('polymarket_alerts.json', 'r') as f:
                data = json.load(f)
                self.alerted_opportunities = data.get('alerts', {})
                logging.info(f"Loaded {len(self.alerted_opportunities)} alert history entries")
        except:
            self.alerted_opportunities = {}
    
    def save_alert_history(self):
        """Save alert history"""
        try:
            with open('polymarket_alerts.json', 'w') as f:
                json.dump({'alerts': self.alerted_opportunities}, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving alert history: {e}")
    
    def should_send_alert(self, market_id: str, current_price: float) -> bool:
        """Check if alert should be sent (deduplication logic)"""
        now = datetime.now()
        
        if market_id not in self.alerted_opportunities:
            # First time seeing this opportunity
            self.alerted_opportunities[market_id] = {
                'count': 1,
                'first_seen': now.isoformat(),
                'last_alert': now.isoformat(),
                'last_price': current_price,
                'prices_seen': [current_price]
            }
            self.save_alert_history()
            return True
        
        alert_info = self.alerted_opportunities[market_id]
        
        # Check if we've alerted too many times
        if alert_info.get('count', 0) >= self.max_alert_count:
            logging.info(f"Skipping alert for {market_id[:20]}... - max alerts reached ({self.max_alert_count})")
            return False
        
        # Check cooldown period
        last_alert = datetime.fromisoformat(alert_info.get('last_alert', now.isoformat()))
        hours_since_last = (now - last_alert).total_seconds() / 3600
        
        if hours_since_last < self.alert_cooldown_hours:
            logging.info(f"Skipping alert for {market_id[:20]}... - in cooldown ({hours_since_last:.1f}h < {self.alert_cooldown_hours}h)")
            return False
        
        # Check if price changed significantly (>10% change)
        last_price = alert_info.get('last_price', current_price)
        price_change_pct = abs(current_price - last_price) / last_price if last_price > 0 else 0
        
        if price_change_pct < 0.10:  # Less than 10% change
            logging.info(f"Skipping alert for {market_id[:20]}... - price stable ({price_change_pct*100:.1f}% change)")
            return False
        
        # Update alert info
        alert_info['count'] = alert_info.get('count', 0) + 1
        alert_info['last_alert'] = now.isoformat()
        alert_info['last_price'] = current_price
        alert_info['prices_seen'] = alert_info.get('prices_seen', []) + [current_price]
        
        self.save_alert_history()
        return True
    
    def generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for API requests"""
        if not self.api_secret:
            return ""
        message = timestamp + method + path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_headers(self, method: str = "GET", path: str = "", body: str = "") -> Dict:
        """Get authentication headers"""
        if not self.api_key:
            return {}
        
        timestamp = str(int(time.time() * 1000))
        signature = self.generate_signature(timestamp, method, path, body)
        
        return {
            'POLYMARKET-API-KEY': self.api_key,
            'POLYMARKET-API-PASSPHRASE': self.passphrase or '',
            'POLYMARKET-API-TIMESTAMP': timestamp,
            'POLYMARKET-API-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
    
    def get_balance(self) -> float:
        """Get USDC balance - returns 1000 as default for testing"""
        # Polymarket balance API requires special auth
        # For now, return a default value to allow trading
        # In production, this should call the correct endpoint
        try:
            # Try to get balance from API
            path = "/api/v1/balance"  # Updated endpoint
            headers = self.get_headers("GET", path)
            
            response = requests.get(
                f"{self.base_url}{path}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                balance = float(data.get('balance', 0))
                logging.info(f"USDC Balance: ${balance:.2f}")
                return balance
            else:
                # Log but don't fail - use fallback
                logging.debug(f"Balance API returned {response.status_code}")
        except Exception as e:
            logging.debug(f"Balance check error: {e}")
        
        # Fallback: assume sufficient balance for trading
        # In real trading, you'd want to properly integrate with Polymarket's API
        logging.info("Using fallback balance: $1000 (API not fully integrated)")
        return 1000.0  # Default fallback
    
    def get_total_exposure(self) -> float:
        """Calculate total position exposure"""
        total = 0
        for pos in self.positions.values():
            total += float(pos.get('size', 0))
        return total
    
    def can_trade(self, size: float) -> bool:
        """Check if we can place a trade"""
        # Check API credentials
        if not self.api_key:
            logging.warning("No API credentials - cannot trade")
            return False
        
        # Check daily reset
        current_date = datetime.now().date()
        if current_date != self.last_trade_date:
            self.daily_pnl = 0
            self.daily_trades = 0
            self.last_trade_date = current_date
            logging.info("New day - daily stats reset")
        
        # Check balance
        balance = self.get_balance()
        if balance < size:
            logging.warning(f"Insufficient balance: ${balance:.2f} < ${size:.2f}")
            return False
        
        # Check max position size
        if size > self.config['max_position_size']:
            logging.warning(f"Position size ${size:.2f} exceeds max ${self.config['max_position_size']}")
            return False
        
        # Check total exposure
        current_exposure = self.get_total_exposure()
        if current_exposure + size > self.config['max_total_exposure']:
            logging.warning(f"Max exposure reached: ${current_exposure:.2f} / ${self.config['max_total_exposure']}")
            return False
        
        return True
    
    def place_order(self, market_id: str, side: str, size: float, price: float = None, token_id: str = None) -> Dict:
        """Place an order on Polymarket CLOB"""
        try:
            # PAPER TRADING MODE: Simulate trade without real execution
            if self.paper_trading:
                logging.info("[PAPER TRADE] Simulating order execution")
                import uuid
                mock_order_id = f"paper_{uuid.uuid4().hex[:16]}"
                return {
                    'orderId': mock_order_id,
                    'status': 'simulated',
                    'size': size,
                    'price': price or 0.5,
                    'token_id': token_id,
                    'paper_trade': True
                }
            
            # Load private key from config
            private_key = None
            try:
                with open('polymarket_config.json', 'r') as f:
                    config = json.load(f)
                    private_key = config.get('polymarket', {}).get('private_key', '')
                    # Validate key format
                    if private_key and (not private_key.startswith('0x') or len(private_key) != 66):
                        private_key = None
            except:
                pass
            
            if not private_key:
                logging.warning("LIVE TRADING NOT CONFIGURED")
                logging.warning("Add private_key to polymarket_config.json")
                return {}
            
            if not token_id:
                logging.error("No token_id provided - cannot place order")
                return {}
            
            # Use py-clob-client for live trading
            try:
                from py_clob_client.client import ClobClient
                from py_clob_client.clob_types import ApiCreds, OrderArgs
                
                # Initialize client with private key
                client = ClobClient(
                    host=self.base_url,
                    key=private_key,
                    chain_id=137,  # Polygon
                    creds=ApiCreds(
                        api_key=self.api_key,
                        api_secret=self.api_secret,
                        api_passphrase=self.passphrase
                    )
                )
                
                # Set allowance if needed (one-time)
                try:
                    client.set_allowance()
                    logging.info("Allowance set")
                except Exception as e:
                    logging.debug(f"Allowance check: {e}")
                
                # Create order arguments
                # Price is in cents (0-1 range, where 1 = $1.00)
                # Minimum price on Polymarket is 0.001 ($0.001)
                order_price = price if price else 0.5
                
                # Ensure price meets minimum requirements
                if order_price < 0.001:
                    order_price = 0.001
                if order_price > 0.999:
                    order_price = 0.999
                
                logging.info(f"Adjusted price: {order_price:.3f}")
                
                order_args = OrderArgs(
                    price=order_price,
                    size=size,
                    side=side.upper(),  # 'BUY' or 'SELL' (must be uppercase)
                    token_id=token_id
                )
                
                logging.info(f"Creating {side} order: ${size:.2f} @ {order_price:.3f}")
                
                # Create the signed order
                signed_order = client.create_order(order_args)
                
                # Submit the order
                result = client.post_order(signed_order)
                
                if result and result.get('orderID'):
                    order_id = result.get('orderID')
                    logging.info(f"ORDER PLACED SUCCESSFULLY: {order_id}")
                    logging.info(f"Status: {result.get('status', 'unknown')}")
                    return {
                        'orderId': order_id,
                        'status': result.get('status', 'open'),
                        'size': size,
                        'price': order_price,
                        'token_id': token_id
                    }
                else:
                    logging.error(f"Order submission failed: {result}")
                    return {}
                
            except ImportError as e:
                logging.error(f"py-clob-client not installed: {e}")
                return {}
            except Exception as e:
                logging.error(f"CLOB error: {e}")
                import traceback
                logging.error(traceback.format_exc())
                return {}
                
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return {}
    
    def execute_trade(self, opportunity: Dict) -> bool:
        """Execute a trade based on opportunity"""
        signal = opportunity.get('signal')
        edge = opportunity.get('edge', 0)
        market_id = opportunity.get('market_id')
        question = opportunity.get('question', 'Unknown')[:50]
        
        # Validate signal
        if signal not in ['BUY_YES', 'SELL_YES']:
            logging.info(f"Signal {signal} is not actionable - skipping")
            return False
        
        # Check minimum edge
        if edge < self.config['min_edge']:
            logging.info(f"Edge {edge*100:.1f}% below minimum {self.config['min_edge']*100:.1f}% - skipping")
            return False
        
        # Check liquidity
        liquidity = opportunity.get('liquidity', 0)
        if liquidity < self.config['min_liquidity']:
            logging.info(f"Liquidity ${liquidity:,.0f} below minimum ${self.config['min_liquidity']:,.0f} - skipping")
            return False
        
        # Check volume
        volume = opportunity.get('volume', 0)
        if volume < self.config['min_volume']:
            logging.info(f"Volume ${volume:,.0f} below minimum ${self.config['min_volume']:,.0f} - skipping")
            return False
        
        # Determine trade size (Kelly criterion simplified)
        balance = self.get_balance()
        kelly_fraction = edge / 0.5  # Simplified Kelly
        trade_size = min(
            balance * kelly_fraction * 0.25,  # Quarter Kelly, capped
            self.config['max_position_size'],
            liquidity * 0.01  # Max 1% of liquidity
        )
        
        # Minimum trade size
        if trade_size < 5:
            logging.info(f"Trade size ${trade_size:.2f} too small - skipping")
            return False
        
        # Check if we can trade
        if not self.can_trade(trade_size):
            return False
        
        # Execute the trade
        if signal == 'BUY_YES':
            side = 'buy'
            token_id = opportunity.get('yes_token_id')
            trade_price = opportunity.get('yes_price', 0.5)
        else:  # SELL_YES (buy NO)
            side = 'buy'
            token_id = opportunity.get('no_token_id')
            trade_price = opportunity.get('no_price', 0.5)
        
        if not token_id:
            logging.error(f"No token_id for {signal} - cannot trade")
            return False
        
        logging.info("=" * 60)
        logging.info(f"EXECUTING TRADE: {signal}")
        logging.info(f"Market: {question}")
        logging.info(f"Edge: {edge*100:.1f}% | Size: ${trade_size:.2f}")
        logging.info(f"Price: ${trade_price:.3f}")
        logging.info(f"Token: {token_id[:20]}...")
        logging.info("=" * 60)
        
        result = self.place_order(market_id, side, trade_size, trade_price, token_id)
        
        if result and result.get('orderId'):
            # Record position
            self.positions[market_id] = {
                'question': question,
                'side': side,
                'signal': signal,
                'size': trade_size,
                'entry_price': trade_price,
                'edge': edge,
                'timestamp': datetime.now().isoformat(),
                'order_id': result.get('orderId'),
                'token_id': token_id,
                'status': result.get('status', 'open')
            }
            self.save_positions()
            
            self.daily_trades += 1
            logging.info(f"Trade recorded. Daily trades: {self.daily_trades}")
            
            # Send notification (if Telegram configured)
            self.notify_trade(opportunity, trade_size, result.get('orderId'))
            
            return True
        else:
            logging.error("Trade execution failed")
            return False
    
    def notify_trade(self, opportunity: Dict, size: float, order_id: str):
        """Send trade notification with deduplication"""
        try:
            market_id = opportunity.get('market_id')
            yes_price = opportunity.get('yes_price', 0.5)
            
            # Check if we should send alert (deduplication)
            if not self.should_send_alert(market_id, yes_price):
                logging.info(f"Notification suppressed - already alerted for {market_id[:20]}...")
                return
            
            # Try to send to Telegram if notifier exists
            import sys
            sys.path.insert(0, '.')
            from trade_notifier import send_message
            
            signal = opportunity.get('signal')
            question = opportunity.get('question', 'Unknown')[:40]
            edge = opportunity.get('edge', 0) * 100
            alert_count = self.alerted_opportunities.get(market_id, {}).get('count', 1)
            
            message = f"""
🎯 POLYMARKET {'[' + str(alert_count) + '/' + str(self.max_alert_count) + '] ' if alert_count > 1 else ''}PAPER TRADE

Signal: {signal}
Market: {question}...
Size: ${size:.2f}
Edge: {edge:.1f}%
Order ID: {order_id[:20]}...

Daily Trades: {self.daily_trades}

{'⚠️ Max alerts reached for this opportunity' if alert_count >= self.max_alert_count else 'Will alert again if price changes >10%'}
            """
            send_message(message)
            logging.info(f"Notification sent for {market_id[:20]}... (alert {alert_count}/{self.max_alert_count})")
        except Exception as e:
            logging.debug(f"Notification skipped: {e}")
    
    def close_position(self, market_id: str) -> bool:
        """Close an existing position"""
        if market_id not in self.positions:
            logging.warning(f"No position found for {market_id}")
            return False
        
        pos = self.positions[market_id]
        current_side = pos.get('side')
        size = pos.get('size', 0)
        
        # Opposite side to close
        close_side = 'SELL' if current_side == 'BUY' else 'BUY'
        
        logging.info(f"Closing position: {close_side} ${size:.2f}")
        
        result = self.place_order(market_id, close_side, size)
        
        if result and result.get('orderId'):
            del self.positions[market_id]
            self.save_positions()
            logging.info("Position closed successfully")
            return True
        else:
            logging.error("Failed to close position")
            return False
    
    def get_active_markets(self, limit: int = 50) -> List[Dict]:
        """Fetch active prediction markets"""
        try:
            url = f"{self.gamma_url}/markets"
            params = {
                "active": "true",
                "closed": "false",
                "limit": limit
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            # Handle different API response formats
            if isinstance(data, list):
                markets = data
            elif isinstance(data, dict):
                markets = data.get('markets', data.get('data', []))
            else:
                markets = []
            
            logging.info(f"Found {len(markets)} active markets")
            return markets
            
        except Exception as e:
            logging.error(f"Error fetching markets: {e}")
            return []
    
    def get_crypto_markets(self) -> List[Dict]:
        """Filter for crypto-related markets"""
        markets = self.get_active_markets(limit=100)
        
        crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'solana', 'sol', 'cardano', 'ada']
        crypto_markets = []
        
        for market in markets:
            title = market.get('question', '').lower()
            if any(keyword in title for keyword in crypto_keywords):
                crypto_markets.append(market)
        
        logging.info(f"Found {len(crypto_markets)} crypto-related markets")
        return crypto_markets
    
    def get_market_orderbook(self, market_id: str) -> Dict:
        """Fetch orderbook for a specific market"""
        try:
            url = f"{self.base_url}/book"
            params = {"market": market_id}
            
            response = requests.get(url, params=params, timeout=30)
            return response.json()
            
        except Exception as e:
            logging.error(f"Error fetching orderbook: {e}")
            return {}
    
    def analyze_market(self, market: Dict) -> Dict:
        """Analyze a prediction market for trading opportunity"""
        market_id = market.get('conditionId')
        question = market.get('question', '')
        
        # Get token IDs from clobTokenIds array
        # Index 0 = Yes, Index 1 = No
        clob_token_ids = market.get('clobTokenIds', [])
        
        # Debug logging
        logging.debug(f"Market: {question[:50]}...")
        logging.debug(f"Raw clobTokenIds: {clob_token_ids} (type: {type(clob_token_ids)})")
        
        # Handle case where clobTokenIds is a string (JSON array)
        if isinstance(clob_token_ids, str):
            try:
                import json
                clob_token_ids = json.loads(clob_token_ids)
                logging.debug(f"Parsed clobTokenIds from string: {clob_token_ids}")
            except Exception as e:
                logging.debug(f"Failed to parse clobTokenIds string: {e}")
                clob_token_ids = []
        
        # Ensure it's a list
        if not isinstance(clob_token_ids, list):
            logging.debug(f"clobTokenIds is not a list, attempting conversion")
            # Try to convert to list if it's a dict or other type
            if isinstance(clob_token_ids, dict):
                # Some markets store it as a dict with 'yes'/'no' keys
                yes_token_id = clob_token_ids.get('yes') or clob_token_ids.get('0')
                no_token_id = clob_token_ids.get('no') or clob_token_ids.get('1')
                clob_token_ids = [yes_token_id, no_token_id]
            else:
                clob_token_ids = []
        
        # Extract token IDs
        yes_token_id = None
        no_token_id = None
        
        if len(clob_token_ids) > 0:
            yes_token_id = clob_token_ids[0]
        if len(clob_token_ids) > 1:
            no_token_id = clob_token_ids[1]
        
        # Clean token IDs - handle nested lists
        if yes_token_id and isinstance(yes_token_id, list):
            yes_token_id = yes_token_id[0] if len(yes_token_id) > 0 else None
        if no_token_id and isinstance(no_token_id, list):
            no_token_id = no_token_id[0] if len(no_token_id) > 0 else None
        
        # Ensure token IDs are valid strings (Polymarket token IDs are 64-77 hex characters)
        yes_token_id = str(yes_token_id) if yes_token_id and len(str(yes_token_id)) >= 64 else None
        no_token_id = str(no_token_id) if no_token_id and len(str(no_token_id)) >= 64 else None
        
        logging.debug(f"Extracted - Yes: {yes_token_id[:20] if yes_token_id else 'None'}..., No: {no_token_id[:20] if no_token_id else 'None'}...")
        
        # If clobTokenIds is empty, try alternative sources
        if not yes_token_id or not no_token_id:
            logging.debug("Trying alternative token ID sources...")
            
            # Try outcomes array
            outcomes = market.get('outcomes', [])
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except:
                    outcomes = []
            
            if outcomes and len(outcomes) >= 2:
                if not yes_token_id:
                    yes_token_id = outcomes[0].get('token_id') if isinstance(outcomes[0], dict) else None
                if not no_token_id:
                    no_token_id = outcomes[1].get('token_id') if isinstance(outcomes[1], dict) else None
            
            # Try from conditionId and outcomeIndex
            if not yes_token_id and market_id:
                # Construct token ID from condition (this is a fallback)
                logging.debug(f"Using conditionId fallback for market {market_id}")
        
        # Final validation
        if not yes_token_id or not no_token_id:
            logging.warning(f"Could not extract valid token IDs for market: {question[:50]}...")
        
        # Get prices from outcomePrices
        outcome_prices = market.get('outcomePrices', [])
        
        # Handle case where outcomePrices is a string
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except:
                outcome_prices = []
        
        if outcome_prices and len(outcome_prices) >= 2:
            yes_price = float(outcome_prices[0])
            no_price = float(outcome_prices[1])
        else:
            # Fallback to bestBid/bestAsk
            yes_price = market.get('lastTradePrice', 0.5)
            no_price = 1 - yes_price
        
        # Calculate implied probability
        implied_prob = yes_price
        
        # Get volume and liquidity
        volume = float(market.get('volumeNum', market.get('volume', 0)))
        liquidity = float(market.get('liquidityNum', market.get('liquidity', 0)))
        
        # Determine if there's an edge
        analysis = {
            'market_id': market_id,
            'question': question,
            'yes_price': yes_price,
            'no_price': no_price,
            'yes_token_id': yes_token_id,
            'no_token_id': no_token_id,
            'implied_probability': implied_prob,
            'volume': volume,
            'liquidity': liquidity,
            'end_date': market.get('endDate'),
            'category': market.get('category')
        }
        
        return analysis
    
    def find_opportunities(self, min_edge: float = 0.1) -> List[Dict]:
        """Find trading opportunities with edge across ALL markets"""
        opportunities = []
        
        # Scan ALL active markets (not just crypto)
        logging.info("Scanning ALL active markets for opportunities...")
        all_markets = self.get_active_markets(limit=100)
        
        # Also get crypto markets as a subset
        crypto_markets = self.get_crypto_markets()
        crypto_questions = {m.get('question', '').lower() for m in crypto_markets}
        
        logging.info(f"Scanning {len(all_markets)} total markets ({len(crypto_markets)} crypto-related)")
        
        # Categories we're interested in (expand beyond just crypto)
        interesting_categories = [
            'crypto', 'bitcoin', 'ethereum', 'politics', 'us-politics', 'sports',
            'technology', 'ai', 'finance', 'business', 'entertainment', 'gaming'
        ]
        
        for market in all_markets:
            question = market.get('question', '').lower()
            category = market.get('category', '').lower()
            
            # Skip markets with very low liquidity or volume
            volume = float(market.get('volumeNum', market.get('volume', 0)))
            liquidity = float(market.get('liquidityNum', market.get('liquidity', 0)))
            
            if volume < 25000 or liquidity < 5000:
                continue  # Skip illiquid markets
            
            analysis = self.analyze_market(market)
            prob = analysis['implied_probability']
            
            # Check if this is an interesting category or high volume
            is_interesting = any(cat in category for cat in interesting_categories) or volume > 100000
            
            if not is_interesting:
                continue  # Skip uninteresting markets
            
            # Opportunity: Extreme mispricing (<15% or >85%)
            if prob > 0.85:  # Market very confident YES
                if self.check_value_proposition(analysis, 'NO'):
                    edge = prob - 0.85
                    if edge >= min_edge:
                        opportunities.append({
                            **analysis,
                            'signal': 'SELL_YES',
                            'edge': edge,
                            'reason': f'Overpriced YES ({category})',
                            'is_crypto': question in crypto_questions
                        })
                    
            elif prob < 0.15:  # Market very confident NO
                if self.check_value_proposition(analysis, 'YES'):
                    edge = 0.15 - prob
                    if edge >= min_edge:
                        opportunities.append({
                            **analysis,
                            'signal': 'BUY_YES',
                            'edge': edge,
                            'reason': f'Underpriced YES ({category})',
                            'is_crypto': question in crypto_questions
                        })
            
            # Opportunity: Moderate mispricing (15-25% or 75-85%)
            elif (prob < 0.25 or prob > 0.75) and volume > 50000:
                if prob < 0.25:
                    edge = 0.25 - prob
                    signal = 'BUY_YES'
                    reason = f'Undervalued YES ({category})'
                else:
                    edge = prob - 0.75
                    signal = 'SELL_YES'
                    reason = f'Overvalued YES ({category})'
                
                if edge >= min_edge * 0.5:  # Lower threshold for moderate edges
                    opportunities.append({
                        **analysis,
                        'signal': signal,
                        'edge': edge,
                        'reason': reason,
                        'is_crypto': question in crypto_questions
                    })
        
        # Sort by edge (highest first), then by volume
        opportunities.sort(key=lambda x: (x['edge'], x['volume']), reverse=True)
        
        # Log summary
        crypto_count = sum(1 for o in opportunities if o.get('is_crypto'))
        other_count = len(opportunities) - crypto_count
        logging.info(f"Found {len(opportunities)} opportunities ({crypto_count} crypto, {other_count} other)")
        
        return opportunities[:15]  # Top 15 opportunities
    
    def check_value_proposition(self, analysis: Dict, side: str) -> bool:
        """Check if there's actual value in the bet"""
        # Factors to consider:
        # 1. Time to resolution (closer = more certain)
        # 2. Volume (higher = more reliable)
        # 3. Liquidity (can we exit?)
        
        days_to_resolution = self.get_days_to_resolution(analysis['end_date'])
        
        if days_to_resolution < 7:  # Less than a week
            return False  # Too close to bet against consensus
        
        if analysis['volume'] < 50000:  # Low volume
            return False  # Not enough market confidence
        
        if analysis['liquidity'] < 10000:  # Low liquidity
            return False  # Can't exit easily
        
        return True
    
    def get_days_to_resolution(self, end_date: str) -> int:
        """Calculate days until market resolution"""
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            now = datetime.now().astimezone()
            diff = (end - now).days
            return max(diff, 0)
        except:
            return 30  # Default
    
    def scan_and_trade(self, max_trades: int = 2):
        """Scan and execute trades"""
        logging.info("=" * 60)
        logging.info("SCANNING POLYMARKET FOR TRADING OPPORTUNITIES")
        logging.info(f"Max trades this scan: {max_trades}")
        logging.info(f"Current positions: {len(self.positions)}")
        logging.info(f"Total exposure: ${self.get_total_exposure():.2f}")
        logging.info("=" * 60)
        
        opportunities = self.find_opportunities()
        
        if not opportunities:
            logging.info("No opportunities found")
            return 0
        
        logging.info(f"\nFound {len(opportunities)} opportunities:\n")
        
        trades_executed = 0
        
        for i, opp in enumerate(opportunities, 1):
            logging.info(f"{i}. {opp['question'][:60]}...")
            logging.info(f"   YES Price: ${opp['yes_price']:.3f} ({opp['implied_probability']*100:.1f}%)")
            logging.info(f"   Signal: {opp['signal']} | Edge: {opp['edge']*100:.1f}%")
            logging.info(f"   Volume: ${opp['volume']:,.0f} | Liquidity: ${opp['liquidity']:,.0f}")
            logging.info(f"   Reason: {opp['reason']}")
            
            # Check if we already have a position on this market
            market_id = opp.get('market_id')
            if market_id in self.positions:
                logging.info(f"   SKIPPED: Already have position")
                logging.info("-" * 60)
                continue
            
            # Try to execute trade if we haven't reached max
            if trades_executed < max_trades and opp.get('signal') in ['BUY_YES', 'SELL_YES']:
                logging.info(f"   EXECUTING TRADE...")
                if self.execute_trade(opp):
                    trades_executed += 1
                    logging.info(f"   TRADE EXECUTED ✓")
                else:
                    logging.info(f"   TRADE FAILED ✗")
            
            logging.info("-" * 60)
        
        logging.info(f"\nScan complete. Trades executed: {trades_executed}")
        return trades_executed
    
    def run_trading_loop(self, scan_interval: int = 300, max_trades_per_scan: int = 2):
        """Run continuous trading loop"""
        logging.info("=" * 60)
        logging.info("STARTING POLYMARKET TRADING BOT")
        logging.info(f"Scan interval: {scan_interval}s")
        logging.info(f"Max trades per scan: {max_trades_per_scan}")
        logging.info("=" * 60)
        
        try:
            while True:
                self.scan_and_trade(max_trades=max_trades_per_scan)
                
                logging.info(f"\n⏱️  Next scan in {scan_interval} seconds...")
                logging.info(f"💼 Active positions: {len(self.positions)}")
                logging.info(f"💰 Daily trades: {self.daily_trades}")
                logging.info("=" * 60 + "\n")
                
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            logging.info("\n🛑 Trading bot stopped by user")
            self.save_positions()
        except Exception as e:
            logging.error(f"Error in trading loop: {e}")
            self.save_positions()

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Polymarket Trading Bot')
    parser.add_argument('--live', action='store_true', 
                        help='Enable LIVE trading (default: paper trading)')
    parser.add_argument('--interval', type=int, default=300,
                        help='Scan interval in seconds (default: 300)')
    parser.add_argument('--max-trades', type=int, default=2,
                        help='Max trades per scan (default: 2)')
    args = parser.parse_args()
    
    # SAFETY: Default to paper trading unless explicitly enabled with --live
    paper_mode = not args.live
    
    # Create trader instance
    trader = PolymarketTrader(paper_trading=paper_mode)
    
    if paper_mode:
        logging.info("MODE: PAPER TRADING (simulated - no real money)")
        logging.info("Use --live flag to enable real trading (requires valid API credentials)")
    else:
        logging.info("MODE: LIVE TRADING (REAL MONEY AT RISK)")
        logging.warning("⚠️  MAKE SURE YOU HAVE:")
        logging.warning("   1. Valid API credentials")
        logging.warning("   2. USDC.e deposited on Polygon")
        logging.warning("   3. Approved token spend allowance")
        input("Press Enter to confirm and continue...")
    
    trader.run_trading_loop(scan_interval=args.interval, max_trades_per_scan=args.max_trades)
