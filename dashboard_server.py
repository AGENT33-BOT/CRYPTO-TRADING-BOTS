"""
Dashboard Server for Crypto Trading Bots
Serves the dashboard HTML and provides API for trading data
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import threading
from datetime import datetime

# Trading data storage
class TradingDataStore:
    def __init__(self):
        self.data = {
            'balance': 469.84,  # Challenge starting balance
            'challenge': {
                'starting_balance': 469.84,
                'target_balance': 938.00,
                'start_time': '2026-03-03T13:25:00-05:00',
                'duration_hours': 24,
                'positions_open': 0,
                'risk_limit': 375.87,  # 20% stop
                'status': 'ACTIVE'
            },
            'trendline': {
                'positions': [],
                'trades': 0,
                'wins': 0,
                'pnl': 0.0
            },
            'bybit': {
                'positions': [],
                'trades': 0,
                'wins': 0,
                'pnl': 0.0
            },
            'last_updated': datetime.now().isoformat()
        }
        self.lock = threading.Lock()
    
    def update(self, bot, data):
        with self.lock:
            if bot in self.data:
                self.data[bot].update(data)
                self.data['last_updated'] = datetime.now().isoformat()
    
    def update_balance(self, balance):
        with self.lock:
            self.data['balance'] = balance
            self.data['last_updated'] = datetime.now().isoformat()
    
    def get_data(self):
        with self.lock:
            return self.data.copy()

data_store = TradingDataStore()

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def do_GET(self):
        if self.path == '/api/trading-data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data_store.get_data()).encode())
        elif self.path == '/':
            self.path = '/dashboard.html'
            super().do_GET()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/update':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                update = json.loads(body)
                if 'bot' in update and 'data' in update:
                    data_store.update(update['bot'], update['data'])
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'ok'}).encode())
                elif 'balance' in update:
                    data_store.update_balance(update['balance'])
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'ok'}).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logs
        pass

def run_server(port=8080):
    server = HTTPServer(('localhost', port), DashboardHandler)
    print(f"🚀 Dashboard server running at http://localhost:{port}")
    print(f"📊 View your trading dashboard at http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
