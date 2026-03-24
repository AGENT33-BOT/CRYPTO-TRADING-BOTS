@echo off
echo ===========================================
echo Auto Position Opener Monitor - %date% %time%
echo ===========================================
cd /d "C:\Users\digim\clawd\crypto_trader"
python -c "import psutil; print('Checking processes...'); [print(f'Found: {p.info[\"pid\"]} - {\" \".join(p.info[\"cmdline\"] or [])}') for p in psutil.process_iter(['pid','cmdline']) if 'auto_position_opener' in ' '.join(p.info['cmdline'] or [])]"
echo.
echo Check complete
echo ===========================================
