"""
发票检查器 - Streamlit版本
采购发票自动化验证系统
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# 页面配置
st.set_page_config(
    page_title="发票检查器",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(to bottom right, #EFF6FF, #E0E7FF);
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
    }
    .upload-section {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .contract-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .contract-complete {
        border-left-color: #10B981;
        background-color: #F0FDF4;
    }
    .contract-incomplete {
        border-left-color: #F59E0B;
        background-color: #FFFBEB;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    h1 {
        color: #1F2937;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 数据库初始化
DB_PATH = "invoice_checker.db"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 合同表
    c.execute('''CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT UNIQUE NOT NULL,
        order_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        file_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 发票表
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
    conn.close()

def get_all_contracts():
    """获取所有合同及状态"""
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()
    return df

def get_contract_invoices(contract_id):
    """获取某个合同的所有发票"""
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT id, spec_model, quantity, amount, status, created_at, file_name
        FROM invoices 
        WHERE contract_id = ?
        ORDER BY created_at DESC
    '''
    df = pd.read_sql_query(query, conn, params=(contract_id,))
    conn.close()
    return df

def add_contract(po_number, order_date, quantity, total_amount, file_name):
    """添加合同"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO contracts (po_number, order_date, quantity, total_amount, file_name)
                     VALUES (?, ?, ?, ?, ?)''',
                  (po_number, order_date, quantity, total_amount, file_name))
        conn.commit()
        return True, "合同添加成功！"
    except sqlite3.IntegrityError:
        return False, "采购单号已存在！"
    finally:
        conn.close()

def delete_contract(contract_id):
    """删除合同及其关联发票"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM invoices WHERE contract_id = ?", (contract_id,))
        c.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
        conn.commit()
        return True, "合同已删除！"
    except Exception as e:
        return False, f"删除失败: {str(e)}"
    finally:
        conn.close()

def delete_invoice(invoice_id):
    """删除单张发票"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
        return True, "发票已删除！"
    except Exception as e:
        return False, f"删除失败: {str(e)}"
    finally:
        conn.close()

def add_invoice(contract_number, spec_model, quantity, amount, file_name):
    """添加发票"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 查找对应合同
    c.execute("SELECT id FROM contracts WHERE po_number = ?", (contract_number,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return False, f"未找到合同号: {contract_number}"
    
    contract_id = result[0]
    
    c.execute('''INSERT INTO invoices (contract_id, contract_number, spec_model, quantity, amount, file_name)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (contract_id, contract_number, spec_model, quantity, amount, file_name))
    conn.commit()
    conn.close()
    return True, "发票验证通过并添加！"

# 初始化数据库
init_db()

# 初始化session state
if 'upload_type' not in st.session_state:
    st.session_state.upload_type = 'contract'
if 'show_details' not in st.session_state:
    st.session_state.show_details = {}
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = {}

# 标题
st.markdown("# 📋 发票检查器")
st.markdown('<p class="subtitle">采购发票自动化验证系统</p>', unsafe_allow_html=True)

