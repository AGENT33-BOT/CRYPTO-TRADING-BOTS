import os

print("=== GRID TRADER LOG (last 5 lines) ===")
if os.path.exists('grid_trader.log'):
    with open('grid_trader.log') as f:
        lines = f.readlines()
        for line in lines[-5:]:
            print(line.strip())
else:
    print("NO LOG FILE")

print("\n=== FUNDING ARBITRAGE LOG (last 5 lines) ===")
if os.path.exists('funding_arbitrage.log'):
    with open('funding_arbitrage.log') as f:
        lines = f.readlines()
        for line in lines[-5:]:
            print(line.strip())
else:
    print("NO LOG FILE")

print("\n=== SCALPING BOT LOG (last 3 lines) ===")
if os.path.exists('scalping_bot.log'):
    with open('scalping_bot.log') as f:
        lines = f.readlines()
        for line in lines[-3:]:
            print(line.strip())
else:
    print("NO LOG FILE")

print("\n=== MOMENTUM BOT LOG (last 3 lines) ===")
if os.path.exists('momentum_bot.log'):
    with open('momentum_bot.log') as f:
        lines = f.readlines()
        for line in lines[-3:]:
            print(line.strip())
else:
    print("NO LOG FILE")

print("\n=== MEAN REVERSION LOG (last 3 lines) ===")
if os.path.exists('mean_reversion_bot.log'):
    with open('mean_reversion_bot.log') as f:
        lines = f.readlines()
        for line in lines[-3:]:
            print(line.strip())
else:
    print("NO LOG FILE")
