"""
CHALLENGE MODE CONFIGURATION v2.0
$516 → $616 in 36 Hours (+$100 / 19.4% Return)
Created: March 5, 2026 - 7:54 PM ET
Restarted with lesson learned from failed 25x attempt
"""

# CHALLENGE PARAMETERS
CHALLENGE_MODE = True
STARTING_BALANCE = 516.01
TARGET_BALANCE = 616.01
TARGET_PROFIT = 100.00  # +$100
CHALLENGE_START_TIME = "2026-03-05 19:54:00"
CHALLENGE_END_TIME = "2026-03-07 07:54:00"  # 36 hours later

# PHASE 1: CONSISTENT SCALPING (Hours 0-12)
# Target: $516 → $566 (+$50 / +9.7%)
# LESSON LEARNED: 5x max leverage (not 25x!), 15% sizing
PHASE1_CONFIG = {
    'enabled': True,
    'leverage': 5,  # REDUCED from 25x - lesson learned!
    'position_size_pct': 0.15,  # 15% of account per trade (was 4%)
    'position_size_usd': 75,  # ~$75 per position at 5x = ~$375 notional
    'tp_pct': 0.03,  # 3% price move = 15% gain on position
    'sl_pct': 0.015,  # 1.5% price move = 7.5% loss on position
    'max_loss_per_position_usd': 10,  # HARD STOP: Close if -$10 reached
    'max_positions': 2,  # REDUCED from 4 - focus on quality
    'timeframe': '15m',  # SLOWER from 3m - better signals
    'scan_interval': 30,  # Slower scanning for better setups
    'symbols': ['ETH/USDT:USDT', 'NEAR/USDT:USDT'],  # Removed SOL (too volatile)
    'rsi_period': 14,
    'rsi_oversold': 30,  # STRICTER (was 35)
    'rsi_overbought': 70,  # STRICTER (was 65)
    'bb_period': 20,
    'bb_std': 2,
    'confidence_threshold': 75,  # HIGHER = better quality signals (was 65)
    'min_risk_reward': 2.0,  # Minimum 2:1 R:R
}

# PHASE 2: MOMENTUM SURFING (Hours 12-24)
# Target: $566 → $596 (+$30 / +5.3%)
PHASE2_CONFIG = {
    'enabled': False,  # Will enable after Phase 1
    'leverage': 3,  # Even lower for momentum
    'position_size_pct': 0.20,  # 20% per trade
    'tp_pct': 0.04,  # 4% = 12% gain with 3x
    'sl_pct': 0.02,  # 2% = 6% loss with 3x
    'max_positions': 2,
    'timeframe': '30m',  # Higher timeframe for momentum
    'symbols': ['ETH/USDT:USDT', 'BTC/USDT:USDT'],
    'volume_threshold': 1.3,  # 130% of average volume
}

# PHASE 3: GRID FINISH (Hours 24-36)
# Target: $596 → $616+ (+$20 / +3.4%)
PHASE3_CONFIG = {
    'enabled': False,  # Will enable after Phase 2
    'leverage': 3,
    'grid_levels': 8,
    'grid_spacing_pct': 0.02,  # 2% between levels
    'position_per_level_pct': 0.10,  # 10% per level
    'symbols': ['ETH/USDT:USDT', 'NEAR/USDT:USDT'],
}

# RISK MANAGEMENT - HARD STOPS (LESSONS APPLIED)
RISK_CONFIG = {
    'daily_loss_limit_usd': 51.60,  # 10% of account (was 20%)
    'max_drawdown_pct': 0.15,  # 15% - END CHALLENGE (was 30%)
    'consecutive_losses_limit': 2,  # Take 2-hour break (was 3)
    'max_loss_per_position_usd': 10,  # $10 hard stop per position
    'max_positions_total': 2,  # Max 2 positions (was 4)
    'trailing_stop_enabled': True,
    'trailing_stop_pct': 0.02,  # 2% trailing (wider for 5x)
    'breakeven_trigger_pct': 0.02,  # Move to breakeven at +2%
    'auto_close_on_profit_target': True,
    'partial_close_enabled': True,  # Take 50% at 1.5%, rest at 3%
}

# TRADE TRACKING
trade_log = []
phase1_trades = []
phase2_trades = []
phase3_trades = []

# PERFORMANCE TRACKING
stats = {
    'total_trades': 0,
    'wins': 0,
    'losses': 0,
    'win_rate': 0.0,
    'total_pnl': 0.0,
    'largest_win': 0.0,
    'largest_loss': 0.0,
    'current_phase': 1,
    'phase1_pnl': 0.0,
    'phase2_pnl': 0.0,
    'phase3_pnl': 0.0,
}

# ALERT CONFIGURATION
ALERT_CONFIG = {
    'telegram_enabled': True,
    'telegram_user_id': '5804173449',
    'alert_on_trade': True,
    'alert_on_phase_change': True,
    'alert_on_daily_limit': True,
    'alert_interval_minutes': 60,  # Hourly updates
}

print("=" * 70)
print("BYBIT CHALLENGE MODE v2.0 - RESTARTED")
print("=" * 70)
print(f"Starting Balance: ${STARTING_BALANCE}")
print(f"Target Balance: ${TARGET_BALANCE}")
print(f"Target Profit: ${TARGET_PROFIT}")
print(f"Duration: 36 Hours")
print("=" * 70)
print("LESSONS APPLIED:")
print("  • 5x max leverage (not 25x)")
print("  • 15% sizing per trade")
print("  • 15m timeframe (not 3m)")
print("  • Stricter entry criteria (RSI 30/70)")
print("  • Lower risk limits (10% daily, 15% max DD)")
print("=" * 70)
print("PHASE 1: Consistent Scalping (5x leverage, 15% sizing)")
print("PHASE 2: Momentum Surfing (3x leverage, 20% sizing)")
print("PHASE 3: Grid Finish (3x leverage)")
print("=" * 70)
print(f"Daily Loss Limit: ${RISK_CONFIG['daily_loss_limit_usd']}")
print(f"Max Drawdown: {RISK_CONFIG['max_drawdown_pct'] * 100}%")
print("=" * 70)
