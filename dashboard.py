# Trading Dashboard - Performance Metrics
# Shows current positions, PnL, and statistics

import json
from datetime import datetime
from typing import Dict, List

class TradingDashboard:
    def __init__(self):
        self.positions = []
        self.trades_history = []
        self.daily_stats = {}
    
    def update_position(self, symbol: str, side: str, entry: float, 
                       amount: float, stop: float, target: float):
        """Add new position"""
        position = {
            'symbol': symbol,
            'side': side,
            'entry_price': entry,
            'amount': amount,
            'stop_loss': stop,
            'take_profit': target,
            'open_time': datetime.now().isoformat(),
            'status': 'OPEN'
        }
        self.positions.append(position)
        return position
    
    def close_position(self, symbol: str, exit_price: float, pnl: float, reason: str):
        """Close position and record trade"""
        for pos in self.positions:
            if pos['symbol'] == symbol and pos['status'] == 'OPEN':
                pos['status'] = 'CLOSED'
                pos['exit_price'] = exit_price
                pos['pnl'] = pnl
                pos['close_reason'] = reason
                pos['close_time'] = datetime.now().isoformat()
                
                self.trades_history.append(pos)
                self.positions.remove(pos)
                return True
        return False
    
    def get_current_positions(self) -> List[Dict]:
        """Get all open positions"""
        return [p for p in self.positions if p['status'] == 'OPEN']
    
    def get_performance_summary(self) -> Dict:
        """Get performance metrics"""
        if not self.trades_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0
            }
        
        wins = [t for t in self.trades_history if t.get('pnl', 0) > 0]
        losses = [t for t in self.trades_history if t.get('pnl', 0) <= 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in self.trades_history)
        
        return {
            'total_trades': len(self.trades_history),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(self.trades_history) * 100,
            'total_pnl': total_pnl,
            'avg_win': sum(t['pnl'] for t in wins) / len(wins) if wins else 0,
            'avg_loss': sum(t['pnl'] for t in losses) / len(losses) if losses else 0,
            'profit_factor': abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else float('inf')
        }
    
    def render_dashboard(self):
        """Render ASCII dashboard"""
        summary = self.get_performance_summary()
        open_positions = self.get_current_positions()
        
        dashboard = f"""
{'='*70}
TRADING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}

PORTFOLIO STATUS:
  Balance: $50.00 USDT
  Open Positions: {len(open_positions)}/3
  Daily PnL: Calculating...

PERFORMANCE METRICS:
  Total Trades: {summary['total_trades']}
  Win Rate: {summary['win_rate']:.1f}%
  Total PnL: ${summary['total_pnl']:.2f}
  Avg Win: +${summary['avg_win']:.2f}
  Avg Loss: ${summary['avg_loss']:.2f}
  Profit Factor: {summary['profit_factor']:.2f}

OPEN POSITIONS:
"""
        
        if open_positions:
            for pos in open_positions:
                dashboard += f"""
  [{pos['side']}] {pos['symbol']}
    Entry: ${pos['entry_price']:.2f}
    Amount: {pos['amount']:.6f}
    Stop: ${pos['stop_loss']:.2f}
    Target: ${pos['take_profit']:.2f}
    Opened: {pos['open_time'][:19]}
"""
        else:
            dashboard += "  No open positions - Scanning for setups\n"
        
        dashboard += f"""
{'='*70}
STRATEGY: Trendline Bounce + RSI + Volume
Timeframe: 4H | Risk/Trade: 1.5% | R:R: 1:2
{'='*70}
"""
        
        return dashboard
    
    def save_to_file(self, filename='dashboard.json'):
        """Save dashboard data"""
        data = {
            'positions': self.positions,
            'trades_history': self.trades_history,
            'summary': self.get_performance_summary(),
            'updated': datetime.now().isoformat()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filename='dashboard.json'):
        """Load dashboard data"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.positions = data.get('positions', [])
                self.trades_history = data.get('trades_history', [])
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    dashboard = TradingDashboard()
    print(dashboard.render_dashboard())
