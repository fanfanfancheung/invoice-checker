#!/bin/bash

# 发票检查器 - 一键部署脚本

echo "🚀 发票检查器 - 一键部署"
echo "=========================="
echo ""

# 检查Git
if ! command -v git &> /dev/null; then
    echo "❌ 未找到 Git，请先安装"
    exit 1
fi

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo "📦 初始化Git仓库..."
    git init
    git add .
    git commit -m "feat: 初始化发票检查器项目"
fi

echo "请选择部署方式:"
echo "1) Vercel + Railway (推荐，免费)"
echo "2) Docker本地运行"
echo "3) Render (一体化部署)"
echo ""
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📱 Vercel + Railway 部署"
        echo "========================"
        echo ""
        echo "步骤1: 部署后端到Railway"
        echo "1. 访问: https://railway.app"
        echo "2. 点击 'New Project' → 'Deploy from GitHub repo'"
        echo "3. 选择这个仓库"
        echo "4. Root Directory: backend/"
        echo "5. Start Command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
        echo "6. 复制Railway给你的URL (例如: https://xxx.railway.app)"
        echo ""
        read -p "按回车继续..."
        echo ""
        echo "步骤2: 部署前端到Vercel"
        echo "1. 访问: https://vercel.com"
        echo "2. 点击 'Add New' → 'Project'"
        echo "3. Import这个仓库"
        echo "4. Root Directory: frontend/"
        echo "5. 添加环境变量:"
        echo "   NEXT_PUBLIC_API_URL = <你的Railway URL>"
        echo "6. 点击 Deploy"
        echo ""
        echo "✅ 完成！访问Vercel给你的URL即可使用"
        ;;
    2)
        echo ""
        echo "🐳 Docker本地运行"
        echo "================="
        if ! command -v docker &> /dev/null; then
            echo "❌ 未找到 Docker，请先安装: https://www.docker.com/get-started"
            exit 1
        fi
        echo "构建并启动容器..."
        docker-compose up --build -d
        echo ""
        echo "✅ 启动成功！"
        echo "前端: http://localhost:3000"
        echo "后端: http://localhost:8000"
        echo "API文档: http://localhost:8000/docs"
        ;;
    3)
        echo ""
        echo "🎨 Render 部署"
        echo "=============="
        echo "1. 访问: https://render.com"
        echo "2. 点击 'New' → 'Blueprint'"
        echo "3. 连接这个Git仓库"
        echo "4. Render会自动检测并部署"
        echo ""
        echo "或者手动配置:"
        echo "- Service: Web Service"
        echo "- Build Command: cd backend && pip install -r requirements.txt"
        echo "- Start Command: uvicorn main:app --host 0.0.0.0 --port \$PORT"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================="
echo "💪 需要帮助？查看 DEPLOY.md"
