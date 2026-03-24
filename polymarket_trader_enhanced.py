"""
Enhanced Polymarket Trading Bot - Deduplicated, Multi-Market Scanner
"""

import requests
import json
import time
import logging
import os
from datetime import datetime, timedelta
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
        """Initialize Polymarket trader with deduplication"""
        self.base_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        
        # Trading configuration
        self.config = {
            'max_position_size': 20,
            'max_total_exposure': 100,
            'min_edge': 0.10,
            'min_liquidity': 5000,
            'min_volume': 25000,
        }
        
        # PAPER TRADING MODE - Safety flag
        self.paper_trading = paper_trading
        
        # Alert deduplication
        self.alerted_opportunities = {}
        self.max_alert_count = 3
        self.alert_cooldown_hours = 4
        self.price_change_threshold = 0.10
        self.load_alert_history()
        
        # Load API credentials
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        
        # Track positions
        self.positions = {}
        self.load_positions()
        
        logging.info("=" * 60)
        logging.info("POLYMARKET TRADER INITIALIZED")
        if self.paper_trading:
            logging.info("*** PAPER TRADING MODE - NO REAL MONEY AT RISK ***")
        logging.info("=" * 60)
    
    def load_positions(self):
        """Load existing positions"""
        try:
            with open('polymarket_positions.json', 'r') as f:
                self.positions = json.load(f)
        except:
            self.positions = {}
    
    def save_positions(self):
        """Save positions"""
        try:
            with open('polymarket_positions.json', 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving positions: {e}")
    
    def load_alert_history(self):
        """Load alert history"""
        try:
            with open('polymarket_alerts.json', 'r') as f:
                data = json.load(f)
                self.alerted_opportunities = data.get('alerts', {})
        except:
            self.alerted_opportunities = {}
    
    def save_alert_history(self):
        """Save alert history"""
        try:
            with open('polymarket_alerts.json', 'w') as f:
                json.dump({'alerts': self.alerted_opportunities}, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving alerts: {e}")
    
    def should_send_alert(self, market_id: str, current_price: float) -> bool:
        """Check if alert should be sent"""
        now = datetime.now()
        
        if market_id not in self.alerted_opportunities:
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
        
        # Check max alerts
        if alert_info.get('count', 0) >= self.max_alert_count:
            logging.info(f"Skipping alert - max reached ({self.max_alert_count})")
            return False
        
        # Check cooldown
        last_alert = datetime.fromisoformat(alert_info.get('last_alert', now.isoformat()))
        hours_since = (now - last_alert).total_seconds() / 3600
        
        if hours_since < self.alert_cooldown_hours:
            logging.info(f"Skipping - cooldown ({hours_since:.1f}h < {self.alert_cooldown_hours}h)")
            return False
        
        # Check price change
        last_price = alert_info.get('last_price', current_price)
        change_pct = abs(current_price - last_price) / last_price if last_price > 0 else 0
        
        if change_pct < self.price_change_threshold:
            logging.info(f"Skipping - price stable ({change_pct*100:.1f}% < {self.price_change_threshold*100}%)")
            return False
        
        # Update and allow
        alert_info['count'] += 1
        alert_info['last_alert'] = now.isoformat()
        alert_info['last_price'] = current_price
        alert_info['prices_seen'].append(current_price)
        self.save_alert_history()
        return True
    
    def get_active_markets(self, limit: int = 100) -> List[Dict]:
        """Fetch active markets"""
        try:
            url = f"{self.gamma_url}/markets"
            params = {"active": "true", "closed": "false", "limit": limit}
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get('markets', data.get('data', []))
            return []
        except Exception as e:
            logging.error(f"Error fetching markets: {e}")
            return []
    
    def analyze_market(self, market: Dict) -> Optional[Dict]:
        """Analyze market for opportunity"""
        try:
            market_id = market.get('conditionId')
            question = market.get('question', '')
            
            # Get token IDs
            clob_token_ids = market.get('clobTokenIds', [])
            if isinstance(clob_token_ids, str):
                import json as _json
                clob_token_ids = _json.loads(clob_token_ids)
            
            yes_token_id = clob_token_ids[0] if len(clob_token_ids) > 0 else None
            no_token_id = clob_token_ids[1] if len(clob_token_ids) > 1 else None
            
            # Validate token IDs
            yes_token_id = str(yes_token_id) if yes_token_id and len(str(yes_token_id)) >= 64 else None
            no_token_id = str(no_token_id) if no_token_id and len(str(no_token_id)) >= 64 else None
            
            # Get prices
            outcome_prices = market.get('outcomePrices', [])
            if isinstance(outcome_prices, str):
                import json as _json
                outcome_prices = _json.loads(outcome_prices)
            
            if outcome_prices and len(outcome_prices) >= 2:
                yes_price = float(outcome_prices[0])
                no_price = float(outcome_prices[1])
            else:
                yes_price = market.get('lastTradePrice', 0.5)
                no_price = 1 - yes_price
            
            # Get volume/liquidity
            volume = float(market.get('volumeNum', market.get('volume', 0)))
            liquidity = float(market.get('liquidityNum', market.get('liquidity', 0)))
            
            return {
                'market_id': market_id,
                'question': question,
                'yes_price': yes_price,
                'no_price': no_price,
                'yes_token_id': yes_token_id,
                'no_token_id': no_token_id,
                'implied_probability': yes_price,
                'volume': volume,
                'liquidity': liquidity,
                'end_date': market.get('endDate'),
                'category': market.get('category', 'Unknown')
            }
        except Exception as e:
            logging.error(f"Error analyzing market: {e}")
            return None
    
    def find_opportunities(self) -> List[Dict]:
        """Find opportunities across ALL markets"""
        opportunities = []
        
        logging.info("Scanning ALL active markets...")
        markets = self.get_active_markets(limit=100)
        logging.info(f"Found {len(markets)} markets")
        
        # Interesting categories
        interesting = ['crypto', 'bitcoin', 'ethereum', 'politics', 'sports', 
                      'technology', 'ai', 'finance', 'entertainment', 'gaming']
        
        for market in markets:
            category = market.get('category', '').lower()
            question = market.get('question', '').lower()
            
            # Skip low liquidity
            volume = float(market.get('volumeNum', 0))
            liquidity = float(market.get('liquidityNum', 0))
            
            if volume < 25000 or liquidity < 5000:
                continue
            
            analysis = self.analyze_market(market)
            if not analysis:
                continue
            
            prob = analysis['implied_probability']
            is_interesting = any(cat in category for cat in interesting) or volume > 100000
            
            if not is_interesting:
                continue
            
            # Extreme mispricing (<15% or >85%)
            if prob > 0.85:
                edge = prob - 0.85
                if edge >= 0.10:
                    opportunities.append({
                        **analysis,
                        'signal': 'SELL_YES',
                        'edge': edge,
                        'reason': f'Overpriced YES ({category})'
                    })
            elif prob < 0.15:
                edge = 0.15 - prob
                if edge >= 0.10:
                    opportunities.append({
                        **analysis,
                        'signal': 'BUY_YES',
                        'edge': edge,
                        'reason': f'Underpriced YES ({category})'
                    })
            
            # Moderate mispricing (15-25% or 75-85%)
            elif (prob < 0.25 or prob > 0.75) and volume > 50000:
                if prob < 0.25:
                    edge = 0.25 - prob
                    signal = 'BUY_YES'
                else:
                    edge = prob - 0.75
                    signal = 'SELL_YES'
                
                if edge >= 0.05:
                    opportunities.append({
                        **analysis,
                        'signal': signal,
                        'edge': edge,
                        'reason': f'Value bet ({category})'
                    })
        
        opportunities.sort(key=lambda x: (x['edge'], x['volume']), reverse=True)
        return opportunities[:10]
    
    def execute_paper_trade(self, opportunity: Dict) -> bool:
        """Execute paper trade"""
        try:
            market_id = opportunity.get('market_id')
            signal = opportunity.get('signal')
            yes_price = opportunity.get('yes_price', 0.5)
            
            # Check deduplication
            if not self.should_send_alert(market_id, yes_price):
                logging.info(f"Alert suppressed for {market_id[:20]}...")
                return False
            
            edge = opportunity.get('edge', 0)
            question = opportunity.get('question', 'Unknown')[:50]
            
            trade_size = min(50, 1000 * edge * 0.5)
            
            import uuid
            order_id = f"paper_{uuid.uuid4().hex[:16]}"
            
            # Record position
            self.positions[market_id] = {
                'question': question,
                'signal': signal,
                'size': trade_size,
                'price': yes_price,
                'edge': edge,
                'timestamp': datetime.now().isoformat(),
                'order_id': order_id
            }
            self.save_positions()
            
            # Log and notify
            alert_count = self.alerted_opportunities.get(market_id, {}).get('count', 1)
            
            logging.info("=" * 60)
            logging.info(f"🎯 PAPER TRADE [{alert_count}/3]")
            logging.info(f"Market: {question}")
            logging.info(f"Signal: {signal} | Edge: {edge*100:.1f}%")
            logging.info(f"Size: ${trade_size:.2f} @ ${yes_price:.3f}")
            logging.info("=" * 60)
            
            # Send notification
            self.notify_trade(opportunity, trade_size, order_id)
            
            return True
            
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            return False
    
    def notify_trade(self, opportunity: Dict, size: float, order_id: str):
        """Send notification"""
        try:
            market_id = opportunity.get('market_id')
            signal = opportunity.get('signal')
            question = opportunity.get('question', 'Unknown')[:40]
            edge = opportunity.get('edge', 0) * 100
            alert_count = self.alerted_opportunities.get(market_id, {}).get('count', 1)
            
            # Try Telegram
            try:
                import sys
                sys.path.insert(0, '.')
                from trade_notifier import send_message
                
                message = f"""
🎯 POLYMARKET PAPER TRADE [{alert_count}/3]

Signal: {signal}
Market: {question}...
Size: ${size:.2f}
Edge: {edge:.1f}%
Order: {order_id[:20]}...

{'⚠️ Max alerts reached' if alert_count >= 3 else f'Next alert if price moves >10%'}
"""
                send_message(message)
            except:
                pass
            
            # Save to log file
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'market': question,
                'signal': signal,
                'edge': edge,
                'size': size,
                'alert_count': alert_count
            }
            
            try:
                with open('trading_logs/polymarket_trades.jsonl', 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except:
                pass
                
        except Exception as e:
            logging.error(f"Notification error: {e}")
    
    def scan_and_trade(self, max_trades: int = 2):
        """Scan and execute trades"""
        logging.info("=" * 60)
        logging.info("SCANNING POLYMARKET")
        logging.info("=" * 60)
        
        opportunities = self.find_opportunities()
        
        if not opportunities:
            logging.info("No opportunities found")
            return 0
        
        logging.info(f"\nFound {len(opportunities)} opportunities:\n")
        
        trades = 0
        for i, opp in enumerate(opportunities[:5], 1):
            logging.info(f"{i}. {opp['question'][:60]}...")
            logging.info(f"   Price: ${opp['yes_price']:.3f} ({opp['implied_probability']*100:.1f}%)")
            logging.info(f"   Signal: {opp['signal']} | Edge: {opp['edge']*100:.1f}%")
            logging.info(f"   Reason: {opp['reason']}")
            
            if trades < max_trades and opp.get('signal') in ['BUY_YES', 'SELL_YES']:
                logging.info(f"   EXECUTING...")
                if self.execute_paper_trade(opp):
                    trades += 1
                    logging.info(f"   ✓ TRADE RECORDED")
            
            logging.info("-" * 60)
        
        logging.info(f"\nComplete. Trades: {trades}")
        return trades
    
    def run_once(self):
        """Run single scan"""
        self.scan_and_trade(max_trades=2)

if __name__ == "__main__":
    trader = PolymarketTrader(paper_trading=True)
    trader.run_once()
