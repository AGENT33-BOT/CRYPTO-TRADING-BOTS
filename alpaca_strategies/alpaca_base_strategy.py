"""
Base Strategy Class for Alpaca Trading
All strategies inherit from this base class.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

# Try to import Alpaca packages
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.data import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca packages not installed. Running in simulation mode.")

from alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, TradingConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class Signal:
    """Trading signal data structure"""
    symbol: str
    direction: str  # 'LONG', 'SHORT', 'FLAT', 'BUY', 'SELL'
    confidence: float = 0.0  # 0-100
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class SignalType:
    """Signal type constants"""
    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"
    HOLD = "HOLD"

@dataclass
class Position:
    """Position tracking"""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    quantity: float
    entry_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: str = ""
    unrealized_pnl: float = 0.0

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None, 
                 symbols: List[str] = None, timeframe: str = '1d', **kwargs):
        self.name = name
        self.config = config or {}
        self.symbols = symbols or []
        self.timeframe = timeframe
        self.enabled = self.config.get('enabled', True) if config else True
        self.trading_config = TradingConfig()
        
        # Initialize Alpaca clients if available
        self.trading_client = None
        self.data_client = None
        
        if ALPACA_AVAILABLE and ALPACA_API_KEY and ALPACA_SECRET_KEY:
            try:
                self.trading_client = TradingClient(
                    api_key=ALPACA_API_KEY,
                    secret_key=ALPACA_SECRET_KEY,
                    paper=True,
                    url_override=ALPACA_BASE_URL if 'paper' in ALPACA_BASE_URL else None
                )
                
                self.data_client = StockHistoricalDataClient(
                    api_key=ALPACA_API_KEY,
                    secret_key=ALPACA_SECRET_KEY
                )
            except Exception as e:
                logging.warning(f"Could not initialize Alpaca clients: {e}")
        
        # Logger
        self.logger = logging.getLogger(f"Strategy.{name}")
        
        # State
        self.positions: Dict[str, Position] = {}
        self.signals: List[Signal] = []
        self.equity_curve: List[Dict] = []
        self.trades: List[Dict] = []
        
    def get_historical_data(self, symbol: str, timeframe: str = '1d', 
                           limit: int = 100) -> pd.DataFrame:
        """Fetch historical price data from Alpaca"""
        if not self.data_client:
            self.logger.warning("Data client not available - returning empty DataFrame")
            return pd.DataFrame()
        
        try:
            # Map timeframe strings to TimeFrame
            tf_map = {
                '1m': TimeFrame.Minute,
                '1min': TimeFrame.Minute,
                '5m': TimeFrame(5, TimeFrame.Minute),
                '5min': TimeFrame(5, TimeFrame.Minute),
                '15m': TimeFrame(15, TimeFrame.Minute),
                '15min': TimeFrame(15, TimeFrame.Minute),
                '30m': TimeFrame(30, TimeFrame.Minute),
                '30min': TimeFrame(30, TimeFrame.Minute),
                '1h': TimeFrame.Hour,
                '1hour': TimeFrame.Hour,
                '4h': TimeFrame(4, TimeFrame.Hour),
                '4hour': TimeFrame(4, TimeFrame.Hour),
                '1d': TimeFrame.Day,
                '1day': TimeFrame.Day,
                '1w': TimeFrame.Week,
                '1week': TimeFrame.Week,
            }
            
            timeframe_obj = tf_map.get(timeframe.lower(), TimeFrame.Day)
            
            # Calculate start date
            end = datetime.now()
            if timeframe.lower() in ['1m', '1min', '5m', '5min', '15m', '15min', '30m', '30min']:
                start = end - timedelta(days=7)
            elif timeframe.lower() in ['1h', '1hour', '4h', '4hour']:
                start = end - timedelta(days=30)
            else:
                start = end - timedelta(days=365)
            
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_obj,
                start=start,
                end=end
            )
            
            bars = self.data_client.get_stock_bars(request)
            
            if symbol in bars.data:
                df = pd.DataFrame([
                    {
                        'timestamp': bar.timestamp,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume
                    }
                    for bar in bars.data[symbol]
                ])
                df.set_index('timestamp', inplace=True)
                return df
            else:
                self.logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_account(self):
        """Get account information"""
        if not self.trading_client:
            return None
        try:
            return self.trading_client.get_account()
        except Exception as e:
            self.logger.error(f"Error getting account: {e}")
            return None
    
    def get_positions(self):
        """Get current positions"""
        if not self.trading_client:
            return {}
        try:
            positions = self.trading_client.get_all_positions()
            return {p.symbol: p for p in positions}
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return {}
    
    def submit_market_order(self, symbol: str, side, 
                           qty: float, time_in_force=None):
        """Submit a market order"""
        if not self.trading_client:
            self.logger.warning("Trading client not available")
            return None
        
        try:
            if time_in_force is None:
                time_in_force = TimeInForce.DAY
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data)
            self.logger.info(f"Submitted {side.value if hasattr(side, 'value') else side} order for {qty} {symbol}")
            return order
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return None
    
    def submit_limit_order(self, symbol: str, side, 
                          qty: float, limit_price: float,
                          time_in_force=None):
        """Submit a limit order"""
        if not self.trading_client:
            self.logger.warning("Trading client not available")
            return None
        
        try:
            if time_in_force is None:
                time_in_force = TimeInForce.DAY
            
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                limit_price=limit_price,
                time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data)
            self.logger.info(f"Submitted limit order for {qty} {symbol} @ {limit_price}")
            return order
        except Exception as e:
            self.logger.error(f"Error submitting limit order: {e}")
            return None
    
    def submit_tp_sl_orders(self, symbol: str, side: str, qty: float, 
                            entry_price: float, stop_loss: float = None, 
                            take_profit: float = None):
        """Submit TP/SL bracket orders after opening a position"""
        if not self.trading_client:
            self.logger.warning("Trading client not available")
            return
        
        try:
            # Submit stop loss order
            if stop_loss:
                if side == 'LONG':
                    # For LONG: sell if price drops to stop_loss
                    stop_side = OrderSide.SELL
                    stop_price = stop_loss
                else:  # SHORT
                    # For SHORT: buy if price rises to stop_loss
                    stop_side = OrderSide.BUY
                    stop_price = stop_loss
                
                stop_order = StopOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=stop_side,
                    stop_price=stop_price,
                    time_in_force=TimeInForce.GTC
                )
                self.trading_client.submit_order(stop_order)
                self.logger.info(f"✅ Set STOP LOSS for {symbol}: {stop_price}")
            
            # Submit take profit order
            if take_profit:
                if side == 'LONG':
                    # For LONG: sell if price rises to take_profit
                    tp_side = OrderSide.SELL
                    tp_price = take_profit
                else:  # SHORT
                    # For SHORT: buy if price drops to take_profit
                    tp_side = OrderSide.BUY
                    tp_price = take_profit
                
                tp_order = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=tp_side,
                    limit_price=tp_price,
                    time_in_force=TimeInForce.GTC
                )
                self.trading_client.submit_order(tp_order)
                self.logger.info(f"✅ Set TAKE PROFIT for {symbol}: {tp_price}")
                
        except Exception as e:
            self.logger.error(f"Error setting TP/SL orders: {e}")
    
    def close_position(self, symbol: str):
        """Close a position"""
        if not self.trading_client:
            self.logger.warning("Trading client not available")
            return False
        
        try:
            self.trading_client.close_position(symbol)
            self.logger.info(f"Closed position for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                                stop_price: float) -> float:
        """Calculate position size based on risk management"""
        account = self.get_account()
        if not account:
            # Default size if no account available
            return 1
        
        equity = float(account.equity)
        risk_amount = equity * self.trading_config.risk_per_trade_pct
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share == 0:
            risk_per_share = entry_price * 0.01  # Default 1%
        
        # Calculate number of shares
        shares = risk_amount / risk_per_share
        
        # Check max position size
        max_position_value = equity * self.trading_config.max_position_size_pct
        max_shares = max_position_value / entry_price
        
        shares = min(shares, max_shares)
        
        return int(shares) if shares >= 1 else 0
    
    def calculate_stop_loss(self, entry_price: float, side: str = 'LONG', 
                           stop_pct: float = None) -> float:
        """Calculate stop loss price"""
        if stop_pct is None:
            stop_pct = self.trading_config.default_stop_loss_pct
        
        if side.upper() == 'LONG':
            return entry_price * (1 - stop_pct)
        else:  # SHORT
            return entry_price * (1 + stop_pct)
    
    def calculate_take_profit(self, entry_price: float, side: str = 'LONG', 
                              tp_pct: float = None) -> float:
        """Calculate take profit price"""
        if tp_pct is None:
            tp_pct = self.trading_config.default_take_profit_pct
        
        if side.upper() == 'LONG':
            return entry_price * (1 + tp_pct)
        else:  # SHORT
            return entry_price * (1 - tp_pct)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators - override in subclass if needed"""
        return df
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """Generate trading signals - must be implemented by subclass"""
        pass
    
    def update_positions(self):
        """Update position tracking"""
        alpaca_positions = self.get_positions()
        
        # Update local position cache
        for symbol, pos in alpaca_positions.items():
            if symbol in self.positions:
                self.positions[symbol].unrealized_pnl = float(pos.unrealized_pl)
    
    def check_exits(self) -> List[str]:
        """Check for position exits (stop loss / take profit)"""
        exits = []
        alpaca_positions = self.get_positions()
        
        for symbol, position in self.positions.items():
            if symbol not in alpaca_positions:
                continue
            
            current_price = float(alpaca_positions[symbol].current_price)
            
            if position.side == 'LONG':
                if position.stop_loss and current_price <= position.stop_loss:
                    self.logger.info(f"Stop loss hit for {symbol}")
                    self.close_position(symbol)
                    exits.append(symbol)
                elif position.take_profit and current_price >= position.take_profit:
                    self.logger.info(f"Take profit hit for {symbol}")
                    self.close_position(symbol)
                    exits.append(symbol)
            else:  # SHORT
                if position.stop_loss and current_price >= position.stop_loss:
                    self.logger.info(f"Stop loss hit for {symbol}")
                    self.close_position(symbol)
                    exits.append(symbol)
                elif position.take_profit and current_price <= position.take_profit:
                    self.logger.info(f"Take profit hit for {symbol}")
                    self.close_position(symbol)
                    exits.append(symbol)
        
        return exits
    
    def run(self):
        """Main strategy loop - override in subclass for custom behavior"""
        if not self.enabled:
            self.logger.info(f"Strategy {self.name} is disabled")
            return
        
        self.logger.info(f"Running strategy: {self.name}")
        
        # Check existing positions for exits
        self.check_exits()
        
        # Update positions
        self.update_positions()
        
        # Generate signals for each symbol
        symbols = self.config.get('symbols', [])
        for symbol in symbols:
            try:
                df = self.get_historical_data(symbol, self.config.get('timeframe', '1d'))
                if df.empty:
                    continue
                
                signal = self.generate_signals(df, symbol)
                if signal and signal.direction not in ['FLAT', 'HOLD']:
                    self.signals.append(signal)
                    self.execute_signal(signal)
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
    
    def execute_signal(self, signal: Signal):
        """Execute a trading signal"""
        # Handle both Signal formats (base strategy uses direction, some strategies use signal_type)
        direction = signal.direction
        if not direction and hasattr(signal, 'signal_type'):
            # Map signal_type to direction
            signal_type_map = {
                'BUY': 'LONG',
                'SELL': 'SHORT', 
                'LONG': 'LONG',
                'SHORT': 'SHORT'
            }
            direction = signal_type_map.get(signal.signal_type, None)
        
        if not direction or direction in ['FLAT', 'HOLD']:
            return
        
        # Get entry price (handle both price and entry_price fields)
        entry_price = signal.entry_price
        if not entry_price and hasattr(signal, 'price'):
            entry_price = signal.price
        
        # Check if we already have a position
        current_positions = self.get_positions()
        if signal.symbol in current_positions:
            self.logger.info(f"Already have position in {signal.symbol}")
            return
        
        # Calculate position size
        stop_price = signal.stop_loss or (entry_price * 0.98 if entry_price else 0)
        qty = self.calculate_position_size(signal.symbol, entry_price or 0, stop_price)
        
        if qty == 0:
            self.logger.warning(f"Calculated position size is 0 for {signal.symbol}")
            return
        
        # Submit order
        if ALPACA_AVAILABLE:
            side = OrderSide.BUY if direction in ['LONG', 'BUY'] else OrderSide.SELL
            order = self.submit_market_order(signal.symbol, side, qty)
        else:
            self.logger.info(f"[SIMULATION] Would execute {direction} for {qty} {signal.symbol}")
            order = None
        
        if order or not ALPACA_AVAILABLE:
            # Track position
            pos_side = 'LONG' if direction in ['LONG', 'BUY'] else 'SHORT'
            
            # Calculate stop loss and take profit if not provided
            sl = signal.stop_loss
            tp = signal.take_profit
            if not sl or not tp:
                if entry_price:
                    if not sl:
                        sl = self.calculate_stop_loss(entry_price, pos_side)
                    if not tp:
                        tp = self.calculate_take_profit(entry_price, pos_side)
            
            self.positions[signal.symbol] = Position(
                symbol=signal.symbol,
                side=pos_side,
                quantity=qty,
                entry_price=entry_price or 0,
                entry_time=datetime.now(),
                stop_loss=sl,
                take_profit=tp,
                strategy=self.name
            )
            
            self.logger.info(f"Executed {direction} signal for {signal.symbol}: {qty} shares | SL: {sl:.2f} | TP: {tp:.2f}")
            
            # Set TP/SL orders automatically
            if sl or tp:
                actual_entry = entry_price
                if not actual_entry and order:
                    # Try to get actual fill price from order
                    try:
                        actual_entry = float(order.filled_avg_price) if hasattr(order, 'filled_avg_price') else entry_price
                    except:
                        actual_entry = entry_price or 0
                
                self.submit_tp_sl_orders(
                    symbol=signal.symbol,
                    side=pos_side,
                    qty=qty,
                    entry_price=actual_entry,
                    stop_loss=sl,
                    take_profit=tp
                )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }
        
        trades_df = pd.DataFrame(self.trades)
        wins = len(trades_df[trades_df['pnl'] > 0])
        losses = len(trades_df[trades_df['pnl'] <= 0])
        total = len(trades_df)
        
        win_rate = (wins / total * 100) if total > 0 else 0
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if losses > 0 else 0
        
        return {
            'total_trades': total,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }
