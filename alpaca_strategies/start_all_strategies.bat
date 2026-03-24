@echo off
REM Start all Alpaca strategies in separate background processes

cd /d "C:\Users\digim\clawd\crypto_trader\alpaca_strategies"

echo Starting all Alpaca strategies...
echo.

REM Trend Following Strategies
start /B python alpaca_strategy_manager.py ma_crossover > logs\ma_crossover.log 2>&1
echo Started: MA Crossover

start /B python alpaca_strategy_manager.py ema_crossover > logs\ema_crossover.log 2>&1
echo Started: EMA Crossover

start /B python alpaca_strategy_manager.py macd_trend > logs\macd_trend.log 2>&1
echo Started: MACD Trend

start /B python alpaca_strategy_manager.py supertrend > logs\supertrend.log 2>&1
echo Started: Supertrend

start /B python alpaca_strategy_manager.py atr_trend > logs\atr_trend.log 2>&1
echo Started: ATR Trend

start /B python alpaca_strategy_manager.py adx_trend > logs\adx_trend.log 2>&1
echo Started: ADX Trend

REM Mean Reversion Strategies
start /B python alpaca_strategy_manager.py rsi_mean_reversion > logs\rsi_mean_reversion.log 2>&1
echo Started: RSI Mean Reversion

start /B python alpaca_strategy_manager.py bb_mean_reversion > logs\bb_mean_reversion.log 2>&1
echo Started: BB Mean Reversion

start /B python alpaca_strategy_manager.py vwap_reversion > logs\vwap_reversion.log 2>&1
echo Started: VWAP Reversion

start /B python alpaca_strategy_manager.py zscore_reversion > logs\zscore_reversion.log 2>&1
echo Started: Z-Score Reversion

start /B python alpaca_strategy_manager.py stochastic_reversion > logs\stochastic_reversion.log 2>&1
echo Started: Stochastic Reversion

REM Breakout/Momentum Strategies
start /B python alpaca_strategy_manager.py breakout_retest > logs\breakout_retest.log 2>&1
echo Started: Breakout Retest

start /B python alpaca_strategy_manager.py volatility_squeeze > logs\volatility_squeeze.log 2>&1
echo Started: Volatility Squeeze

start /B python alpaca_strategy_manager.py range_breakout > logs\range_breakout.log 2>&1
echo Started: Range Breakout

start /B python alpaca_strategy_manager.py momentum_ignition > logs\momentum_ignition.log 2>&1
echo Started: Momentum Ignition

REM Grid/DCA Strategies
start /B python alpaca_strategy_manager.py grid_trading > logs\grid_trading.log 2>&1
echo Started: Grid Trading

start /B python alpaca_strategy_manager.py dca_scaling > logs\dca_scaling.log 2>&1
echo Started: DCA Scaling

REM Statistical Arbitrage Strategies
start /B python alpaca_strategy_manager.py pairs_trading > logs\pairs_trading.log 2>&1
echo Started: Pairs Trading

start /B python alpaca_strategy_manager.py statistical_arbitrage > logs\statistical_arbitrage.log 2>&1
echo Started: Statistical Arbitrage

start /B python alpaca_strategy_manager.py market_making > logs\market_making.log 2>&1
echo Started: Market Making

echo.
echo All strategies started in background.
echo Check logs\ folder for output.
