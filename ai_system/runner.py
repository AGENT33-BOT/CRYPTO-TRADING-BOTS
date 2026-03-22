"""
AI Autonomous Trading Runner
Run this to start the AI trading system
"""

import asyncio
import logging
from datetime import datetime

from . import AITradingSystem
from .config import TRADING_CONFIG, API_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutonomousTrader:
    """
    Main class to run the autonomous trading system
    """
    
    def __init__(self):
        # Get API config
        api_key = API_CONFIG['bybit']['api_key']
        api_secret = API_CONFIG['bybit']['api_secret']
        
        # Initialize AI system
        self.ai_system = AITradingSystem(api_key, api_secret)
        
        # Load config
        self.symbols = TRADING_CONFIG['symbols']
        self.interval = TRADING_CONFIG['analysis_interval']
        
        logger.info("🤖 Autonomous Trader initialized")
        logger.info(f"📊 Trading symbols: {self.symbols}")
    
    async def start(self):
        """Start autonomous trading"""
        logger.info("🚀 Starting Autonomous Trading...")
        logger.info(f"⏱️ Analysis interval: {self.interval}s")
        
        try:
            await self.ai_system.run_autonomous(
                symbols=self.symbols,
                interval=self.interval
            )
        except KeyboardInterrupt:
            logger.info("🛑 Stopping...")
            self.ai_system.stop()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.ai_system.stop()
    
    async def analyze_single(self, symbol: str):
        """Analyze a single symbol"""
        signal = await self.ai_system.generate_signal(symbol)
        
        if signal:
            logger.info(f"📊 Signal for {symbol}: {signal}")
        else:
            logger.info(f"📊 No signal for {symbol}")
        
        return signal
    
    async def get_status(self):
        """Get system status"""
        positions = await self.ai_system.position_manager.get_positions()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'open_positions': len(positions),
            'positions': positions,
            'is_running': self.ai_system.is_running
        }


async def main():
    """Main entry point"""
    trader = AutonomousTrader()
    
    # Start trading
    await trader.start()


if __name__ == '__main__':
    asyncio.run(main())


# Usage examples:

# Example 1: Run autonomous
# asyncio.run(main())

# Example 2: Single analysis
# async def test():
#     trader = AutonomousTrader()
#     signal = await trader.analyze_single('BTCUSDT')
# asyncio.run(test())

# Example 3: Get status
# async def status():
#     trader = AutonomousTrader()
#     status = await trader.get_status()
#     print(status)
# asyncio.run(status())
