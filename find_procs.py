"""Find Python processes by command line - using psutil"""
import psutil
import sys

def find_procs_by_name(name):
    """Find processes matching name in command line"""
    matching = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'python' in proc.info['name'].lower() and name in cmdline:
                matching.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return matching

if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
        pids = find_procs_by_name(name)
        for pid in pids:
            print(pid)
    else:
        # List all python processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    print(f"{proc.info['pid']}: {cmdline[:100]}")
            except:
                pass
