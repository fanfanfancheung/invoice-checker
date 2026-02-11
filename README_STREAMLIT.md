# 发票检查器 - Streamlit版本

## 🎉 一个文件搞定前后端！

这是发票检查器的Streamlit版本，相比Next.js+FastAPI版本：
- ✅ **更简单** - 一个Python文件，无需前后端分离
- ✅ **更快** - 5分钟部署到Streamlit Cloud
- ✅ **免费托管** - Streamlit Cloud完全免费

---

## 🚀 立即部署到Streamlit Cloud

### 步骤1: 推送到GitHub（已完成✓）

代码已在: https://github.com/fanfanfancheung/invoice-checker

### 步骤2: 部署到Streamlit Cloud

1. 访问: https://share.streamlit.io
2. 点击 "New app"
3. 填写信息:
   - **Repository**: `fanfanfancheung/invoice-checker`
   - **Branch**: `master`
   - **Main file path**: `streamlit_app.py`
4. 点击 "Deploy"

等待1-2分钟，你的应用就上线了！🎉

---

## 💻 本地运行

### 安装依赖

```bash
pip install streamlit pandas
```

### 启动应用

```bash
cd tools/invoice-checker
streamlit run streamlit_app.py
```

自动在浏览器打开: http://localhost:8501

---

## ✨ 功能特性

### 侧边栏 - 上传区域
- 📄 上传合同
- 🧾 上传发票
- 📊 实时统计

### 主区域 - 合同管理
- 📋 合同列表展示
- 🟢 绿色 = 金额一致（已完成）
- 🟡 黄色 = 金额不足（未完成）
- 🔍 筛选和排序
- 📝 展开查看发票明细

### 状态验证
- ✅ 自动计算已开发票金额
- ⚠️ 显示还欠多少金额
- 📈 统计已完成/未完成合同数

---

## 📸 界面预览

```
┌──────────────────────────────────────────────┐
│ 📋 发票检查器                  [侧边栏: 上传] │
│ 采购发票自动化验证系统                        │
├──────────────────────────────────────────────┤
│                                              │
│ 📑 合同列表                                  │
│                                              │
│ 🟢 PO-2024001 | 2024-01-15 | ¥50,000 | ✓已齐│
│    [📋 查看发票明细 (2张)]                   │
│                                              │
│ 🟡 PO-2024002 | 2024-01-16 | ¥80,000 | 欠¥30k│
│    [📋 查看发票明细 (1张)]                   │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🆚 vs Next.js版本

| 特性 | Streamlit版本 | Next.js版本 |
|------|--------------|-------------|
| **开发速度** | ⚡️ 超快 (1个文件) | 🐌 较慢 (前后端分离) |
| **部署难度** | ✅ 简单 (一键部署) | ⚠️ 复杂 (需配置2个服务) |
| **成本** | 💰 免费 | 💰 免费 (Vercel+Railway) |
| **自定义界面** | ⚠️ 受限于Streamlit组件 | ✅ 完全自定义CSS |
| **性能** | 🐢 页面刷新慢一点 | 🚀 React SPA快 |
| **适合场景** | 内部工具、快速原型 | 正式产品、复杂交互 |

---

## 🎯 推荐使用场景

**选择Streamlit版本 (streamlit_app.py)：**
- ✅ 快速上线测试
- ✅ 团队内部使用
- ✅ 数据密集型应用
- ✅ Python开发者友好

**选择Next.js版本 (frontend/ + backend/)：**
- ✅ 需要精美界面
- ✅ 面向客户的产品
- ✅ 复杂的前端交互
- ✅ 需要移动端优化

---

## 📝 数据存储

Streamlit版本使用SQLite数据库（`invoice_checker.db`）：
- ✅ 数据持久化保存
- ✅ 重启应用数据不丢失
- ⚠️ 仅适合单用户或小团队
- 💡 生产环境建议升级到PostgreSQL

---

## 🔧 后续优化方向

### MVP已完成 ✅
- 合同/发票上传
- 数据存储
- 金额验证
- 状态展示

### 第二阶段 ⏳
- [ ] 接入OCR API（腾讯云/百度云）
- [ ] 规格型号模糊匹配
- [ ] 批量导入Excel
- [ ] 数据导出功能
- [ ] 领星API集成

### 第三阶段 🔮
- [ ] 多用户权限管理
- [ ] 审批工作流
- [ ] 邮件通知
- [ ] 数据看板

---

## 🆘 常见问题

**Q: Streamlit Cloud部署失败？**
A: 确保 `requirements.txt` 在根目录，内容为:
```
streamlit==1.31.0
pandas==2.2.0
```

**Q: 数据会丢失吗？**
A: Streamlit Cloud的数据库在应用休眠后可能丢失。正式使用建议：
- 连接外部数据库（PostgreSQL）
- 定期导出备份

**Q: 能处理多少数据？**
A: SQLite适合 <10000条记录。更大数据量需升级数据库。

**Q: 如何连接PostgreSQL？**
A: 修改 `streamlit_app.py` 的连接字符串：
```python
import psycopg2
conn = psycopg2.connect(st.secrets["postgres_url"])
```

---

## 💪 下一步

1. **立即部署**: 访问 https://share.streamlit.io 部署应用
2. **本地测试**: `streamlit run streamlit_app.py`
3. **定制开发**: 修改 `streamlit_app.py` 添加功能

---

**Happy Streamliting! 🎈**
