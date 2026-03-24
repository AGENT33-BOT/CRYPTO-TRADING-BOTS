import ccxt
import time

# Bybit credentials
api_key = 'bsK06QDhsagOWwFsXQ'
api_secret = 'ObTb9OWB0wkqAXZKuditbRo987NKpmM6VCLa'

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

# Cancel DOGE orders in a loop for 30 seconds
print("Cancelling DOGE orders for 30 seconds...")
end_time = time.time() + 30
cancelled_total = 0

while time.time() < end_time:
    try:
        orders = exchange.fetch_open_orders('DOGE/USDT:USDT')
        if not orders:
            print(f"No more orders. Total cancelled: {cancelled_total}")
            break
        for o in orders:
            try:
                exchange.cancel_order(o['id'], 'DOGE/USDT:USDT')
                print(f"Cancelled: {o['side']} {o['amount']} @ {o.get('price', 'market')}")
                cancelled_total += 1
            except Exception as e:
                print(f"Error cancelling: {e}")
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)

print(f"\nFinal count: {cancelled_total} orders cancelled")
