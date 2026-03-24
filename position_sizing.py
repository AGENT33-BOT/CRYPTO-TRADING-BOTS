#!/usr/bin/env python3
"""
Position Sizing Calculator
Implements Kelly Criterion and risk-based position sizing
"""

import os
import sys
import json
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Historical performance metrics (update these based on your actual trading data)
DEFAULT_METRICS = {
    'win_rate': 0.58,           # 58% win rate (typical for scalping)
    'avg_win': 2.5,             # 2.5% average win
    'avg_loss': 1.5,            # 1.5% average loss
    'profit_factor': 1.67,      # Gross profit / Gross loss
    'max_consecutive_losses': 3,
    'total_trades': 100,
}

# Risk settings
MAX_RISK_PER_TRADE = 0.02      # 2% max risk per trade (conservative)
MAX_POSITION_SIZE = 0.20       # 20% max of account in one position
KELLY_FRACTION = 0.5           # Half-Kelly for safety


@dataclass
class SizingResult:
    method: str
    position_size_usd: float
    position_size_percent: float
    risk_amount: float
    leverage: float
    kelly_percent: float
    recommendation: str


def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Calculate Kelly Criterion percentage.
    
    f* = (p(b+1) - 1) / b
    Where:
    - p = win probability
    - b = average win / average loss (odds)
    
    Returns optimal fraction of bankroll to risk (0.0 to 1.0)
    """
    if avg_loss == 0:
        return 0
    
    b = avg_win / avg_loss  # Odds
    kelly = (win_rate * (b + 1) - 1) / b
    
    return max(0, min(kelly, 1.0))  # Clamp between 0 and 1


def calculate_fixed_fraction(account_balance: float, risk_percent: float) -> float:
    """Calculate position size based on fixed risk percentage"""
    return account_balance * risk_percent


def calculate_fixed_ratio(account_balance: float, delta: float, units: int) -> float:
    """
    Calculate position size using Fixed Ratio method.
    
    Position size increases only after accumulating 'delta' profits
    per unit of position size.
    """
    # Simplified - increase size every $100 profit per unit
    size_increase = int(account_balance / delta)
    return min(size_increase, units) * delta


def get_optimal_position_size(
    account_balance: float,
    entry_price: float,
    stop_loss_price: float,
    symbol: str = "",
    method: str = "kelly_half",
    metrics: Optional[Dict] = None
) -> SizingResult:
    """
    Calculate optimal position size using various methods.
    
    Methods:
    - 'kelly_full': Full Kelly Criterion (aggressive)
    - 'kelly_half': Half Kelly (recommended)
    - 'kelly_quarter': Quarter Kelly (conservative)
    - 'fixed_2pct': Fixed 2% risk per trade
    - 'fixed_1pct': Fixed 1% risk per trade
    """
    if metrics is None:
        metrics = DEFAULT_METRICS
    
    # Calculate risk distance
    risk_distance = abs(entry_price - stop_loss_price) / entry_price
    
    if risk_distance == 0:
        return SizingResult(
            method=method,
            position_size_usd=0,
            position_size_percent=0,
            risk_amount=0,
            leverage=0,
            kelly_percent=0,
            recommendation="Error: Stop loss must be different from entry price"
        )
    
    # Calculate Kelly Criterion
    kelly_full = calculate_kelly_criterion(
        metrics['win_rate'],
        metrics['avg_win'],
        metrics['avg_loss']
    )
    
    # Determine risk fraction based on method
    if method == 'kelly_full':
        risk_fraction = kelly_full
    elif method == 'kelly_half':
        risk_fraction = kelly_full * 0.5
    elif method == 'kelly_quarter':
        risk_fraction = kelly_full * 0.25
    elif method == 'fixed_2pct':
        risk_fraction = 0.02
    elif method == 'fixed_1pct':
        risk_fraction = 0.01
    else:
        risk_fraction = kelly_full * 0.5  # Default to half-kelly
    
    # Apply maximum risk cap
    risk_fraction = min(risk_fraction, MAX_RISK_PER_TRADE)
    
    # Calculate risk amount in USD
    risk_amount = account_balance * risk_fraction
    
    # Calculate position size based on risk distance
    # Position Size = Risk Amount / Risk Distance
    position_size = risk_amount / risk_distance
    
    # Apply maximum position size cap
    max_position = account_balance * MAX_POSITION_SIZE
    position_size = min(position_size, max_position)
    
    # Calculate required leverage
    if position_size > 0:
        leverage = position_size / account_balance
        leverage = min(leverage, 20.0)  # Max 20x leverage
    else:
        leverage = 0
    
    # Generate recommendation
    recommendation = generate_recommendation(
        method, kelly_full, risk_fraction, position_size, 
        account_balance, leverage
    )
    
    return SizingResult(
        method=method,
        position_size_usd=round(position_size, 2),
        position_size_percent=round((position_size / account_balance) * 100, 2),
        risk_amount=round(risk_amount, 2),
        leverage=round(leverage, 1),
        kelly_percent=round(kelly_full * 100, 2),
        recommendation=recommendation
    )


def generate_recommendation(method: str, kelly_full: float, risk_fraction: float,
                           position_size: float, account_balance: float, leverage: float) -> str:
    """Generate human-readable recommendation"""
    
    recommendations = []
    
    # Kelly-based recommendations
    if kelly_full <= 0:
        recommendations.append("⚠️ Kelly Criterion suggests NO TRADE (negative expectancy)")
    elif kelly_full < 0.1:
        recommendations.append("🟡 Low Kelly score - consider better setups only")
    elif kelly_full > 0.5:
        recommendations.append("🟢 High Kelly score - strong edge detected")
    
    # Risk warnings
    if leverage > 10:
        recommendations.append("⚠️ High leverage (>10x) - use tight stops!")
    elif leverage > 5:
        recommendations.append("🟡 Moderate leverage - monitor closely")
    else:
        recommendations.append("🟢 Conservative leverage - good risk management")
    
    # Position size warnings
    position_pct = (position_size / account_balance) * 100
    if position_pct > 15:
        recommendations.append(f"⚠️ Large position ({position_pct:.1f}% of account)")
    
    # Method-specific notes
    if 'kelly' in method:
        recommendations.append(f"📊 Using {method} ({risk_fraction*100:.1f}% of Kelly)")
    
    return " | ".join(recommendations) if recommendations else "✅ Standard sizing applied"


def calculate_all_methods(account_balance: float, entry_price: float, 
                         stop_loss_price: float, symbol: str = "") -> Dict:
    """Calculate position sizes for all methods"""
    
    methods = ['kelly_full', 'kelly_half', 'kelly_quarter', 'fixed_2pct', 'fixed_1pct']
    results = {}
    
    for method in methods:
        results[method] = get_optimal_position_size(
            account_balance, entry_price, stop_loss_price, symbol, method
        )
    
    return results


def load_account_balance() -> float:
    """Load current account balance from Bybit"""
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
        
        balance = exchange.fetch_balance({'type': 'unified'})
        usdt_total = balance.get('USDT', {}).get('total', 0)
        return float(usdt_total)
    except Exception as e:
        logger.error(f"Failed to load balance: {e}")
        return 0.0


def print_sizing_report(result: SizingResult, account_balance: float):
    """Print formatted sizing report"""
    print(f"\n{'='*60}")
    print(f"POSITION SIZING REPORT - {result.method.upper()}")
    print(f"{'='*60}")
    print(f"Account Balance:     ${account_balance:,.2f}")
    print(f"Kelly Criterion:     {result.kelly_percent:.1f}% (optimal)")
    print(f"Risk Amount:         ${result.risk_amount:,.2f}")
    print(f"Position Size:       ${result.position_size_usd:,.2f} ({result.position_size_percent}% of account)")
    print(f"Recommended Leverage: {result.leverage}x")
    print(f"\nRecommendation:     {result.recommendation}")
    print(f"{'='*60}")


def main():
    """Main calculator interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Position Sizing Calculator')
    parser.add_argument('--balance', type=float, help='Account balance (auto-fetch if not provided)')
    parser.add_argument('--entry', type=float, required=True, help='Entry price')
    parser.add_argument('--stop', type=float, required=True, help='Stop loss price')
    parser.add_argument('--symbol', type=str, default='', help='Trading symbol')
    parser.add_argument('--method', type=str, default='kelly_half', 
                       choices=['kelly_full', 'kelly_half', 'kelly_quarter', 'fixed_2pct', 'fixed_1pct'],
                       help='Sizing method')
    parser.add_argument('--compare', action='store_true', help='Show all methods')
    
    args = parser.parse_args()
    
    # Get account balance
    if args.balance:
        balance = args.balance
    else:
        balance = load_account_balance()
        if balance == 0:
            print("❌ Could not fetch balance. Use --balance flag.")
            return
    
    print(f"\n💰 Account Balance: ${balance:,.2f}")
    print(f"📈 Entry Price: ${args.entry}")
    print(f"🛑 Stop Loss: ${args.stop}")
    print(f"📊 Risk Distance: {abs(args.entry - args.stop) / args.entry * 100:.2f}%")
    
    if args.compare:
        print("\n" + "="*80)
        print("COMPARISON OF ALL METHODS")
        print("="*80)
        
        results = calculate_all_methods(balance, args.entry, args.stop, args.symbol)
        
        print(f"\n{'Method':<15} {'Position $':<12} {'Pos %':<8} {'Risk $':<10} {'Lev':<6} {'Kelly %'}")
        print("-"*80)
        
        for method, result in results.items():
            print(f"{method:<15} ${result.position_size_usd:<11,.0f} "
                  f"{result.position_size_percent:<7}% ${result.risk_amount:<9,.2f} "
                  f"{result.leverage:<5}x {result.kelly_percent}%")
        
        print("\n" + "="*80)
        print("RECOMMENDED: kelly_half (Half-Kelly for safety)")
        print("="*80)
    else:
        result = get_optimal_position_size(
            balance, args.entry, args.stop, args.symbol, args.method
        )
        print_sizing_report(result, balance)
    
    # Save to history
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'balance': balance,
        'entry': args.entry,
        'stop': args.stop,
        'symbol': args.symbol,
        'method': args.method,
        'result': result.__dict__ if not args.compare else {k: v.__dict__ for k, v in results.items()}
    }
    
    try:
        history_file = 'sizing_history.json'
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
        
        history.append(history_entry)
        
        with open(history_file, 'w') as f:
            json.dump(history[-100:], f, indent=2)  # Keep last 100 entries
        
        print(f"\n💾 History saved to {history_file}")
    except Exception as e:
        logger.warning(f"Could not save history: {e}")


if __name__ == '__main__':
    main()
