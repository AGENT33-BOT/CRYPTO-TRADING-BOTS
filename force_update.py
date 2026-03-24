"""
Force update the risk_per_trade setting
"""

# Read the file
with open('ml_trader_live.py', 'r') as f:
    lines = f.readlines()

# Find and replace the line
for i, line in enumerate(lines):
    if 'self.risk_per_trade = 0.02' in line or 'self.risk_per_trade =0.02' in line:
        lines[i] = '        self.risk_per_trade = 0.20  # 20% of balance per trade\n'
        print(f'Line {i+1} updated: {lines[i].strip()}')

# Write back
with open('ml_trader_live.py', 'w') as f:
    f.writelines(lines)

print('File updated successfully!')

# Verify
with open('ml_trader_live.py', 'r') as f:
    content = f.read()
    if 'self.risk_per_trade = 0.20' in content:
        print('✅ Verified: 0.20 (20%) is now set!')
    else:
        print('❌ Still showing old value')
        print('Looking for:', [l for l in content.split('\n') if 'risk_per_trade' in l])
