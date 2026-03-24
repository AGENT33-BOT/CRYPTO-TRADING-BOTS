@echo off
echo ============================================
echo  Alpaca Strategy Manager
echo ============================================
echo.

if "%~1"=="" (
    echo Usage: run_alpaca_strategies.bat [strategy_name^|all^|status]
    echo.
    echo Examples:
    echo   run_alpaca_strategies.bat all
    echo   run_alpaca_strategies.bat ema_crossover
    echo   run_alpaca_strategies.bat rsi_mean_reversion
    echo   run_alpaca_strategies.bat status
    echo.
    echo Available strategies:
    echo   ma_crossover, ema_crossover, macd_trend, supertrend
    echo   atr_trend, adx_trend, rsi_mean_reversion, bb_mean_reversion
    echo   vwap_reversion, zscore_reversion, stochastic_reversion
    echo   breakout_retest, volatility_squeeze, range_breakout
    echo   momentum_ignition, grid_trading, dca_scaling
    echo   pairs_trading, statistical_arbitrage, market_making
    echo   sector_rotation, portfolio_rebalancer, risk_parity
    goto :eof
)

cd /d "%~dp0"
python alpaca_strategy_manager.py %1
