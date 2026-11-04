@echo off
chcp 65001 >nul
rem 启动千鹤桌宠
rem 用 WMI 启动：父进程是 WmiPrvSE，脱离当前进程树，
rem 这样 Harness / 这个终端关掉时，桌宠不会被一起杀掉。
set PYTHONIOENCODING=utf-8

powershell -NoProfile -Command "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='\"E:\test\uv-venv\Scripts\pythonw.exe\" \"E:\RentAGirl\pet\pet.py\"'} | Out-Null"

exit
