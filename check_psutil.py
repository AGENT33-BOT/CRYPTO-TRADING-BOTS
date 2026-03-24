import psutil
try:
    import psutil
    print("psutil OK")
except ImportError:
    print("psutil missing")