# 侧边栏 - 上传区域
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
            
            # 取消上传按钮
            if st.button("❌ 取消上传", key="cancel_contract_upload"):
                st.session_state.pop("contract_uploader", None)
                st.rerun()
            
            with st.form("contract_form"):
                st.markdown("##### 请填写合同信息")
                st.caption("⚠️ 请根据合同内容手动填写以下信息")
                
                po_number = st.text_input("采购单号 *", value="", placeholder="例: PO-20240001")
                order_date = st.date_input("订单日期 *", value=datetime.now())
                quantity = st.number_input("数量 *", min_value=0, value=0, step=1, help="请填写合同中的采购数量")
                total_amount = st.number_input("总金额(¥，小写) *", min_value=0.0, value=0.0, step=100.0, help="请填写合同中的总金额（小写数字）")
                
                submitted = st.form_submit_button("✅ 确认添加合同", use_container_width=True)
                
                if submitted:
                    # 验证必填项
                    if not po_number.strip():
                        st.error("请填写采购单号！")
                    elif quantity <= 0:
                        st.error("数量必须大于0！")
                    elif total_amount <= 0:
                        st.error("总金额必须大于0！")
                    else:
                        success, message = add_contract(
                            po_number.strip(), 
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
            
            # 取消上传按钮
            if st.button("❌ 取消上传", key="cancel_invoice_upload"):
                st.session_state.pop("invoice_uploader", None)
                st.rerun()
            
            with st.form("invoice_form"):
                st.markdown("##### 请填写发票信息")
                st.caption("⚠️ 请根据发票内容手动填写以下信息")
                
                contracts_df = get_all_contracts()
                if len(contracts_df) == 0:
                    st.warning("⚠️ 请先添加合同")
                else:
                    contract_options = contracts_df['po_number'].tolist()
                    contract_number = st.selectbox("关联合同号", contract_options)
                    spec_model = st.text_input("规格型号", value="", placeholder="例: SKU-A001")
                    quantity = st.number_input("数量", min_value=0, value=0, step=1)
                    amount = st.number_input("发票金额(¥)", min_value=0.0, value=0.0, step=100.0)
                    
                    submitted = st.form_submit_button("✅ 确认添加发票", use_container_width=True)
                    
                    if submitted:
                        if quantity <= 0:
                            st.error("数量必须大于0！")
                        elif amount <= 0:
                            st.error("金额必须大于0！")
                        else:
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

# 主区域 - 合同列表
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
    
    # 显示合同卡片
    for _, row in filtered_df.iterrows():
        is_complete = abs(row['total_amount'] - row['invoiced_amount']) < 0.01
        status_emoji = "🟢" if is_complete else "🟡"
        status_text = "✓ 金额一致" if is_complete else f"欠 ¥{row['total_amount'] - row['invoiced_amount']:,.2f}"
        
        with st.container():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.3, 1.5, 1, 1, 1.5, 1.2, 0.5])
            
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
            with col7:
                # 删除按钮
                delete_key = f"del_{row['id']}"
                if st.button("🗑️", key=delete_key, help="删除此合同"):
                    st.session_state.confirm_delete[row['id']] = True
            
            # 删除确认
            if st.session_state.confirm_delete.get(row['id'], False):
                confirm_col1, confirm_col2, confirm_col3 = st.columns([4, 1, 1])
                with confirm_col1:
                    st.warning(f"⚠️ 确定要删除合同 **{row['po_number']}** 及其所有关联发票吗？")
                with confirm_col2:
                    if st.button("✅ 确认删除", key=f"confirm_del_{row['id']}", type="primary"):
                        success, message = delete_contract(row['id'])
                        if success:
                            st.session_state.confirm_delete.pop(row['id'], None)
                            st.rerun()
                        else:
                            st.error(message)
                with confirm_col3:
                    if st.button("❌ 取消", key=f"cancel_del_{row['id']}"):
                        st.session_state.confirm_delete.pop(row['id'], None)
                        st.rerun()
            
            # 发票明细展开
            if st.button(f"📋 查看发票明细 ({int(row['invoice_count'])}张)", key=f"btn_{row['id']}", use_container_width=True):
                st.session_state.show_details[row['id']] = not st.session_state.show_details.get(row['id'], False)
            
            if st.session_state.show_details.get(row['id'], False):
                invoices_df = get_contract_invoices(row['id'])
                if len(invoices_df) > 0:
                    st.markdown("##### 发票明细")
                    for idx, inv in invoices_df.iterrows():
                        inv_col1, inv_col2, inv_col3, inv_col4, inv_col5, inv_col6 = st.columns([2, 1, 1, 1, 1, 0.5])
                        with inv_col1:
                            st.text(f"规格: {inv['spec_model']}")
                        with inv_col2:
                            st.text(f"数量: {inv['quantity']}")
                        with inv_col3:
                            st.text(f"¥{inv['amount']:,.2f}")
                        with inv_col4:
                            st.text(inv['created_at'][:10])
                        with inv_col5:
                            st.success("✓ 已验证")
                        with inv_col6:
                            if st.button("🗑️", key=f"del_inv_{inv['id']}", help="删除此发票"):
                                success, msg = delete_invoice(inv['id'])
                                if success:
                                    st.rerun()
                                else:
                                    st.error(msg)
                else:
                    st.info("暂无发票")
            
            st.markdown("---")

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 1rem;'>
    <p>💪 发票检查器 v0.2.0 | Streamlit版本</p>
    <p><a href="https://github.com/fanfanfancheung/invoice-checker" target="_blank">GitHub</a> | 
       <a href="https://github.com/fanfanfancheung/invoice-checker/blob/master/USAGE.md" target="_blank">使用文档</a></p>
</div>
""", unsafe_allow_html=True)
