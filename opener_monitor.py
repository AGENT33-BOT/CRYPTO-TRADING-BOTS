#!/usr/bin/env python3
"""
Auto Position Opener Monitor
Checks if auto_position_opener.py is running and restarts if needed.
"""

import psutil
import subprocess
import sys
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('opener_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def is_opener_running():
    """Check if auto_position_opener.py process is running."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('auto_position_opener.py' in str(arg) for arg in cmdline):
                    logger.info(f"Found running process: PID {proc.info['pid']}")
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    except Exception as e:
        logger.error(f"Error checking processes: {e}")
        return False, None

def restart_opener():
    """Restart the auto_position_opener.py script."""
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        opener_path = os.path.join(script_dir, 'auto_position_opener.py')
        
        if not os.path.exists(opener_path):
            logger.error(f"auto_position_opener.py not found at {opener_path}")
            return False
        
        logger.info(f"Starting {opener_path}...")
        
        # Start the process detached (so it continues after monitor exits)
        if sys.platform == 'win32':
            # Windows: use CREATE_NEW_PROCESS_GROUP and DETACHED_PROCESS
            process = subprocess.Popen(
                [sys.executable, opener_path],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                cwd=script_dir
            )
        else:
            # Unix: use nohup and disown pattern via start_new_session
            process = subprocess.Popen(
                [sys.executable, opener_path],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                cwd=script_dir
            )
        
        logger.info(f"Auto Position Opener restarted with PID {process.pid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to restart opener: {e}")
        return False

def main():
    """Main monitor logic."""
    logger.info("=" * 60)
    logger.info("Auto Position Opener Monitor - Checking status...")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    running, pid = is_opener_running()
    
    if running:
        logger.info(f"[OK] Auto Position Opener is running (PID: {pid})")
        return 0
    else:
        logger.warning("[ALERT] Auto Position Opener is NOT running!")
        logger.info("Attempting to restart...")
        
        if restart_opener():
            logger.info("[OK] Successfully restarted Auto Position Opener")
            return 0
        else:
            logger.error("[FAIL] Failed to restart Auto Position Opener")
            return 1

if __name__ == '__main__':
    sys.exit(main())
