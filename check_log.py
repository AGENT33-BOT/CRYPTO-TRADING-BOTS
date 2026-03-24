with open('funding_arbitrage.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    print(f'Total lines: {len(lines)}')
    print(''.join(lines[-10:]))
