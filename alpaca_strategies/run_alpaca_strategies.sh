#!/bin/bash
# Alpaca Strategy Launcher
echo "============================================"
echo "  Alpaca Strategy Manager"
echo "============================================"
echo ""

if [ -z "$1" ]; then
    echo "Usage: ./run_alpaca_strategies.sh [strategy_name|all|status]"
    echo ""
    echo "Examples:"
    echo "  ./run_alpaca_strategies.sh all"
    echo "  ./run_alpaca_strategies.sh ema_crossover"
    echo "  ./run_alpaca_strategies.sh rsi_mean_reversion"
    echo ""
    echo "Available strategies:"
    echo "  ma_crossover, ema_crossover, macd_trend, supertrend"
    echo "  atr_trend, adx_trend, rsi_mean_reversion, bb_mean_reversion"
    echo "  vwap_reversion, zscore_reversion, stochastic_reversion"
    echo "  breakout_retest, volatility_squeeze, range_breakout"
    echo "  momentum_ignition, grid_trading, dca_scaling"
    echo "  pairs_trading, statistical_arbitrage, market_making"
    echo "  sector_rotation, portfolio_rebalancer, risk_parity"
    exit 0
fi

cd "$(dirname "$0")"
python3 alpaca_strategy_manager.py "$1"
