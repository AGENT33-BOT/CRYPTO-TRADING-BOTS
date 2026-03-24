"""
Bot Health Monitor - Restarts stopped bots
"""
import os
import subprocess
import sys

SCRIPTS_DIR = r"C:\Users\digim\OneDrive\Pictures\auto_opener_monitor\crypto_trader"

def check_and_restart():
    # Check scalping bot
    result = subprocess.run(
        [sys.executable, "check_bots.py"],
        cwd=SCRIPTS_DIR,
        capture_output=True,
        text=True
    )
    
    output = result.stdout
    
    # If scalping bot stopped, restart it
    if "Scalping Bot: STOPPED" in output:
        print("Scalping Bot stopped - restarting...")
        subprocess.Popen(
            [sys.executable, "scalping_bot.py"],
            cwd=SCRIPTS_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    
    if "Momentum Bot: STOPPED" in output:
        print("Momentum Bot stopped - restarting...")
        subprocess.Popen(
            [sys.executable, "momentum_trader.py"],
            cwd=SCRIPTS_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

if __name__ == "__main__":
    check_and_restart()
