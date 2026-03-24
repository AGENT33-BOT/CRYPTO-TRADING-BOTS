#!/usr/bin/env python3
"""Real-time Bybit Dashboard Generator"""
import json
import os

DASHBOARD_HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>Bybit Trading Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        h1 { color: #00ff88; }
        .balance { font-size: 2em; color: #00ff88; }
        .balance.low { color: #ff4444; }
        .card { background: #16213e; padding: 20px; margin: 10px 0; border-radius: 10px; }
        .positions { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
        .position { background: #0f3460; padding: 15px; border-radius: 8px; }
        .position.up { border-left: 4px solid #00ff88; }
        .position.down { border-left: 4px solid #ff4444; }
        .symbol { font-weight: bold; font-size: 1.2em; }
        .pnl { font-size: 1.5em; }
        .pnl.up { color: #00ff88; }
        .pnl.down { color: #ff4444; }
        .bots { display: flex; gap: 10px; flex-wrap: wrap; }
        .bot { background: #0f3460; padding: 10px 20px; border-radius: 5px; }
        .bot.running { border: 2px solid #00ff88; }
        .bot.stopped { border: 2px solid #ff4444; }
        .timestamp { color: #888; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Bybit Trading Dashboard</h1>
        <span class="timestamp">Last updated: <span id="time"></span></span>
    </div>
    
    <div class="card">
        <h2>💰 Balance</h2>
        <div class="balance" id="balance">Loading...</div>
    </div>
    
    <div class="card">
        <h2>📈 Open Positions</h2>
        <div class="positions" id="positions">Loading...</div>
    </div>
    
    <div class="card">
        <h2>🤖 Bot Status</h2>
        <div class="bots" id="bots">Loading...</div>
    </div>

    <script>
        document.getElementById('time').textContent = new Date().toLocaleTimeString();
        
        // Fetch data from API
        fetch('data.json')
            .then(r => r.json())
            .then(data => {{
                // Balance
                const balanceEl = document.getElementById('balance');
                balanceEl.textContent = '$' + data.balance.toFixed(2) + ' USDT';
                if (data.balance < 50) balanceEl.classList.add('low');
                
                // Positions
                const positionsEl = document.getElementById('positions');
                data.positions.forEach(pos => {{
                    const div = document.createElement('div');
                    div.className = 'position ' + (pos.pnl >= 0 ? 'up' : 'down');
                    div.innerHTML = `
                        <div class="symbol">${{pos.symbol}}</div>
                        <div>${{pos.side}} | ${{pos.size}}</div>
                        <div class="pnl ${{pos.pnl >= 0 ? 'up' : 'down'}}">
                            ${{pos.pnl >= 0 ? '+' : ''}}$${{pos.pnl.toFixed(2)}}
                        </div>
                    `;
                    positionsEl.appendChild(div);
                }});
                
                // Bots
                const botsEl = document.getElementById('bots');
                data.bots.forEach(bot => {{
                    const div = document.createElement('div');
                    div.className = 'bot ' + bot.status;
                    div.textContent = bot.name + ': ' + bot.status.toUpperCase();
                    botsEl.appendChild(div);
                }});
            }});
    </script>
</body>
</html>
'''

def update_dashboard():
    """Update dashboard with current data"""
    # Read current balance and positions
    try:
        import subprocess
        result = subprocess.run(['python', 'quick_check.py'], capture_output=True, text=True, cwd='crypto_trader')
        output = result.stdout
        
        # Parse balance
        balance = 0.0
        positions = []
        for line in output.split('\n'):
            if 'Balance:' in line:
                balance = float(line.split('Balance:')[1].split('USDT')[0].strip())
            if 'PnL' in line and 'USDT' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pnl = float(parts[-1].replace('$', '').replace('USDT', ''))
                        positions.append({'symbol': 'UNKNOWN', 'side': 'UNKNOWN', 'size': 0, 'pnl': pnl})
                    except:
                        pass
        
        data = {
            'balance': balance,
            'positions': positions,
            'bots': [
                {'name': 'Mean Reversion', 'status': 'running'},
                {'name': 'Momentum', 'status': 'running'},
                {'name': 'Scalping', 'status': 'running'},
                {'name': 'Grid', 'status': 'running'},
                {'name': 'Funding', 'status': 'running'}
            ]
        }
        
        with open('dashboard/data.json', 'w') as f:
            json.dump(data, f)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    update_dashboard()
