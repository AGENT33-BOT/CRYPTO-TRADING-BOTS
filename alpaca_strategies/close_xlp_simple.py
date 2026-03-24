import os
from dotenv import load_dotenv
load_dotenv('.alpaca_env')
from alpaca.trading.client import TradingClient
client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
client.close_position('XLP')
print('XLP closed')
