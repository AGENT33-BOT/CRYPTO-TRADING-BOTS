"""
Agent33 Trading Risk Management Configuration
Consolidated position sizing rules for all trading bots
Based on analysis from Feb 23, 2026
"""

# =======================
# GLOBAL RISK PARAMETERS
# =======================

RISK_CONFIG = {
    # Account-level limits
    'max_account_utilization': 0.75,      # Max 75% of account in positions
    'min_free_balance_usd': 15,            # Minimum $15 free balance
    'max_daily_drawdown_pct': 0.10,        # Stop if down 10% in a day
    
    # Position-level limits
    'max_position_pct': 0.15,              # Max 15% of account per position
    'max_symbol_pct': 0.25,                # Max 25% per symbol
    'min_position_usd': 5,                 # Minimum $5 per trade
    
    # Circuit breakers
    'circuit_breaker_free_balance': -20,   # Pause if free < -$20
    'circuit_breaker_daily_loss': -30,     # Pause if daily loss > $30
    'circuit_breaker_consecutive_losses': 3,  # Pause after 3 losing trades
}

# =======================
# SYMBOL CLASSIFICATION
# =======================

SYMBOLS = {
    # WINNERS - High performance symbols (KEEP)
    'winners': [
        'NEAR/USDT:USDT',   # High volatility, high reward - REDUCE SIZE 30%
        'ETH/USDT:USDT',    # Consistent performer - normal sizing
        'DOGE/USDT:USDT',   # Low volatility, steady - normal sizing
        'BTC/USDT:USDT',    # Stable, good for grid
        'SOL/USDT:USDT',    # Moderate volatility
        'XRP/USDT:USDT',    # Moderate volatility
    ],
    
    # AVOID - Poor performance symbols (DO NOT TRADE)
    'avoid': [
        'LINK/USDT:USDT',   # 0% win rate in analysis
        'ADA/USDT:USDT',    # Consistent small losses
        'DOT/USDT:USDT',    # Not in data - avoid
        'AVAX/USDT:USDT',   # Not in data - avoid
        'LTC/USDT:USDT',    # Not in data - avoid
        'BCH/USDT:USDT',    # Not in data - avoid
    ],
    
    # HIGH VOLATILITY - Reduce position size by 30%
    'high_volatility': [
        'NEAR/USDT:USDT',
    ],
}

# =======================
# BOT-SPECIFIC CONFIGS
# =======================

BOT_CONFIGS = {
    'scalping': {
        'enabled': True,
        'symbols': ['ETH/USDT:USDT', 'NEAR/USDT:USDT'],
        'timeframe': '1m',
        'leverage': 5,
        'position_size': 25,           # Will be validated against max_position_pct
        'max_positions': 3,
        'min_confidence': 80,
        'profit_target': 0.008,        # 0.8%
        'stop_loss': 0.005,            # 0.5%
        'max_hold_minutes': 15,
    },
    
    'mean_reversion': {
        'enabled': True,
        'symbols': ['ETH/USDT:USDT', 'NEAR/USDT:USDT', 'DOGE/USDT:USDT'],
        'timeframe': '5m',
        'leverage': 3,
        'position_size': 40,
        'max_positions': 4,
        'min_confidence': 75,
        'profit_target': 0.025,        # 2.5%
        'stop_loss': 0.015,            # 1.5%
    },
    
    'momentum': {
        'enabled': True,
        'symbols': ['ETH/USDT:USDT', 'NEAR/USDT:USDT'],
        'timeframe': '15m',
        'leverage': 3,
        'position_size': 35,
        'max_positions': 3,
        'min_confidence': 80,
        'profit_target': 0.035,        # 3.5%
        'stop_loss': 0.020,            # 2.0%
    },
    
    'grid_trader': {
        'enabled': True,
        'symbol': 'DOGE/USDT:USDT',
        'grid_levels': 10,
        'grid_lower': 0.0910,
        'grid_upper': 0.0980,
        'total_investment': 30,        # Will be capped at 50% of account
        'leverage': 2,
        'check_interval': 30,
    },
    
    'funding_arbitrage': {
        'enabled': True,
        'check_interval': 300,         # 5 minutes
        'min_funding_rate': 0.0001,    # 0.01%
        'max_position_usd': 50,
    },
}

# =======================
# HELPER FUNCTIONS
# =======================

def validate_symbol(symbol):
    """Check if symbol is allowed"""
    if symbol in SYMBOLS['avoid']:
        return False, f"{symbol} is on AVOID list (poor performance)"
    if symbol not in SYMBOLS['winners']:
        return False, f"{symbol} not in winners list"
    return True, "OK"

def get_position_size_adjustment(symbol):
    """Get position size adjustment for symbol"""
    if symbol in SYMBOLS['high_volatility']:
        return 0.70  # Reduce to 70% (30% reduction)
    return 1.0  # No adjustment

def calculate_max_position_size(account_balance, symbol=None):
    """Calculate maximum position size based on risk rules"""
    base_size = account_balance * RISK_CONFIG['max_position_pct']
    
    # Apply volatility adjustment if symbol provided
    if symbol:
        adjustment = get_position_size_adjustment(symbol)
        base_size = base_size * adjustment
    
    # Ensure minimum
    if base_size < RISK_CONFIG['min_position_usd']:
        return 0  # Can't trade with this balance
    
    return round(base_size, 2)

def check_circuit_breakers(free_balance, daily_pnl, consecutive_losses):
    """Check if circuit breakers should trigger"""
    if free_balance < RISK_CONFIG['circuit_breaker_free_balance']:
        return True, f"Free balance ${free_balance:.2f} below circuit breaker"
    
    if daily_pnl < RISK_CONFIG['circuit_breaker_daily_loss']:
        return True, f"Daily PnL ${daily_pnl:.2f} below circuit breaker"
    
    if consecutive_losses >= RISK_CONFIG['circuit_breaker_consecutive_losses']:
        return True, f"{consecutive_losses} consecutive losses"
    
    return False, "OK"

# =======================
# USAGE EXAMPLE
# =======================

if __name__ == '__main__':
    # Example usage
    print("Agent33 Risk Configuration")
    print("=" * 50)
    
    print("\nMax Position Size Examples:")
    for balance in [100, 300, 500, 1000]:
        size = calculate_max_position_size(balance)
        near_size = calculate_max_position_size(balance, 'NEAR/USDT:USDT')
        print(f"  ${balance}: Standard=${size:.2f}, NEAR (30% reduction)=${near_size:.2f}")
    
    print("\nSymbol Validation:")
    for symbol in ['ETH/USDT:USDT', 'LINK/USDT:USDT', 'BTC/USDT:USDT']:
        valid, msg = validate_symbol(symbol)
        status = "✅" if valid else "❌"
        print(f"  {status} {symbol}: {msg}")
    
    print("\nCircuit Breaker Example:")
    triggered, reason = check_circuit_breakers(-25, -35, 2)
    status = "🔴 TRIGGERED" if triggered else "🟢 OK"
    print(f"  {status}: {reason}")
