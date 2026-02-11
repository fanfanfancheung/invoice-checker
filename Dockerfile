# 发票检查器 - Docker镜像

# 阶段1: 构建前端
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 阶段2: 后端运行环境
FROM python:3.11-slim
WORKDIR /app

# 安装依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/.next/standalone ./static
COPY --from=frontend-builder /app/frontend/.next/static ./static/_next/static

# 创建上传目录
RUN mkdir -p uploads/contracts uploads/invoices

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
