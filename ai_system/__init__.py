"""
AI Trading System - Main Controller
Coordinates all AI/ML components for autonomous trading
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from .signal_aggregator import SignalAggregator
from .ml_predictor import MLPredictor
from .sentiment_analyzer import SentimentAnalyzer
from .volatility_adapter import VolatilityAdapter
from .time_filter import TimeFilter
from .correlation_detector import CorrelationDetector
from .position_manager import PositionManager
from .risk_manager import RiskManager
from .config import TRADING_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AITradingSystem:
    """
    Main AI Trading System that coordinates all components:
    - ML Price Predictor
    - Signal Aggregator (RSI, MACD, BB, etc.)
    - Sentiment Analyzer (News)
    - Volatility Adapter (ATR-based TP/SL)
    - Time Filter (Volume-based)
    - Correlation Detector (BTC direction)
    - Risk Manager
    - Position Manager
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Initialize all components
        self.signal_aggregator = SignalAggregator()
        self.ml_predictor = MLPredictor()
        self.sentiment = SentimentAnalyzer()
        self.volatility = VolatilityAdapter()
        self.time_filter = TimeFilter()
        self.correlation = CorrelationDetector()
        self.position_manager = PositionManager(api_key, api_secret)
        self.risk_manager = RiskManager()
        
        # Trading state
        self.is_running = False
        self.last_analysis = {}
        self.trade_signals = []
        
        logger.info("🤖 AI Trading System initialized")
    
    async def analyze_market(self, symbol: str) -> Dict:
        """Run comprehensive market analysis"""
        logger.info(f"📊 Analyzing {symbol}...")
        
        # 1. Get price data
        price_data = await self._get_price_data(symbol)
        
        # 2. Generate technical signals
        signals = self.signal_aggregator.analyze(price_data)
        
        # 3. ML Prediction
        ml_prediction = await self.ml_predictor.predict(price_data)
        
        # 4. Sentiment Analysis
        sentiment = await self.sentiment.analyze(symbol)
        
        # 5. Volatility Analysis
        volatility = self.volatility.analyze(price_data)
        
        # 6. Time Filter
        time_ok = self.time_filter.is_trading_allowed()
        
        # 7. Correlation with BTC
        btc_correlation = await self.correlation.get_direction(symbol)
        
        # Combine all signals
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'technical_signals': signals,
            'ml_prediction': ml_prediction,
            'sentiment': sentiment,
            'volatility': volatility,
            'time_ok': time_ok,
            'btc_correlation': btc_correlation,
        }
        
        self.last_analysis[symbol] = analysis
        return analysis
    
    async def generate_signal(self, symbol: str) -> Optional[Dict]:
        """Generate trade signal based on all indicators"""
        
        # Run analysis
        analysis = await self.analyze_market(symbol)
        
        # Calculate composite score
        score = self._calculate_composite_score(analysis)
        
        # Check risk management
        risk_ok, risk_msg = self.risk_manager.check_risk(score)
        
        if not risk_ok:
            logger.warning(f"⚠️ Risk check failed: {risk_msg}")
            return None
        
        # Generate signal
        if score['action'] == 'BUY' and score['confidence'] >= TRADING_CONFIG['min_confidence']:
            signal = {
                'action': 'BUY',
                'symbol': symbol,
                'confidence': score['confidence'],
                'reasons': score['reasons'],
                'tp_percent': analysis['volatility']['recommended_tp'],
                'sl_percent': analysis['volatility']['recommended_sl'],
                'size_percent': self.risk_manager.calculate_position_size(score['confidence']),
                'analysis': analysis
            }
            logger.info(f"✅ BUY signal: {symbol} (confidence: {score['confidence']}%)")
            return signal
            
        elif score['action'] == 'SELL' and score['confidence'] >= TRADING_CONFIG['min_confidence']:
            signal = {
                'action': 'SELL',
                'symbol': symbol,
                'confidence': score['confidence'],
                'reasons': score['reasons'],
                'analysis': analysis
            }
            logger.info(f"✅ SELL signal: {symbol} (confidence: {score['confidence']}%)")
            return signal
        
        return None
    
    def _calculate_composite_score(self, analysis: Dict) -> Dict:
        """Calculate composite trading score from all indicators"""
        
        scores = []
        reasons = []
        
        # Technical Signals (40%)
        signals = analysis['technical_signals']
        if signals['overall'] == 'STRONG_BUY':
            scores.append(90)
            reasons.append("Strong technical buy")
        elif signals['overall'] == 'BUY':
            scores.append(70)
            reasons.append("Technical buy")
        elif signals['overall'] == 'SELL':
            scores.append(30)
            reasons.append("Technical sell")
        elif signals['overall'] == 'STRONG_SELL':
            scores.append(10)
            reasons.append("Strong technical sell")
        else:
            scores.append(50)
        
        # ML Prediction (25%)
        ml = analysis['ml_prediction']
        if ml['prediction'] == 'UP' and ml['confidence'] > 60:
            scores.append(ml['confidence'])
            reasons.append(f"ML predicts UP ({ml['confidence']}%)")
        elif ml['prediction'] == 'DOWN' and ml['confidence'] > 60:
            scores.append(100 - ml['confidence'])
            reasons.append(f"ML predicts DOWN ({ml['confidence']}%)")
        
        # Sentiment (15%)
        sentiment = analysis['sentiment']
        if sentiment['score'] > 0.3:
            scores.append(70 + sentiment['score'] * 30)
            reasons.append(f"Bullish sentiment ({sentiment['score']:.2f})")
        elif sentiment['score'] < -0.3:
            scores.append(30 + sentiment['score'] * 30)
            reasons.append(f"Bearish sentiment ({sentiment['score']:.2f})")
        
        # Correlation (10%)
        corr = analysis['btc_correlation']
        if corr['aligned']:
            scores.append(80)
            reasons.append("Aligned with BTC direction")
        
        # Time filter (10%)
        if analysis['time_ok']:
            scores.append(80)
        else:
            scores.append(0)
            reasons.append("Outside trading hours")
        
        # Calculate final
        avg_score = sum(scores) / len(scores) if scores else 50
        
        # Determine action
        if avg_score >= 65:
            action = 'BUY'
        elif avg_score <= 35:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        return {
            'action': action,
            'confidence': round(avg_score, 1),
            'scores': scores,
            'reasons': reasons
        }
    
    async def execute_signal(self, signal: Dict) -> bool:
        """Execute a trade signal"""
        logger.info(f"🚀 Executing {signal['action']} for {signal['symbol']}")
        
        # Set TP/SL with volatility adapter
        tp = signal.get('tp_percent', 2.5)
        sl = signal.get('sl_percent', 2.5)
        
        # Execute trade
        result = await self.position_manager.open_position(
            symbol=signal['symbol'],
            side=signal['action'],
            size=signal.get('size_percent', 10),
            tp_percent=tp,
            sl_percent=sl
        )
        
        if result['success']:
            logger.info(f"✅ Position opened: {signal['symbol']}")
            return True
        else:
            logger.error(f"❌ Failed to open position: {result['error']}")
            return False
    
    async def run_autonomous(self, symbols: List[str], interval: int = 60):
        """Run the trading system autonomously"""
        self.is_running = True
        logger.info("🤖 Starting autonomous trading...")
        
        while self.is_running:
            try:
                for symbol in symbols:
                    # Check existing positions
                    positions = await self.position_manager.get_positions(symbol)
                    
                    if not positions:
                        # No position - look for entry
                        signal = await self.generate_signal(symbol)
                        if signal:
                            await self.execute_signal(signal)
                    else:
                        # Manage existing position
                        await self._manage_position(positions[0])
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in autonomous loop: {e}")
                await asyncio.sleep(60)
    
    async def _manage_position(self, position: Dict):
        """Manage existing position"""
        # Check if should take profit or stop loss
        pnl_pct = position.get('pnl_percent', 0)
        
        # Trailing stop logic
        if pnl_pct > 1:
            await self.position_manager.update_trailing_stop(position['symbol'], 1)
        
        # Take profit at target
        if pnl_pct >= 2.5:
            await self.position_manager.close_position(position['symbol'])
    
    async def _get_price_data(self, symbol: str) -> Dict:
        """Fetch price data from exchange"""
        # This would use ccxt or bybit API
        pass
    
    def stop(self):
        """Stop the trading system"""
        self.is_running = False
        logger.info("🛑 Trading system stopped")


# Singleton instance
_trading_system = None

def get_trading_system(api_key: str, api_secret: str) -> AITradingSystem:
    global _trading_system
    if _trading_system is None:
        _trading_system = AITradingSystem(api_key, api_secret)
    return _trading_system
