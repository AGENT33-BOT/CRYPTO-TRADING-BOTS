"""
Position Manager - Handles opening/closing positions
"""

import ccxt
from typing import Dict, List, Optional


class PositionManager:
    """Manages trading positions on Bybit"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
    
    async def open_position(self, symbol: str, side: str, size: float, 
                          tp_percent: float = 2.5, sl_percent: float = 2.5) -> Dict:
        """
        Open a new position with TP/SL
        """
        try:
            # Clean symbol
            clean_symbol = symbol.replace('/', '').replace('-', '')
            if not clean_symbol.endswith('USDT'):
                clean_symbol += 'USDT'
            
            # Get current price
            ticker = self.exchange.fetch_ticker(clean_symbol)
            price = ticker['last']
            
            # Calculate TP/SL
            if side.upper() == 'BUY' or side == 'long':
                tp_price = price * (1 + tp_percent / 100)
                sl_price = price * (1 - sl_percent / 100)
            else:  # SELL / short
                tp_price = price * (1 - tp_percent / 100)
                sl_price = price * (1 + sl_percent / 100)
            
            # Set leverage
            try:
                self.exchange.set_leverage(10, clean_symbol)
            except:
                pass
            
            # Open position
            order = self.exchange.create_market_order(
                symbol=clean_symbol,
                side=side.lower(),
                amount=size,
                params={
                    'takeProfit': str(round(tp_price, 4)),
                    'stopLoss': str(round(sl_price, 4))
                }
            )
            
            return {
                'success': True,
                'order_id': order.get('id'),
                'symbol': clean_symbol,
                'side': side,
                'size': size,
                'entry': price,
                'tp': tp_price,
                'sl': sl_price
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_position(self, symbol: str) -> Dict:
        """Close existing position"""
        try:
            clean_symbol = symbol.replace('/', '').replace('-', '')
            if not clean_symbol.endswith('USDT'):
                clean_symbol += 'USDT'
            
            positions = self.exchange.fetch_positions([clean_symbol])
            
            for pos in positions:
                if float(pos.get('contracts', 0)) > 0:
                    # Close position
                    self.exchange.create_market_order(
                        symbol=clean_symbol,
                        side='sell' if pos['side'] == 'long' else 'buy',
                        amount=pos['contracts']
                    )
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get open positions"""
        try:
            positions = self.exchange.fetch_positions()
            open_positions = []
            
            for pos in positions:
                if float(pos.get('contracts', 0)) > 0:
                    if symbol is None or symbol in pos['symbol']:
                        open_positions.append({
                            'symbol': pos['symbol'],
                            'side': pos['side'],
                            'size': pos['contracts'],
                            'entry': pos['entryPrice'],
                            'mark': pos['markPrice'],
                            'pnl': pos.get('unrealizedPnl', 0),
                            'tp': pos.get('takeProfit'),
                            'sl': pos.get('stopLoss')
                        })
            
            return open_positions
            
        except Exception as e:
            return []
    
    async def update_trailing_stop(self, symbol: str, trailing_percent: float = 1.0):
        """Update trailing stop for position"""
        # Implementation using Bybit API
        pass
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance['total'].get('USDT', 0),
                'free': balance['free'].get('USDT', 0),
                'used': balance['used'].get('USDT', 0)
            }
        except:
            return {'total': 0, 'free': 0, 'used': 0}
