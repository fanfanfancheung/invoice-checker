# 发票检查器 (Invoice Checker)

采购发票自动化验证和上传系统

## 功能特性

- 📤 拖拽上传合同和发票
- 🔍 自动OCR识别关键信息
- ✅ 智能验证规格型号和金额
- 🎨 实时状态展示（绿色/黄色标记）
- 📊 合同发票关联管理

## 技术栈

- **前端**: Next.js 14 + TypeScript + Tailwind CSS
- **后端**: Python FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **OCR**: 腾讯云OCR API

## 快速开始

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:3000

## MVP 功能清单

- [x] 项目初始化
- [ ] 文件上传接口
- [ ] OCR识别引擎
- [ ] 合同数据存储
- [ ] 发票验证逻辑
- [ ] 前端拖拽界面
- [ ] 状态显示系统
