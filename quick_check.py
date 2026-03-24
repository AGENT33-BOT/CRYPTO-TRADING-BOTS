# Quick check of current positions and TP/SL status
import sys
sys.path.insert(0, r'C:\Users\digim\clawd\crypto_trader')
import bybit_wrapper
import json

client = bybit_wrapper.BybitClient()
pos = client.get_positions()

print("="*60)
print("📊 CURRENT POSITIONS WITH TP/SL STATUS")
print("="*60)

for p in pos:
    size = float(p.get('size', 0))
    if size != 0:
        symbol = p['symbol']
        entry = p.get('entry_price', 0)
        tp = p.get('take_profit', 0)
        sl = p.get('stop_loss', 0)
        pnl = p.get('unrealised_pnl', 0)
        
        tp_status = "✅ SET" if float(tp) != 0 else "❌ MISSING"
        sl_status = "✅ SET" if float(sl) != 0 else "❌ MISSING"
        
        print(f"\n🔹 {symbol}")
        print(f"   Size: {size} | Entry: {entry}")
        print(f"   P&L: ${float(pnl):.2f}")
        print(f"   TP: {tp} ({tp_status})")
        print(f"   SL: {sl} ({sl_status})")

print("\n" + "="*60)
