#!/bin/bash
set -e

# venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# deps via Tsinghua mirror
pip install -U pip setuptools wheel \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn
pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

export PYTHONUTF8=1
python -m src.api_server