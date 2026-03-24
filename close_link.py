import sys
sys.path.insert(0, '.')
from bybit import ByBit

b = ByBit()
result = b.close_position('LINK/USDT:USDT')
print(result)
