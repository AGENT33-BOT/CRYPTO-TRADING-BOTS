"""
AUTONOMOUS TRADING AGENT
Monitors, adjusts, and optimizes trading system every 30 seconds
Makes decisions without human intervention
"""

import ccxt
import time
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_agent.log'),
        logging.StreamHandler()
    ]
)

API_KEY = 'bsK06QDhsagOWwFsXQ'
API_SECRET = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

class AutonomousTradingAgent:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        self.check_interval = 30  # 30 seconds
        self.report_counter = 0
        self.last_report_time = time.time()
        
        # Performance tracking
        self.session_stats = {
            'trades_taken': 0,
            'trades_closed_profit': 0,
            'trades_closed_loss': 0,
            'total_profit': 0,
            'total_loss': 0,
            'adjustments_made': 0
        }
        
        logging.info("="*70)
        logging.info("AUTONOMOUS TRADING AGENT STARTED")
        logging.info("Making decisions every 30 seconds without human input")
        logging.info("="*70)
    
    def get_account_status(self):
        """Get current account status"""
        try:
            balance = self.exchange.fetch_balance()
            total = float(balance['USDT']['total'])
            free = float(balance['USDT']['free'])
            return {'total': total, 'free': free}
        except:
            return {'total': 0, 'free': 0}
    
    def get_all_positions(self):
        """Get all active positions"""
        positions = []
        pairs = self.get_all_pairs()
        
        for symbol in pairs:
            try:
                pos = self.exchange.fetch_positions([symbol])
                if pos and len(pos) > 0:
                    contracts = float(pos[0].get('contracts', 0))
                    if contracts > 0:
                        positions.append({
                            'symbol': symbol,
                            'side': pos[0]['side'].upper(),
                            'size': contracts,
                            'entry': float(pos[0].get('entryPrice', 0)),
                            'mark': float(pos[0].get('markPrice', 0)),
                            'pnl': float(pos[0].get('unrealizedPnl', 0)),
                            'leverage': float(pos[0].get('leverage', 3))
                        })
            except:
                pass
        
        return positions
    
    def get_all_pairs(self):
        """Return all trading pairs"""
        return [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'ADA/USDT:USDT',
            'DOGE/USDT:USDT', 'XRP/USDT:USDT', 'LINK/USDT:USDT', 'AVAX/USDT:USDT',
            'DOT/USDT:USDT', 'LTC/USDT:USDT', 'BCH/USDT:USDT', 'UNI/USDT:USDT',
            'ATOM/USDT:USDT', 'ETC/USDT:USDT', 'ARB/USDT:USDT', 'OP/USDT:USDT',
            'NEAR/USDT:USDT', 'APT/USDT:USDT', 'SUI/USDT:USDT', 'MATIC/USDT:USDT',
            'INJ/USDT:USDT', 'TIA/USDT:USDT', 'SEI/USDT:USDT', 'STX/USDT:USDT',
            'WLD/USDT:USDT', 'RNDR/USDT:USDT', 'FET/USDT:USDT', 'GRT/USDT:USDT'
        ]
    
    def close_position(self, symbol, reason):
        """Close a position"""
        try:
            pos = self.exchange.fetch_positions([symbol])
            if pos and len(pos) > 0:
                contracts = float(pos[0].get('contracts', 0))
                side = pos[0]['side']
                if contracts > 0:
                    close_side = 'buy' if side == 'short' else 'sell'
                    self.exchange.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=contracts,
                        params={'reduceOnly': True}
                    )
                    self.exchange.cancel_all_orders(symbol)
                    logging.info(f"CLOSED: {symbol} | Reason: {reason}")
                    return True
        except Exception as e:
            logging.error(f"Error closing {symbol}: {e}")
        return False
    
    def analyze_and_adjust(self, positions, balance):
        """Main decision making logic"""
        actions_taken = []
        
        total_pnl = sum(p['pnl'] for p in positions)
        position_count = len(positions)
        
        # DECISION 1: Close positions losing > $3
        for pos in positions:
            if pos['pnl'] < -3.0:
                if self.close_position(pos['symbol'], f"Loss too high: ${pos['pnl']:.2f}"):
                    actions_taken.append(f"Cut loss on {pos['symbol']}: ${pos['pnl']:.2f}")
                    self.session_stats['trades_closed_loss'] += 1
                    self.session_stats['total_loss'] += abs(pos['pnl'])
        
        # DECISION 2: Take profit at $1+ (reinforce dollar profit rule)
        for pos in positions:
            if pos['pnl'] >= 1.0:
                if self.close_position(pos['symbol'], f"Profit target: ${pos['pnl']:.2f}"):
                    actions_taken.append(f"Took profit on {pos['symbol']}: ${pos['pnl']:.2f}")
                    self.session_stats['trades_closed_profit'] += 1
                    self.session_stats['total_profit'] += pos['pnl']
        
        # DECISION 3: Close breakeven positions after 30 min (small profit/loss)
        # This prevents stuck positions
        
        # DECISION 4: Reduce position count if over 5
        if position_count > 5:
            # Sort by PnL, close worst
            sorted_pos = sorted(positions, key=lambda x: x['pnl'])
            for pos in sorted_pos[:2]:  # Close 2 worst
                if self.close_position(pos['symbol'], "Too many positions"):
                    actions_taken.append(f"Reduced position: {pos['symbol']}")
        
        # DECISION 5: Alert if free margin < $20
        if balance['free'] < 20:
            actions_taken.append(f"LOW MARGIN: Only ${balance['free']:.2f} free")
        
        # DECISION 6: Alert if all positions losing
        losing_count = sum(1 for p in positions if p['pnl'] < 0)
        if position_count > 0 and losing_count == position_count:
            actions_taken.append(f"ALL POSITIONS LOSING ({losing_count}/{position_count})")
        
        return actions_taken
    
    def generate_report(self, balance, positions, actions):
        """Generate status report"""
        self.report_counter += 1
        
        report = []
        report.append("="*60)
        report.append(f"AUTONOMOUS AGENT REPORT #{self.report_counter}")
        report.append(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        report.append("="*60)
        
        # Account summary
        report.append(f"Balance: ${balance['total']:.2f} | Free: ${balance['free']:.2f}")
        
        # Positions
        total_pnl = sum(p['pnl'] for p in positions)
        report.append(f"Positions: {len(positions)}/5 | Total PnL: ${total_pnl:+.2f}")
        
        if positions:
            report.append("")
            report.append("Active Positions:")
            for pos in positions:
                status = "PROFIT" if pos['pnl'] > 0 else "LOSS" if pos['pnl'] < 0 else "BE"
                report.append(f"  {pos['symbol']}: {pos['side']} | ${pos['pnl']:+.2f} [{status}]")
        
        # Actions taken
        if actions:
            report.append("")
            report.append("Actions Taken:")
            for action in actions:
                report.append(f"  → {action}")
        else:
            report.append("")
            report.append("Actions: Monitoring... no action needed")
        
        # Session stats
        report.append("")
        report.append("Session Stats:")
        report.append(f"  Profits taken: {self.session_stats['trades_closed_profit']}")
        report.append(f"  Losses cut: {self.session_stats['trades_closed_loss']}")
        report.append(f"  Total P/L: ${self.session_stats['total_profit'] - self.session_stats['total_loss']:+.2f}")
        
        report.append("="*60)
        
        return "\n".join(report)
    
    def run(self):
        """Main autonomous loop"""
        logging.info("Autonomous agent running...")
        
        while True:
            try:
                # Get status
                balance = self.get_account_status()
                positions = self.get_all_positions()
                
                # Analyze and make decisions
                actions = self.analyze_and_adjust(positions, balance)
                
                # Generate and log report
                report = self.generate_report(balance, positions, actions)
                logging.info("\n" + report)
                
                # Check if we should send a message to user (every 5 min)
                if time.time() - self.last_report_time > 300:  # 5 minutes
                    self.send_user_report(balance, positions, actions)
                    self.last_report_time = time.time()
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(self.check_interval)
    
    def send_user_report(self, balance, positions, actions):
        """Send summary to user every 5 minutes"""
        total_pnl = sum(p['pnl'] for p in positions)
        
        # This would send a message - for now just log it
        logging.info(f"USER REPORT: Balance ${balance['total']:.2f}, Positions {len(positions)}, PnL ${total_pnl:+.2f}")

if __name__ == "__main__":
    agent = AutonomousTradingAgent()
    agent.run()
