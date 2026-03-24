"""
Polymarket Strategies - Different trading approaches for prediction markets
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta

class PolymarketStrategies:
    """Various strategies for Polymarket trading"""
    
    @staticmethod
    def extreme_sentiment_strategy(market: Dict) -> Dict:
        """
        Trade against extreme crowd sentiment
        Theory: Crowds are wrong at extremes (>90% or <10%)
        """
        question = market.get('question', '')
        tokens = market.get('tokens', [])
        
        if len(tokens) < 2:
            return {'signal': 'NONE', 'reason': 'Invalid market'}
        
        yes_price = float(tokens[0].get('price', 0))
        
        # Extreme bullish (crowd thinks YES)
        if yes_price > 0.90:
            return {
                'signal': 'BUY_NO',
                'confidence': min((yes_price - 0.90) * 500, 95),
                'reason': f'Extreme bullishness ({yes_price*100:.1f}%) - contrarian NO',
                'expected_return': (1 - yes_price) * 0.8  # 80% of potential
            }
        
        # Extreme bearish (crowd thinks NO)
        elif yes_price < 0.10:
            return {
                'signal': 'BUY_YES',
                'confidence': min((0.10 - yes_price) * 500, 95),
                'reason': f'Extreme bearishness ({yes_price*100:.1f}%) - contrarian YES',
                'expected_return': yes_price * 8  # 8x potential
            }
        
        return {'signal': 'NONE', 'reason': 'Not extreme enough'}
    
    @staticmethod
    def time_decay_strategy(market: Dict) -> Dict:
        """
        Trade on time decay as resolution approaches
        Earlier = more uncertainty (higher prices)
        Later = more certainty (prices converge to 0 or 1)
        """
        end_date = market.get('resolutionDate')
        if not end_date:
            return {'signal': 'NONE'}
        
        # Calculate days to resolution
        try:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            now = datetime.now().astimezone()
            days_left = (end - now).days
        except:
            return {'signal': 'NONE'}
        
        tokens = market.get('tokens', [])
        yes_price = float(tokens[0].get('price', 0)) if tokens else 0.5
        
        # If very close to resolution and price is middle range
        # Prices should converge - scalping opportunity
        if days_left < 3 and 0.40 < yes_price < 0.60:
            return {
                'signal': 'SCALP',
                'direction': 'YES' if yes_price < 0.50 else 'NO',
                'reason': f'Time decay scalp - {days_left} days left, price {yes_price:.2f}',
                'hold_time': 'hours'
            }
        
        return {'signal': 'NONE'}
    
    @staticmethod
    def news_event_strategy(market: Dict, event_type: str = 'crypto') -> Dict:
        """
        Trade on specific news events
        Examples: ETF approvals, Fed decisions, exchange listings
        """
        question = market.get('question', '').lower()
        
        # Crypto events
        if event_type == 'crypto':
            if 'etf' in question or 'approval' in question:
                return {
                    'signal': 'EVENT',
                    'type': 'ETF_APPROVAL',
                    'strategy': 'Buy YES before announcement, sell on news',
                    'risk': 'HIGH - binary outcome'
                }
            
            elif 'price' in question and ('end of' in question or 'by' in question):
                return {
                    'signal': 'PRICE_TARGET',
                    'type': 'PRICE_PREDICTION',
                    'strategy': 'Technical analysis + momentum',
                    'risk': 'MEDIUM'
                }
        
        # Macro events
        elif event_type == 'macro':
            if 'fed' in question or 'interest rate' in question:
                return {
                    'signal': 'EVENT',
                    'type': 'FED_DECISION',
                    'strategy': 'Follow CME FedWatch probabilities',
                    'risk': 'MEDIUM'
                }
        
        return {'signal': 'NONE'}
    
    @staticmethod
    def arbitrage_strategy(markets: List[Dict]) -> List[Dict]:
        """
        Find arbitrage between related markets
        Example: BTC > $60k AND BTC > $70k should have consistent pricing
        """
        arbitrages = []
        
        # Group by asset
        btc_markets = [m for m in markets if 'bitcoin' in m.get('question', '').lower() or 'btc' in m.get('question', '').lower()]
        
        # Check for inconsistent pricing
        for i, market1 in enumerate(btc_markets):
            for market2 in btc_markets[i+1:]:
                # If market1 implies market2 should have higher probability but doesn't
                prob1 = float(market1.get('tokens', [{}])[0].get('price', 0))
                prob2 = float(market2.get('tokens', [{}])[0].get('price', 0))
                
                # Simple check: if market2 is "harder" than market1 but priced lower
                # This is a simplified check - real arbitrage needs careful analysis
                if prob2 > prob1 + 0.05:  # 5% pricing inconsistency
                    arbitrages.append({
                        'market1': market1.get('question'),
                        'market2': market2.get('question'),
                        'prob1': prob1,
                        'prob2': prob2,
                        'edge': prob2 - prob1,
                        'action': f'Buy market1 YES, Sell market2 YES'
                    })
        
        return arbitrages
    
    @staticmethod
    def kelly_criterion_sizing(probability: float, odds: float, bankroll: float) -> float:
        """
        Calculate optimal bet size using Kelly Criterion
        f* = (bp - q) / b
        where:
        b = odds - 1 (net odds received)
        p = probability of winning
        q = probability of losing (1-p)
        """
        if odds <= 1 or probability <= 0 or probability >= 1:
            return 0
        
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Use half Kelly for safety
        half_kelly = kelly / 2
        
        # Maximum 5% of bankroll per bet
        max_bet = bankroll * 0.05
        
        # Return the smaller of half-Kelly and max bet
        bet_size = min(half_kelly * bankroll, max_bet)
        
        return max(bet_size, 0)  # Don't bet negative
    
    @staticmethod
    def portfolio_allocation(opportunities: List[Dict], bankroll: float) -> Dict:
        """
        Allocate capital across multiple opportunities
        Diversification strategy
        """
        allocations = {}
        remaining_bankroll = bankroll
        
        # Sort by expected return
        sorted_opps = sorted(opportunities, key=lambda x: x.get('expected_return', 0), reverse=True)
        
        for opp in sorted_opps[:5]:  # Top 5 opportunities
            market_id = opp.get('market_id')
            expected_return = opp.get('expected_return', 0)
            
            # Allocate based on expected return and confidence
            confidence = opp.get('confidence', 50) / 100
            
            # Max 2% per position for diversification
            max_allocation = bankroll * 0.02
            
            # Scale by confidence and expected return
            allocation = min(max_allocation * confidence * (1 + expected_return), remaining_bankroll * 0.05)
            
            allocations[market_id] = {
                'amount': allocation,
                'side': opp.get('signal'),
                'confidence': confidence,
                'expected_return': expected_return
            }
            
            remaining_bankroll -= allocation
        
        return allocations
