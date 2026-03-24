Get-CimInstance Win32_Process -Filter "name='python.exe'" | Select-Object ProcessId, CommandLine | Where-Object { $_.CommandLine -like '*crypto_trader*' } | Format-Table -AutoSize
