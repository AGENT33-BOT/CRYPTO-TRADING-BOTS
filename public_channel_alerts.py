"""
CryptoAlpha Alerts - Premium Telegram Channel System
Professional trading alerts for @cryptoalphaalerts1
"""

import requests
import json
from datetime import datetime
from typing import Optional, Dict, List

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = "8651591619:AAGulpeOt66s4TKXEsnDuL-lI2PWkM1G6Ao"
CHANNEL_ID = "@cryptoalphaalerts1"
# =======================================================

# Visual styling templates
STYLES = {
    'header': '╔══════════════════════════════════════════╗',
    'footer': '╚══════════════════════════════════════════╝',
    'divider': '─────────────────────────────────────────',
    'buy_emoji': '🟢',
    'sell_emoji': '🔴',
    'neutral_emoji': '⚪',
    'rocket': '🚀',
    'fire': '🔥',
    'chart': '📊',
    'target': '🎯',
    'warning': '⚠️',
    'bulb': '💡',
    'money': '💰',
    'crown': '👑',
    'crystal': '🔮',
}

class PublicChannelAlerts:
    """Premium alert system for CryptoAlpha channel"""
    
    def __init__(self, bot_token: str = None, channel_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.channel_id = channel_id or CHANNEL_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.sent_alerts = {}
        self.load_alert_history()
        
        if not self.bot_token or not self.channel_id:
            print("⚠️  WARNING: Bot token or channel ID not set!")
    
    def load_alert_history(self):
        """Load sent alerts to prevent spam"""
        try:
            with open('public_channel_alerts.json', 'r') as f:
                self.sent_alerts = json.load(f)
        except:
            self.sent_alerts = {}
    
    def save_alert_history(self):
        """Save alert history"""
        try:
            with open('public_channel_alerts.json', 'w') as f:
                json.dump(self.sent_alerts, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def send_message(self, message: str, parse_mode='HTML', pin: bool = False) -> bool:
        """Send message to public channel"""
        if not self.bot_token or not self.channel_id:
            print("❌ Bot token or channel ID not configured!")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.channel_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True,
                'link_preview_options': {'is_disabled': True}
            }
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                message_id = result.get('result', {}).get('message_id')
                if pin and message_id:
                    self._pin_message(message_id)
                return True
            else:
                print(f"❌ Telegram error: {result.get('description')}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def _pin_message(self, message_id: int):
        """Pin a message in the channel"""
        try:
            url = f"{self.base_url}/pinChatMessage"
            payload = {
                'chat_id': self.channel_id,
                'message_id': message_id,
                'disable_notification': True
            }
            requests.post(url, json=payload, timeout=10)
        except:
            pass
    
    def should_alert(self, alert_key: str, current_price: float, 
                     cooldown_hours: int = 4, price_threshold: float = 0.10) -> bool:
        """Check if we should send alert (deduplication)"""
        
        if alert_key not in self.sent_alerts:
            return True
        
        alert_info = self.sent_alerts[alert_key]
        last_time = datetime.fromisoformat(alert_info.get('time', '2000-01-01'))
        last_price = alert_info.get('price', 0)
        
        hours_since = (datetime.now() - last_time).total_seconds() / 3600
        if hours_since < cooldown_hours:
            return False
        
        if last_price > 0:
            price_change = abs(current_price - last_price) / last_price
            if price_change < price_threshold:
                return False
        
        return True
    
    def record_alert(self, alert_key: str, price: float, data: dict = None):
        """Record that we sent an alert"""
        self.sent_alerts[alert_key] = {
            'time': datetime.now().isoformat(),
            'price': price,
            'data': data or {}
        }
        self.save_alert_history()
    
    def _get_opportunity_context(self, edge: float, price: float, signal: str) -> str:
        """Generate context explaining why this is an opportunity"""
        
        contexts = []
        
        if edge > 0.20:
            contexts.append(f"{STYLES['fire']} <b>High Edge Opportunity:</b> {edge*100:.0f}% mispricing detected")
        elif edge > 0.15:
            contexts.append(f"{STYLES['target']} <b>Strong Edge:</b> {edge*100:.0f}% value gap identified")
        elif edge > 0.10:
            contexts.append(f"{STYLES['bulb']} <b>Moderate Edge:</b> {edge*100:.0f}% potential value")
        
        if "BUY" in signal and price < 0.30:
            contexts.append(f"{STYLES['money']} <b>Asymmetric Bet:</b> Low entry, high upside potential")
        elif "SELL" in signal and price > 0.70:
            contexts.append(f"{STYLES['crown']} <b>Overvalued:</b> Market pricing seems too optimistic")
        
        if price > 0.50:
            contexts.append(f"{STYLES['crystal']} <b>Favorite Position:</b> Market consensus aligns")
        else:
            contexts.append(f"{STYLES['rocket']} <b>Contrarian Play:</b> Against market consensus")
        
        return "\n".join(contexts[:2])
    
    def _get_relevant_hashtags(self, category: str, market: str) -> List[str]:
        """Generate relevant hashtags based on market content"""
        
        base_tags = ["#Polymarket", "#PredictionMarkets", "#CryptoAlpha"]
        
        category_tags = {
            "Politics": ["#Politics", "#Elections", "#Trump", "#CryptoRegulation"],
            "Crypto": ["#Crypto", "#Bitcoin", "#Ethereum", "#Altcoins", "#DeFi"],
            "Sports": ["#Sports", "#NBA", "#NFL", "#Soccer", "#Esports"],
            "Science": ["#Science", "#Tech", "#Innovation", "#Space"],
            "Entertainment": ["#Entertainment", "#Crypto", "#Memes"],
            "Weather": ["#Weather", "#Climate"],
            "Financial": ["#Finance", "#Economy", "#Markets", "#CryptoNews"],
        }
        
        # Add category-specific tags
        cat_key = category.split()[0] if category else ""
        for key, tags in category_tags.items():
            if key.lower() in category.lower():
                base_tags.extend(tags)
                break
        
        # Add market-specific tags
        market_lower = market.lower()
        if any(x in market_lower for x in ["trump", "president", "election", "biden"]):
            base_tags.extend(["#Trump2025", "#USPolitics"])
        if any(x in market_lower for x in ["bitcoin", "btc", "crypto"]):
            base_tags.extend(["#BTC", "#CryptoBets"])
        if any(x in market_lower for x in ["ethereum", "eth"]):
            base_tags.extend(["#ETH", "#Ethereum"])
        
        return list(set(base_tags))[:6]  # Limit to 6 unique tags
    
    def alert_polymarket(self, market: str, signal: str, price: float, 
                         edge: float, volume: float = 0, liquidity: float = 0,
                         end_date: str = "", category: str = "Unknown") -> bool:
        """Post enhanced Polymarket opportunity"""
        
        alert_key = f"poly_{market}_{signal}"
        
        if not self.should_alert(alert_key, price):
            print(f"[SKIP] Skipping duplicate: {market[:50]}...")
            return False
        
        # Determine styling
        is_buy = "BUY" in signal
        emoji = STYLES['buy_emoji'] if is_buy else STYLES['sell_emoji']
        signal_word = "BUY YES" if is_buy else "SELL YES"
        signal_emoji = "🟢 BUY SIGNAL" if is_buy else "🔴 SELL SIGNAL"
        
        # Format price
        implied_prob = price * 100
        
        # Build context
        context = self._get_opportunity_context(edge, price, signal)
        
        # Build hashtags
        hashtags = " ".join(self._get_relevant_hashtags(category, market))
        
        # Format dates if available
        date_info = f"\n<b>📅 Expires:</b> {end_date}" if end_date else ""
        
        # Build the message
        message = f"""{emoji} <b>CRYPTOALPHA POLYMARKET ALERT</b> {emoji}

{STYLES['header']}

<b>📌 MARKET:</b>
{market[:220]}

<b>💎 CATEGORY:</b> {category}

{STYLES['divider']}

<b>{signal_emoji}</b>

<b>💰 Current Price:</b> <code>${price:.4f}</code>
<b>📊 Implied Probability:</b> <code>{implied_prob:.1f}%</code>
<b>🎯 Detected Edge:</b> <code>+{edge*100:.1f}%</code>{date_info}

{STYLES['divider']}

<b>💡 WHY THIS MATTERS:</b>
{context}

{STYLES['divider']}

<b>⚠️ RISK MANAGEMENT:</b>
• This is a PAPER TRADE for tracking
• Position size: Demo only
• Not financial advice - DYOR
• Markets can be unpredictable

{STYLES['footer']}

{hashtags}

<i>🤖 Generated by CryptoAlpha Bot • {datetime.now().strftime('%H:%M %Z')}</i>"""
        
        if self.send_message(message):
            self.record_alert(alert_key, price, {
                'market': market,
                'signal': signal,
                'edge': edge,
                'category': category
            })
            print(f"[OK] Posted premium alert: {market[:50]}...")
            return True
        return False
    
    def alert_crypto(self, symbol: str, side: str, entry: float, 
                     target: float, stop: float, reason: str = "",
                     timeframe: str = "", confidence: str = "Medium") -> bool:
        """Post enhanced crypto setup"""
        
        alert_key = f"crypto_{symbol}_{side}_{entry}"
        
        # Calculate metrics
        rr_ratio = abs(target - entry) / abs(stop - entry) if stop != entry else 0
        profit_pct = ((target - entry) / entry) * 100
        risk_pct = ((stop - entry) / entry) * 100
        
        # Determine styling
        emoji = "🚀" if side == "LONG" else "🩳"
        side_emoji = "🟢 LONG" if side == "LONG" else "🔴 SHORT"
        confidence_emoji = {"High": "🔥", "Medium": "⚡", "Low": "💤"}.get(confidence, "⚡")
        
        # Confidence context
        confidence_text = {
            "High": "Multiple confluence factors detected - strong setup",
            "Medium": "Decent setup with reasonable risk/reward",
            "Low": "Speculative setup - lower position size recommended"
        }.get(confidence, "Standard setup")
        
        timeframe_text = f"<b>⏱️ Timeframe:</b> {timeframe}\n" if timeframe else ""
        
        message = f"""{emoji} <b>CRYPTOALPHA TRADE SETUP</b> {emoji}

{STYLES['header']}

<b>📊 SYMBOL:</b> <code>{symbol}</code>
<b>📈 DIRECTION:</b> {side_emoji}
{timeframe_text}
{STYLES['divider']}

<b>🎯 ENTRY ZONE:</b> <code>${entry:.4f}</code>
<b>✅ TAKE PROFIT:</b> <code>${target:.4f}</code> (+{profit_pct:.1f}%)
<b>🛡️ STOP LOSS:</b> <code>${stop:.4f}</code> ({risk_pct:.1f}%)
<b>⚖️ RISK:REWARD:</b> 1:{rr_ratio:.1f}

{STYLES['divider']}

<b>💡 SETUP RATIONALE:</b>
{reason[:350]}

{STYLES['divider']}

<b>{confidence_emoji} CONFIDENCE:</b> {confidence}
<i>{confidence_text}</i>

<b>⚠️ RISK DISCLAIMER:</b>
• Use proper position sizing (1-2% risk max)
• Never trade without stop loss
• This is educational content
• Markets are inherently unpredictable

{STYLES['footer']}

#CryptoAlpha #{symbol.replace('/', '')} #Trading #Bybit #CryptoSignals #TechnicalAnalysis

<i>🤖 Generated by CryptoAlpha Bot • {datetime.now().strftime('%H:%M %Z')}</i>"""
        
        if self.send_message(message):
            self.record_alert(alert_key, entry)
            print(f"[OK] Posted crypto setup: {symbol}")
            return True
        return False
    
    def send_portfolio_update(self, balance: float, pnl: float, 
                              positions: list, daily_change: float = 0) -> bool:
        """Post enhanced portfolio summary"""
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        change_emoji = "📈" if daily_change >= 0 else "📉"
        
        # Sort positions by PnL
        sorted_positions = sorted(positions, key=lambda x: x.get('pnl', 0), reverse=True)
        
        # Top performers and losers
        top_gainers = [p for p in sorted_positions if p.get('pnl', 0) > 0][:3]
        top_losers = [p for p in sorted(sorted_positions, key=lambda x: x.get('pnl', 0)) if p.get('pnl', 0) < 0][:2]
        
        gainers_text = "\n".join([f"🟢 {p.get('symbol', 'N/A')}: +${p.get('pnl', 0):.2f}" for p in top_gainers]) if top_gainers else "No winners yet"
        losers_text = "\n".join([f"🔴 {p.get('symbol', 'N/A')}: ${p.get('pnl', 0):.2f}" for p in top_losers]) if top_losers else "No losers"
        
        total_positions = len(positions)
        
        message = f"""{STYLES['chart']} <b>CRYPTOALPHA PORTFOLIO UPDATE</b> {STYLES['chart']}

{STYLES['header']}

<b>💼 ACCOUNT SUMMARY</b>

<b>Balance:</b> <code>${balance:,.2f} USDT</code>
<b>Unrealized P&L:</b> {emoji} <code>${pnl:+,.2f}</code>
<b>24H Change:</b> {change_emoji} <code>{daily_change:+.2f}%</code>

{STYLES['divider']}

<b>📊 ACTIVE POSITIONS ({total_positions})</b>

<b>🏆 Top Performers:</b>
{gainers_text}

<b>📉 Attention Needed:</b>
{losers_text}

{STYLES['divider']}

<b>📈 TRADING METRICS</b>
<i>• Updated: {datetime.now().strftime('%H:%M %Z')}</i>
<i>• Strategy: Edge-based prediction markets + crypto</i>
<i>• Risk: Conservative position sizing</i>

{STYLES['footer']}

#CryptoAlpha #Portfolio #Trading #P&L #Bybit

<i>🤖 Automated portfolio tracking • Join the alpha 👇</i>"""
        
        return self.send_message(message)
    
    def send_market_insight(self, title: str, content: str, 
                           importance: str = "Medium") -> bool:
        """Post market analysis/insight"""
        
        importance_emoji = {
            "High": "🔥", 
            "Medium": "💡", 
            "Low": "📌"
        }.get(importance, "💡")
        
        message = f"""{importance_emoji} <b>CRYPTOALPHA MARKET INSIGHT</b> {importance_emoji}

{STYLES['header']}

<b>📰 {title[:150]}</b>

{content[:600]}

{STYLES['footer']}

#CryptoAlpha #MarketAnalysis #CryptoNews #{importance}Priority

<i>🤖 Insight generated at {datetime.now().strftime('%H:%M %Z')}</i>"""
        
        return self.send_message(message)
    
    def send_welcome_message(self, pin: bool = True) -> bool:
        """Send and optionally pin the welcome message"""
        
        message = f"""{STYLES['crown']} <b>WELCOME TO CRYPTOALPHA</b> {STYLES['crown']}

{STYLES['header']}

<b>🎯 What We Do</b>
CryptoAlpha is an automated trading intelligence system that identifies high-probability opportunities in prediction markets and crypto.

{STYLES['divider']}

<b>📊 What You'll Receive</b>

🟢 <b>Polymarket Alerts</b>
   • Markets with &gt;10% edge detected
   • Mispriced opportunities
   • Paper trade tracking

🚀 <b>Crypto Setups</b>
   • Entry/exit levels
   • Risk management
   • R:R analysis

📈 <b>Portfolio Updates</b>
   • P&L tracking
   • Position summaries
   • Performance metrics

💡 <b>Market Insights</b>
   • Analysis and commentary
   • Trend identification
   • Alpha signals

{STYLES['divider']}

<b>⚠️ Important Disclaimers</b>
• All alerts are for EDUCATIONAL purposes
• We use PAPER TRADING (no real money)
• Always DYOR (Do Your Own Research)
• Never risk more than you can afford to lose
• Past performance ≠ future results

{STYLES['divider']}

<b>🤝 Join the Community</b>
• Share your trades
• Discuss setups
• Learn together

<b>📅 Schedule:</b>
Polymarket scans every 30 min
Portfolio updates every 4 hours
Market insights as opportunities arise

{STYLES['footer']}

<b>Questions? Just reply to any message!</b>

#CryptoAlpha #Trading #Crypto #Polymarket

<i>Last updated: {datetime.now().strftime('%B %d, %Y')}</i>"""
        
        return self.send_message(message, pin=pin)
    
    def test_connection(self) -> bool:
        """Test channel connection with premium message"""
        
        message = f"""{STYLES['crown']} <b>CRYPTOALPHA SYSTEM ONLINE</b> {STYLES['crown']}

{STYLES['header']}

✅ Bot connected successfully
✅ Channel permissions verified  
✅ Alert system armed

<b>🚀 Coming Soon:</b>
• Polymarket edge opportunities
• Crypto trading setups
• Portfolio tracking
• Market insights

{STYLES['footer']}

<i>Stay tuned... the alpha is coming.</i>

#CryptoAlpha #Launch"""
        
        return self.send_message(message)
    
    def send_custom_alert(self, title: str, body: str, 
                          emoji: str = "📢", hashtags: str = "#CryptoAlpha") -> bool:
        """Send a custom formatted alert"""
        
        message = f"""{emoji} <b>{title[:100]}</b>

{STYLES['divider']}

{body[:800]}

{STYLES['divider']}

{hashtags}

<i>{datetime.now().strftime('%H:%M %Z')}</i>"""
        
        return self.send_message(message)


# ==================== USAGE EXAMPLE ====================
if __name__ == "__main__":
    alerts = PublicChannelAlerts()
    
    print("🚀 Testing CryptoAlpha Alert System...")
    print("-" * 50)
    
    # Test connection
    if alerts.test_connection():
        print("✅ Test message sent successfully!")
        print("\nYour premium alert channel is ready.")
    else:
        print("❌ Failed to send test message.")
        print("\nPlease check:")
        print("1. Bot token is correct")
        print("2. Channel ID/username is correct")
        print("3. Bot is admin of the channel")
