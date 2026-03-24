"""
Auto Position Opener Bot Monitor
Checks if auto_position_opener.py is running and restarts if needed
"""
import psutil
import subprocess
import sys
import time
from datetime import datetime
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('opener_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SCRIPT_NAME = 'auto_position_opener.py'
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCRIPT_NAME)

def is_bot_running():
    """Check if auto_position_opener.py process is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and SCRIPT_NAME in ' '.join(cmdline):
                logger.info(f"Found running process: PID {proc.info['pid']}")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def restart_bot():
    """Restart the auto position opener bot"""
    try:
        logger.info(f"Starting {SCRIPT_NAME}...")
        subprocess.Popen(
            [sys.executable, SCRIPT_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        logger.info(f"{SCRIPT_NAME} restarted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        return False

def main():
    """Main monitor loop"""
    logger.info("="*60)
    logger.info("AUTO POSITION OPENER MONITOR STARTED")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Monitoring: {SCRIPT_NAME}")
    logger.info("="*60)
    
    check_count = 0
    while True:
        try:
            check_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            
            logger.info(f"[{current_time}] Check #{check_count} - Checking if bot is running...")
            
            if not is_bot_running():
                logger.warning(f"⚠️ {SCRIPT_NAME} is NOT running!")
                logger.info("Attempting to restart...")
                if restart_bot():
                    logger.info("✅ Bot restarted successfully")
                    time.sleep(5)  # Give it time to start
                else:
                    logger.error("❌ Failed to restart bot")
            else:
                logger.info(f"✅ {SCRIPT_NAME} is running normally")
            
            # Wait before next check (check every 2 minutes)
            time.sleep(120)
            
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            time.sleep(120)

if __name__ == "__main__":
    main()
