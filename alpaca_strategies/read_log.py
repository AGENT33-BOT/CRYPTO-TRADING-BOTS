with open('strategy_manager.log', 'r') as f:
    lines = f.readlines()
    total = len(lines)
    print(f'Total lines: {total}')
    for line in lines[-50:]:
        print(line.rstrip())
