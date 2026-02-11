#!/bin/bash

# 切换到优化版本的脚本

echo "📋 发票检查器 - 切换到优化版本"
echo "================================"

# 检查文件是否存在
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ 错误: 找不到 streamlit_app.py"
    exit 1
fi

if [ ! -f "streamlit_app_optimized.py" ]; then
    echo "❌ 错误: 找不到 streamlit_app_optimized.py"
    exit 1
fi

# 备份原版本
echo "🔄 备份原版本..."
cp streamlit_app.py streamlit_app_original.py
echo "✅ 已备份到 streamlit_app_original.py"

# 替换为优化版本
echo "🚀 切换到优化版本..."
cp streamlit_app_optimized.py streamlit_app.py
echo "✅ 已替换为优化版本"

echo ""
echo "🎉 切换完成！"
echo ""
echo "📌 现在可以运行:"
echo "   streamlit run streamlit_app.py"
echo ""
echo "💡 如果需要恢复原版本:"
echo "   cp streamlit_app_original.py streamlit_app.py"
echo ""
