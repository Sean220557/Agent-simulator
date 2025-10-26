@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

if not exist "venv\Scripts\python.exe" (
  python -m venv venv
)
call "venv\Scripts\activate.bat"

REM deps via Tsinghua mirror
python -m pip install -U pip setuptools wheel ^
  -i https://pypi.tuna.tsinghua.edu.cn/simple ^
  --trusted-host pypi.tuna.tsinghua.edu.cn
python -m pip install -r requirements.txt ^
  -i https://pypi.tuna.tsinghua.edu.cn/simple ^
  --trusted-host pypi.tuna.tsinghua.edu.cn

set PYTHONUTF8=1
python -m src.api_server

endlocal

