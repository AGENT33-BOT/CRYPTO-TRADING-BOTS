import json
import os
from datetime import datetime, timedelta

# Check for closed trades log
closed_trades_file = 'closed_trades.json'
if os.path.exists(closed_trades_file):
    with open(closed_trades_file, 'r') as f:
        trades = json.load(f)
    recent = [t for t in trades if datetime.fromisoformat(t['close_time']) > datetime.now() - timedelta(hours=24)]
    print(f'Recent closed trades (last 24h): {len(recent)}')
    for t in recent[-5:]:
        print(f"  {t['symbol']}: {t['side']} PnL: ${t.get('realized_pnl', 'N/A')}")
else:
    print('No closed trades file found - checking alternative sources...')
    # Check if there's a trades directory or other log
    if os.path.exists('trades'):
        print(f'Found trades directory with {len(os.listdir("trades"))} files')
    else:
        print('No additional trade history found')