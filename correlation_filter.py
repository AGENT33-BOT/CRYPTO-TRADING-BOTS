#!/usr/bin/env python3
"""
Trading Correlation Filter
Prevents over-concentration in correlated assets
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crypto correlation matrix (based on historical price movements)
# 1.0 = perfect correlation, 0.0 = no correlation, -1.0 = inverse
CORRELATION_MATRIX = {
    'BTC': {'ETH': 0.85, 'SOL': 0.78, 'XRP': 0.65, 'LINK': 0.72, 'AVAX': 0.80, 'NEAR': 0.75, 'ARB': 0.82, 'DOGE': 0.70},
    'ETH': {'BTC': 0.85, 'SOL': 0.82, 'XRP': 0.68, 'LINK': 0.88, 'AVAX': 0.85, 'NEAR': 0.80, 'ARB': 0.90, 'DOGE': 0.72},
    'SOL': {'BTC': 0.78, 'ETH': 0.82, 'XRP': 0.60, 'LINK': 0.75, 'AVAX': 0.80, 'NEAR': 0.78, 'ARB': 0.77, 'DOGE': 0.65},
    'XRP': {'BTC': 0.65, 'ETH': 0.68, 'SOL': 0.60, 'LINK': 0.62, 'AVAX': 0.65, 'NEAR': 0.63, 'ARB': 0.64, 'DOGE': 0.58},
    'LINK': {'BTC': 0.72, 'ETH': 0.88, 'SOL': 0.75, 'XRP': 0.62, 'AVAX': 0.78, 'NEAR': 0.74, 'ARB': 0.85, 'DOGE': 0.68},
    'AVAX': {'BTC': 0.80, 'ETH': 0.85, 'SOL': 0.80, 'XRP': 0.65, 'LINK': 0.78, 'NEAR': 0.82, 'ARB': 0.79, 'DOGE': 0.70},
    'NEAR': {'BTC': 0.75, 'ETH': 0.80, 'SOL': 0.78, 'XRP': 0.63, 'LINK': 0.74, 'AVAX': 0.82, 'ARB': 0.76, 'DOGE': 0.66},
    'ARB': {'BTC': 0.82, 'ETH': 0.90, 'SOL': 0.77, 'XRP': 0.64, 'LINK': 0.85, 'AVAX': 0.79, 'NEAR': 0.76, 'DOGE': 0.69},
    'DOGE': {'BTC': 0.70, 'ETH': 0.72, 'SOL': 0.65, 'XRP': 0.58, 'LINK': 0.68, 'AVAX': 0.70, 'NEAR': 0.66, 'ARB': 0.69},
}

# Risk limits
MAX_CORRELATED_POSITIONS = 2  # Max positions with correlation > threshold
CORRELATION_THRESHOLD = 0.70  # Consider positions correlated above this
MAX_POSITIONS_SAME_DIRECTION = 3  # Max longs OR max shorts


@dataclass
class Position:
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    size: float
    entry_price: float


def extract_base_symbol(symbol: str) -> str:
    """Extract base symbol from trading pair (e.g., 'BTC/USDT:USDT' -> 'BTC')"""
    # Handle various formats: BTC/USDT, BTC/USDT:USDT, BTCUSDT
    symbol = symbol.upper()
    for base in CORRELATION_MATRIX.keys():
        if symbol.startswith(base):
            return base
    return symbol.split('/')[0] if '/' in symbol else symbol[:3]


def get_correlation(symbol1: str, symbol2: str) -> float:
    """Get correlation between two symbols (0.0 to 1.0)"""
    base1 = extract_base_symbol(symbol1)
    base2 = extract_base_symbol(symbol2)
    
    if base1 == base2:
        return 1.0
    
    # Look up in correlation matrix
    if base1 in CORRELATION_MATRIX and base2 in CORRELATION_MATRIX[base1]:
        return CORRELATION_MATRIX[base1][base2]
    
    # Default moderate correlation for unknown pairs
    return 0.50


def check_correlation_risk(new_symbol: str, new_side: str, existing_positions: List[Position]) -> Tuple[bool, str]:
    """
    Check if adding a new position violates correlation rules.
    
    Returns:
        (allowed: bool, reason: str)
    """
    new_base = extract_base_symbol(new_symbol)
    
    # Count existing positions on same side
    same_direction_positions = [p for p in existing_positions if p.side.upper() == new_side.upper()]
    
    if len(same_direction_positions) >= MAX_POSITIONS_SAME_DIRECTION:
        return False, f"Max {MAX_POSITIONS_SAME_DIRECTION} {new_side.upper()} positions allowed"
    
    # Count highly correlated positions
    correlated_count = 0
    correlated_symbols = []
    
    for pos in same_direction_positions:
        correlation = get_correlation(new_symbol, pos.symbol)
        if correlation >= CORRELATION_THRESHOLD:
            correlated_count += 1
            correlated_symbols.append(f"{pos.symbol} ({correlation:.0%})")
    
    if correlated_count >= MAX_CORRELATED_POSITIONS:
        return False, f"Would create {correlated_count+1} correlated {new_side.upper()} positions. Existing: {', '.join(correlated_symbols)}"
    
    # Check for opposite direction correlation (hedging concern)
    opposite_direction = 'SHORT' if new_side.upper() == 'LONG' else 'LONG'
    opposite_positions = [p for p in existing_positions if p.side.upper() == opposite_direction]
    
    for pos in opposite_positions:
        correlation = get_correlation(new_symbol, pos.symbol)
        if correlation >= CORRELATION_THRESHOLD:
            return False, f"Hedging conflict: {new_symbol} highly correlated ({correlation:.0%}) with {pos.side} position {pos.symbol}"
    
    return True, "Position allowed"


def calculate_portfolio_correlation(positions: List[Position]) -> Dict:
    """Calculate portfolio-wide correlation metrics"""
    if len(positions) < 2:
        return {"status": "ok", "message": "Single position - no correlation risk"}
    
    # Group by direction
    longs = [p for p in positions if p.side.upper() == 'LONG']
    shorts = [p for p in positions if p.side.upper() == 'SHORT']
    
    # Check long correlation
    long_correlations = []
    for i, p1 in enumerate(longs):
        for p2 in longs[i+1:]:
            corr = get_correlation(p1.symbol, p2.symbol)
            long_correlations.append({
                'pair': f"{p1.symbol}-{p2.symbol}",
                'correlation': corr,
                'risk': 'HIGH' if corr > 0.80 else 'MEDIUM' if corr > 0.60 else 'LOW'
            })
    
    # Check short correlation
    short_correlations = []
    for i, p1 in enumerate(shorts):
        for p2 in shorts[i+1:]:
            corr = get_correlation(p1.symbol, p2.symbol)
            short_correlations.append({
                'pair': f"{p1.symbol}-{p2.symbol}",
                'correlation': corr,
                'risk': 'HIGH' if corr > 0.80 else 'MEDIUM' if corr > 0.60 else 'LOW'
            })
    
    # Check hedging (opposite direction correlations)
    hedging_issues = []
    for long_pos in longs:
        for short_pos in shorts:
            corr = get_correlation(long_pos.symbol, short_pos.symbol)
            if corr > 0.80:
                hedging_issues.append({
                    'long': long_pos.symbol,
                    'short': short_pos.symbol,
                    'correlation': corr,
                    'issue': 'Positions will largely cancel each other out'
                })
    
    high_risk_count = len([c for c in long_correlations + short_correlations if c['risk'] == 'HIGH'])
    
    status = "warning" if high_risk_count > 0 or len(hedging_issues) > 0 else "ok"
    
    return {
        "status": status,
        "long_correlations": long_correlations,
        "short_correlations": short_correlations,
        "hedging_issues": hedging_issues,
        "summary": {
            "total_positions": len(positions),
            "longs": len(longs),
            "shorts": len(shorts),
            "high_correlation_pairs": high_risk_count,
            "hedging_conflicts": len(hedging_issues)
        }
    }


def load_positions_from_bybit():
    """Load current positions from Bybit"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import ccxt
        api_key = os.getenv('BYBIT_API_KEY', '').strip() or 'bsK06QDhsagOWwFsXQ'
        api_secret = os.getenv('BYBIT_API_SECRET', '').strip() or 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'
        
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        
        raw_positions = exchange.fetch_positions()
        positions = []
        
        for pos in raw_positions:
            size = float(pos.get('contracts', 0))
            if size != 0:
                side = 'LONG' if pos.get('side') == 'long' else 'SHORT'
                positions.append(Position(
                    symbol=pos.get('symbol', 'Unknown'),
                    side=side,
                    size=abs(size),
                    entry_price=float(pos.get('entryPrice', 0))
                ))
        
        return positions
    except Exception as e:
        logger.error(f"Failed to load positions: {e}")
        return []


