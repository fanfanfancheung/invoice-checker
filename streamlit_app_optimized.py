"""
发票检查器 - Streamlit优化版本
采购发票自动化验证系统 - 性能优化版
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
from functools import lru_cache

# 页面配置
st.set_page_config(
    page_title="发票检查器",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据库路径
DB_PATH = "invoice_checker.db"

# ========================================
# 🔧 性能优化1: 数据库连接池
# ========================================
@st.cache_resource
def get_db_connection():
    """缓存的数据库连接（单例模式）"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 允许按列名访问
    return conn

# ========================================
# 🔧 性能优化2: 将CSS移到外部，避免每次渲染
# ========================================
@st.cache_data
def load_css():
    """缓存CSS样式"""
    return """
<style>
    .main { background: linear-gradient(to bottom right, #EFF6FF, #E0E7FF); }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: 600; }
    .metric-card { background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
    h1 { color: #1F2937; font-size: 2.5rem !important; margin-bottom: 0.5rem !important; }
    .subtitle { color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem; }
</style>
"""

st.markdown(load_css(), unsafe_allow_html=True)

# ========================================
# 数据库初始化
# ========================================
def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT UNIQUE NOT NULL,
        order_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        file_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER,
        contract_number TEXT,
        spec_model TEXT,
        quantity INTEGER,
        amount REAL,
        file_name TEXT,
        status TEXT DEFAULT 'verified',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_id) REFERENCES contracts (id)
    )''')
    
    conn.commit()

# ========================================
# 🔧 性能优化3: 缓存数据库查询
# ========================================
@st.cache_data(ttl=10)  # 缓存10秒，避免频繁查询
def get_all_contracts():
    """获取所有合同及状态（带缓存）"""
    conn = get_db_connection()
    query = '''
        SELECT 
            c.id, c.po_number, c.order_date, c.quantity, c.total_amount,
            COALESCE(SUM(i.amount), 0) as invoiced_amount,
            COALESCE(SUM(i.quantity), 0) as invoiced_quantity,
            COUNT(i.id) as invoice_count
        FROM contracts c
        LEFT JOIN invoices i ON c.id = i.contract_id
        GROUP BY c.id
        ORDER BY c.order_date DESC
    '''
    df = pd.read_sql_query(query, conn)
    return df

@st.cache_data(ttl=10)
def get_contract_invoices(contract_id):
    """获取某个合同的所有发票（带缓存）"""
    conn = get_db_connection()
    query = '''
        SELECT spec_model, quantity, amount, status, created_at, file_name
        FROM invoices 
        WHERE contract_id = ?
        ORDER BY created_at DESC
    '''
    df = pd.read_sql_query(query, conn, params=(contract_id,))
    return df

def add_contract(po_number, order_date, quantity, total_amount, file_name):
    """添加合同"""
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO contracts (po_number, order_date, quantity, total_amount, file_name)
                     VALUES (?, ?, ?, ?, ?)''',
                  (po_number, order_date, quantity, total_amount, file_name))
        conn.commit()
        # 🔧 清除缓存，强制重新查询
        get_all_contracts.clear()
        return True, "合同添加成功！"
    except sqlite3.IntegrityError:
        return False, "采购单号已存在！"

