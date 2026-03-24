import sys
sys.path.insert(0, '.')
from bybit import bybit

api1 = bybit('bybit')
api2 = bybit('bybit2')

print("MAIN BYBIT:")
try:
    b1 = api1.balance()
    print(b1)
except Exception as e:
    print(f"Error: {e}")

print("\nBYBIT2:")
try:
    b2 = api2.balance()
    print(b2)
except Exception as e:
    print(f"Error: {e}")
