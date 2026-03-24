"""
AGGRESSIVE OVERNIGHT TRADING CONFIGURATION
Optimized for reaching $300 from $198
"""

# AGGRESSIVE SETTINGS SUMMARY:
# ==============================
# TP: 1% (was 1.5%) - Faster profit taking
# SL: 1.5% (was 2%) - Tighter stops
# Partial Profit: 0.75% (was 1%) - Earlier 50% sell
# Breakeven: 0.5% (was 1%) - Move SL faster
# Trailing: Start 1%, Distance 0.3% (tighter)
# Confidence: 75% (was 80%) - More signals
# Scan Interval: 15s (was 30s) - Faster scanning
# Risk per Trade: 2% (was 1.5%) - Bigger positions
# Leverage: 3x + ISOLATED margin
# Max Loss per Position: $5 (unchanged - SAFETY)

# MATH FOR $300 TARGET:
# =====================
# Current: $198
# Target: $300
# Need: +$102 (+51%)
# 
# With 3x leverage:
# - 1% price move = 3% account gain
# - Each winning trade at 1% TP = ~$6 gain
# - Need ~17 winning trades
# - With 5 positions, need 3-4 full rotations

# RISK MANAGEMENT (UNCHANGED):
# =============================
# - Max $5 loss per position (enforced)
# - Max $15 daily loss (safety)
# - ISOLATED margin (risk contained)
# - Auto-close at SL

print("=" * 70)
print("AGGRESSIVE OVERNIGHT MODE ACTIVATED")
print("=" * 70)
print("TP: 1% | SL: 1.5% | Partial: 0.75% | Conf: 75% | Scan: 15s")
print("Target: $198 → $300 (+$102)")
print("=" * 70)
