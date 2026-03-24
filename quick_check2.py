from bybit_trader import BybitTrader
bt = BybitTrader()
print("=== WALLET ===")
print(bt.get_wallet_balance())
print("\n=== POSITIONS ===")
print(bt.get_positions())