def add_invoice(contract_number, spec_model, quantity, amount, file_name):
    """添加发票"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM contracts WHERE po_number = ?", (contract_number,))
    result = c.fetchone()
    
    if not result:
        return False, f"未找到合同号: {contract_number}"
    
    contract_id = result[0]
    
    c.execute('''INSERT INTO invoices (contract_id, contract_number, spec_model, quantity, amount, file_name)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (contract_id, contract_number, spec_model, quantity, amount, file_name))
    conn.commit()
    
    # 🔧 清除缓存
    get_all_contracts.clear()
    get_contract_invoices.clear()
    
    return True, "发票验证通过并添加！"

# 初始化数据库
init_db()

# ========================================
# 🔧 性能优化4: 优化 session state 管理
# ========================================
if 'upload_type' not in st.session_state:
    st.session_state.upload_type = 'contract'
if 'expanded_contract' not in st.session_state:
    st.session_state.expanded_contract = None  # 只存储当前展开的合同ID

# 标题
st.markdown("# 📋 发票检查器")
st.markdown('<p class="subtitle">采购发票自动化验证系统 ⚡️ 优化版</p>', unsafe_allow_html=True)

# ========================================
# 侧边栏 - 上传区域
# ========================================
with st.sidebar:
    st.markdown("### 📤 文件上传")
    
    upload_type = st.radio(
        "选择上传类型",
        ["📄 合同", "🧾 发票"],
        key="upload_type_radio",
        horizontal=True
    )
    
    st.markdown("---")
    
    if "合同" in upload_type:
        st.markdown("#### 上传合同")
        uploaded_file = st.file_uploader(
            "拖拽或选择文件",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            key="contract_uploader"
        )
        
        if uploaded_file:
            st.success(f"已选择: {uploaded_file.name}")
            
            with st.form("contract_form"):
                st.markdown("##### OCR识别结果")
                st.caption("(演示版 - 请手动输入)")
                
                contracts_df = get_all_contracts()
                next_po = f"PO-2024{len(contracts_df) + 1:03d}"
                
                po_number = st.text_input("采购单号", value=next_po)
                order_date = st.date_input("订单日期", value=datetime.now())
                quantity = st.number_input("数量", min_value=1, value=100, step=1)
                total_amount = st.number_input("总金额(¥)", min_value=0.0, value=50000.0, step=1000.0)
                
                submitted = st.form_submit_button("✅ 确认添加合同", use_container_width=True)
                
                if submitted:
                    success, message = add_contract(
                        po_number, 
                        str(order_date), 
                        quantity, 
                        total_amount,
                        uploaded_file.name
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    else:  # 发票
        st.markdown("#### 上传发票")
        uploaded_file = st.file_uploader(
            "拖拽或选择文件",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            key="invoice_uploader"
        )
        
        if uploaded_file:
            st.success(f"已选择: {uploaded_file.name}")
            
            with st.form("invoice_form"):
                st.markdown("##### OCR识别结果")
                st.caption("(演示版 - 请手动输入)")
                
                contracts_df = get_all_contracts()
                if len(contracts_df) == 0:
                    st.warning("⚠️ 请先添加合同")
                else:
                    contract_options = contracts_df['po_number'].tolist()
                    contract_number = st.selectbox("关联合同号", contract_options)
                    spec_model = st.text_input("规格型号", value="SKU-A001")
                    quantity = st.number_input("数量", min_value=1, value=50, step=1)
                    amount = st.number_input("发票金额(¥)", min_value=0.0, value=25000.0, step=1000.0)
                    
                    submitted = st.form_submit_button("✅ 确认添加发票", use_container_width=True)
                    
                    if submitted:
                        success, message = add_invoice(
                            contract_number,
                            spec_model,
                            quantity,
                            amount,
                            uploaded_file.name
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    
    st.markdown("---")
    st.markdown("### 📊 统计")
    contracts_df = get_all_contracts()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("合同总数", len(contracts_df))
    with col2:
        completed = len(contracts_df[abs(contracts_df['total_amount'] - contracts_df['invoiced_amount']) < 0.01]) if len(contracts_df) > 0 else 0
        st.metric("已完成", completed)

# ========================================
# 主区域 - 合同列表
# ========================================
st.markdown("## 📑 合同列表")

contracts_df = get_all_contracts()

if len(contracts_df) == 0:
    st.info("📭 暂无合同数据，请在左侧上传合同文件")
else:
    # 添加筛选
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "已完成", "未完成"])
    with col2:
        sort_by = st.selectbox("排序", ["日期(新→旧)", "日期(旧→新)", "金额(高→低)", "金额(低→高)"])
    
    # 应用筛选
    filtered_df = contracts_df.copy()
    if status_filter == "已完成":
        filtered_df = filtered_df[abs(filtered_df['total_amount'] - filtered_df['invoiced_amount']) < 0.01]
    elif status_filter == "未完成":
        filtered_df = filtered_df[abs(filtered_df['total_amount'] - filtered_df['invoiced_amount']) >= 0.01]
    
    # 应用排序
    if "旧→新" in sort_by:
        filtered_df = filtered_df.sort_values('order_date', ascending=True)
    elif "金额(高→低)" in sort_by:
        filtered_df = filtered_df.sort_values('total_amount', ascending=False)
    elif "金额(低→高)" in sort_by:
        filtered_df = filtered_df.sort_values('total_amount', ascending=True)
    
    st.markdown("---")
    
    # 🔧 性能优化5: 使用 container 和 expander 减少重渲染
    for _, row in filtered_df.iterrows():
        is_complete = abs(row['total_amount'] - row['invoiced_amount']) < 0.01
        status_emoji = "🟢" if is_complete else "🟡"
        status_text = "✓ 金额一致" if is_complete else f"欠 ¥{row['total_amount'] - row['invoiced_amount']:,.2f}"
        
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([0.3, 1.5, 1, 1, 1.5, 1.2])
            
            with col1:
                st.markdown(f"<h2 style='margin:0;'>{status_emoji}</h2>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{row['po_number']}**")
            with col3:
                st.text(row['order_date'])
            with col4:
                st.text(f"数量: {row['quantity']}")
            with col5:
                st.markdown(f"**¥{row['total_amount']:,.2f}**")
            with col6:
                if is_complete:
                    st.success(status_text)
                else:
                    st.warning(status_text)
            
            # 使用 expander 替代按钮控制，减少交互开销
            with st.expander(f"📋 查看发票明细 ({int(row['invoice_count'])}张)"):
                invoices_df = get_contract_invoices(row['id'])
                if len(invoices_df) > 0:
                    st.markdown("##### 发票明细")
                    # 🔧 使用 DataFrame 显示，比循环快
                    display_df = invoices_df[['spec_model', 'quantity', 'amount', 'created_at']].copy()
                    display_df.columns = ['规格型号', '数量', '金额', '创建时间']
                    display_df['金额'] = display_df['金额'].apply(lambda x: f"¥{x:,.2f}")
                    display_df['创建时间'] = display_df['创建时间'].str[:10]
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("暂无发票")
            
            st.markdown("---")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 1rem;'>
    <p>💪 发票检查器 v0.2.0 | Streamlit 优化版 ⚡️</p>
    <p><small>性能优化: 数据库连接池 | 查询缓存 | CSS缓存 | 减少重渲染</small></p>
</div>
""", unsafe_allow_html=True)
