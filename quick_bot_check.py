import psutil
import sys

print("=" * 60)
print("AGENT33 BOT STATUS CHECK")
print("=" * 60)

bots = {
    "Mean Reversion": ["mean_reversion", "meanreversion"],
    "Momentum": ["momentum"],
    "Scalping": ["scalping", "scalp"],
    "Grid Trading": ["grid", "grid_trading"],
    "Funding Arbitrage": ["funding", "arbitrage"]
}

found_bots = {name: [] for name in bots}

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] and 'python' in proc.info['name'].lower():
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            for bot_name, keywords in bots.items():
                for kw in keywords:
                    if kw in cmdline.lower():
                        found_bots[bot_name].append((proc.info['pid'], cmdline[-60:]))
                        break
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

print("\nBOT STATUS:")
for bot_name, instances in found_bots.items():
    if instances:
        for pid, cmd in instances[:1]:
            print(f"  [OK] {bot_name}: RUNNING (PID: {pid})")
    else:
        print(f"  [MISSING] {bot_name}: NOT RUNNING")

running = sum(1 for v in found_bots.values() if v)
print(f"\nSUMMARY: {running}/5 bots active")
