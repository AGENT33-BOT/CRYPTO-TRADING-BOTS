"""
Monitor Grid + Funding Arbitrage performance
Run this to check bot health and profits
"""
import os
import re
from datetime import datetime

def check_grid_performance():
    """Check grid trading performance"""
    log_file = 'grid_trading.log'
    if not os.path.exists(log_file):
        return {"status": "No log file", "fills": 0, "profit": 0}
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Count fills
    buy_fills = len(re.findall(r'BUY filled', content))
    sell_fills = len(re.findall(r'SELL filled', content))
    
    # Check if running
    is_running = "Grid active" in content[-1000:] if len(content) > 1000 else "Grid active" in content
    
    return {
        "status": "Running" if is_running else "Stopped",
        "buy_fills": buy_fills,
        "sell_fills": sell_fills,
        "total_fills": buy_fills + sell_fills
    }

def check_funding_performance():
    """Check funding arbitrage performance"""
    log_file = 'funding_arbitrage.log'
    if not os.path.exists(log_file):
        return {"status": "No log file", "opportunities": 0, "active": 0}
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Count opportunities found
    opportunities = len(re.findall(r'ENTERING|OPPORTUNITY', content))
    active = len(re.findall(r'Active arbitrages: (\d+)', content))
    
    # Get last active count
    last_active = 0
    matches = re.findall(r'Active arbitrages: (\d+)', content)
    if matches:
        last_active = int(matches[-1])
    
    return {
        "status": "Running" if "Sleeping" in content[-500:] else "Stopped",
        "opportunities_found": opportunities,
        "active_arbitrages": last_active
    }

if __name__ == "__main__":
    print("=" * 60)
    print("BOT PERFORMANCE MONITOR")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    grid = check_grid_performance()
    funding = check_funding_performance()
    
    print("GRID TRADING:")
    print(f"  Status: {grid['status']}")
    print(f"  Buy Fills: {grid['buy_fills']}")
    print(f"  Sell Fills: {grid['sell_fills']}")
    print(f"  Total Fills: {grid['total_fills']}")
    print()
    
    print("FUNDING ARBITRAGE:")
    print(f"  Status: {funding['status']}")
    print(f"  Opportunities Found: {funding['opportunities_found']}")
    print(f"  Active Arbitrages: {funding['active_arbitrages']}")
    print()
    
    print("=" * 60)
