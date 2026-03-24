"""Test Telegram Connection"""
import os
import requests

TOKEN = '7594239785:AAG6YjJ4LDK0vMQT5Cq2LHS5-9q-OWJb8oI'
CHAT_ID = '5804173449'

print("Testing Telegram connection...")
print(f"Bot Token: {TOKEN[:20]}...")
print(f"Chat ID: {CHAT_ID}")

# Test getMe
try:
    response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getMe', timeout=10)
    data = response.json()
    
    if data.get('ok'):
        bot_info = data['result']
        print(f"\n[OK] Bot connected!")
        print(f"  Bot Name: {bot_info.get('first_name')}")
        print(f"  Bot Username: @{bot_info.get('username')}")
        print(f"  Bot ID: {bot_info.get('id')}")
    else:
        print(f"\n[ERROR] Bot connection failed:")
        print(f"  {data.get('description')}")
        
except Exception as e:
    print(f"\n[ERROR] {e}")

# Test send message
try:
    print("\nSending test message...")
    message = "AGENT33 Test: Telegram connection verified!"
    response = requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        json={'chat_id': CHAT_ID, 'text': message},
        timeout=10
    )
    data = response.json()
    
    if data.get('ok'):
        print("[OK] Test message sent successfully!")
    else:
        print(f"[ERROR] Failed to send message:")
        print(f"  {data.get('description')}")
        
        # Check if chat ID is wrong
        if 'chat not found' in data.get('description', '').lower():
            print("\n  [HINT] Chat ID might be incorrect.")
            print("  Try getting your chat ID from @userinfobot")
            
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "="*50)
print("Check your Telegram for the test message!")
print("="*50)
