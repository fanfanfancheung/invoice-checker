#!/bin/bash

# 发票检查器 - 开发环境启动脚本

echo "🚀 启动发票检查器开发环境..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装"
    exit 1
fi

# 启动后端
echo ""
echo "📦 启动后端 API..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ 后端运行在 http://localhost:8000"

# 启动前端
echo ""
echo "🎨 启动前端..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "✅ 前端运行在 http://localhost:3000"

echo ""
echo "======================================"
echo "🎉 发票检查器已启动！"
echo "======================================"
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"

# 等待退出信号
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