def main():
    """Run correlation analysis on current portfolio"""
    logger.info("=" * 60)
    logger.info("Trading Correlation Filter - Portfolio Analysis")
    logger.info("=" * 60)
    
    positions = load_positions_from_bybit()
    
    if not positions:
        logger.info("No open positions found")
        return
    
    logger.info(f"Analyzing {len(positions)} positions:")
    for pos in positions:
        emoji = "🟢" if pos.side == 'LONG' else "🔴"
        logger.info(f"  {emoji} {pos.side:5} {pos.symbol:15} Size: {pos.size}")
    
    # Run correlation analysis
    analysis = calculate_portfolio_correlation(positions)
    
    logger.info("\nCorrelation Analysis Results:")
    logger.info(f"  Status: {analysis['status'].upper()}")
    
    if analysis['long_correlations']:
        logger.info("\n  LONG correlations:")
        for corr in analysis['long_correlations']:
            emoji = "🔴" if corr['risk'] == 'HIGH' else "🟡" if corr['risk'] == 'MEDIUM' else "🟢"
            logger.info(f"    {emoji} {corr['pair']}: {corr['correlation']:.1%} ({corr['risk']} risk)")
    
    if analysis['short_correlations']:
        logger.info("\n  SHORT correlations:")
        for corr in analysis['short_correlations']:
            emoji = "🔴" if corr['risk'] == 'HIGH' else "🟡" if corr['risk'] == 'MEDIUM' else "🟢"
            logger.info(f"    {emoji} {corr['pair']}: {corr['correlation']:.1%} ({corr['risk']} risk)")
    
    if analysis['hedging_issues']:
        logger.info("\n  ⚠️  HEDGING CONFLICTS:")
        for issue in analysis['hedging_issues']:
            logger.info(f"    {issue['long']} LONG vs {issue['short']} SHORT: {issue['correlation']:.1%} correlation")
            logger.info(f"      -> {issue['issue']}")
    
    # Summary
    summary = analysis['summary']
    logger.info(f"\nPortfolio Summary:")
    logger.info(f"  Total positions: {summary['total_positions']}")
    logger.info(f"  Longs: {summary['longs']} | Shorts: {summary['shorts']}")
    logger.info(f"  High correlation pairs: {summary['high_correlation_pairs']}")
    logger.info(f"  Hedging conflicts: {summary['hedging_conflicts']}")
    
    # Recommendations
    if analysis['status'] == 'warning':
        logger.warning("\n⚠️  RECOMMENDATIONS:")
        if summary['high_correlation_pairs'] > 0:
            logger.warning("  - Consider reducing correlated positions")
            logger.warning("  - Diversify into uncorrelated assets (XRP has lowest correlation)")
        if summary['hedging_conflicts'] > 0:
            logger.warning("  - Close one side of hedged correlated pairs")
            logger.warning("  - Pick a direction and commit (don't hedge yourself)")
    else:
        logger.info("\n✅ Portfolio correlation risk is acceptable")
    
    logger.info("=" * 60)
    
    # Save report
    report_file = 'correlation_report.json'
    with open(report_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    logger.info(f"Report saved to {report_file}")


if __name__ == '__main__':
    main()
