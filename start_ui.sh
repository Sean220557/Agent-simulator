#!/bin/bash

echo "================================"
echo "AgentSociety Web UI 启动脚本"
echo "================================"
echo ""

# 检查虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "[错误] 未找到虚拟环境，请先运行以下命令创建："
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "[1/3] 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "[2/3] 检查依赖..."
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[警告] 缺少 fastapi，正在安装依赖..."
    pip install fastapi uvicorn -q
fi

# 启动服务器
echo "[3/3] 启动Web服务器..."
echo ""
echo "================================"
echo "🚀 服务器即将启动"
echo "================================"
echo "📱 Web界面: http://localhost:8000/ui"
echo "📚 API文档: http://localhost:8000/docs"
echo "================================"
echo "按 Ctrl+C 停止服务器"
echo "================================"
echo ""

# 使用 -m 方式运行，确保导入路径正确
python -m src.api_server

