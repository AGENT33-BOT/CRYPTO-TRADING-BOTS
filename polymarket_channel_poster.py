"""
Polymarket Scanner to Public Channel Poster
Formats and posts scanner results to @cryptoalphaalerts1
"""

import requests
import json
from datetime import datetime
from typing import List, Dict

# Configuration
TELEGRAM_BOT_TOKEN = "8651591619:AAGulpeOt66s4TKXEsnDuL-lI2PWkM1G6Ao"
CHANNEL_ID = "@cryptoalphaalerts1"

class PolymarketChannelPoster:
    """Posts formatted scanner results to public channel"""
    
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self.sent_scans = set()
        self.load_history()
    
    def load_history(self):
        """Load sent scan IDs to prevent duplicates"""
        try:
            with open('polymarket_scan_posts.json', 'r') as f:
                data = json.load(f)
                self.sent_scans = set(data.get('scan_ids', []))
        except:
            self.sent_scans = set()
    
    def save_history(self):
        """Save sent scan IDs"""
        try:
            with open('polymarket_scan_posts.json', 'w') as f:
                json.dump({'scan_ids': list(self.sent_scans)}, f)
        except:
            pass
    
    def send_message(self, message: str, parse_mode='HTML') -> bool:
        """Send message to Telegram channel"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': CHANNEL_ID,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.json().get('ok', False)
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def format_scan_results(self, timestamp: str, markets_scanned: int, 
                           opportunities: List[Dict], trades_executed: int) -> str:
        """Format scanner results for channel"""
        
        # Header
        message = f"""🎯 <b>POLYMARKET SCAN RESULTS</b>
<i>{timestamp}</i>

📊 <b>Summary:</b>
• Markets scanned: {markets_scanned}
• Opportunities found: {len(opportunities)}
• Paper trades executed: {trades_executed}

"""
        
        # Opportunities section
        if opportunities:
            message += "🔍 <b>Top Opportunities:</b>\n\n"
            
            for i, opp in enumerate(opportunities[:5], 1):
                question = opp.get('question', 'Unknown')[:60]
                price = opp.get('yes_price', 0)
                signal = opp.get('signal', 'N/A')
                edge = opp.get('edge', 0) * 100
                status = opp.get('status', 'Active')
                
                # Signal emoji
                emoji = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "⚪"
                
                message += f"{emoji} <b>{question}...</b>\n"
                message += f"   Price: ${price:.3f} | Edge: +{edge:.1f}%\n"
                message += f"   Signal: {signal} | Status: {status}\n\n"
        else:
            message += "🔍 No actionable opportunities found in this scan.\n\n"
        
        # Footer
        message += """—
<i>Paper trading mode - No real money at risk
Alerts are educational, not financial advice</i>

#Polymarket #PredictionMarkets #EdgeTrading"""
        
        return message
    
    def post_scan_results(self, timestamp: str, markets_scanned: int,
                          opportunities: List[Dict], trades_executed: int) -> bool:
        """Main method to post scan results"""
        
        # Create unique ID for this scan
        scan_id = f"{timestamp}_{markets_scanned}_{len(opportunities)}"
        
        # Check if already posted
        if scan_id in self.sent_scans:
            print(f"Scan already posted: {scan_id}")
            return False
        
        # Format message
        message = self.format_scan_results(
            timestamp=timestamp,
            markets_scanned=markets_scanned,
            opportunities=opportunities,
            trades_executed=trades_executed
        )
        
        # Send to channel
        if self.send_message(message):
            self.sent_scans.add(scan_id)
            self.save_history()
            print("Scan results posted to channel")
            return True
        else:
            print("Failed to post scan results")
            return False
    
    def post_simple_alert(self, market: str, signal: str, price: float, 
                         edge: float, category: str = "Unknown") -> bool:
        """Post single opportunity alert"""
        
        emoji = "🟢" if "BUY" in signal else "🔴"
        
        message = f"""{emoji} <b>POLYMARKET OPPORTUNITY</b>

<b>Market:</b> {market[:150]}
<b>Category:</b> {category}
<b>Signal:</b> {signal}
<b>Price:</b> ${price:.4f} ({price*100:.2f}% implied)
<b>Edge:</b> +{edge*100:.1f}%

<i>📊 Paper trade executed for tracking
⚠️ Not financial advice - DYOR</i>

#Polymarket #PredictionMarkets #{category.replace(' ', '').replace('&', '')}"""
        
        return self.send_message(message)


# Integration function for polymarket_trader_enhanced.py
def post_to_public_channel(timestamp: str, markets_scanned: int, 
                           opportunities: List[Dict], trades_executed: int):
    """Call this from the scanner to auto-post results"""
    poster = PolymarketChannelPoster()
    return poster.post_scan_results(timestamp, markets_scanned, 
                                    opportunities, trades_executed)


if __name__ == "__main__":
    # Test posting
    poster = PolymarketChannelPoster()
    
    # Example scan results - use unique timestamp
    from datetime import datetime
    unique_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")
    
    test_opportunities = [
        {
            'question': 'Indiana Pacers win 2026 NBA Finals',
            'yes_price': 0.001,
            'signal': 'BUY_YES',
            'edge': 0.149,
            'status': 'On cooldown'
        },
        {
            'question': 'Sacramento Kings win 2026 NBA Finals',
            'yes_price': 0.001,
            'signal': 'BUY_YES',
            'edge': 0.149,
            'status': 'On cooldown'
        }
    ]
    
    success = poster.post_scan_results(
        timestamp=unique_time,
        markets_scanned=100,
        opportunities=test_opportunities,
        trades_executed=0
    )
    
    if success:
        print("Test scan results posted successfully!")
    else:
        print("Failed to post test results")
