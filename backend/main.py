from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
import json
import os

app = FastAPI(title="发票检查器 API", version="0.1.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库初始化
DB_PATH = "invoice_checker.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 合同表
    c.execute('''CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT UNIQUE NOT NULL,
        order_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        file_path TEXT,
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
        file_path TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_id) REFERENCES contracts (id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# 数据模型
class ContractCreate(BaseModel):
    po_number: str
    order_date: str
    quantity: int
    total_amount: float

class InvoiceCreate(BaseModel):
    contract_number: str
    spec_model: str
    quantity: int
    amount: float

class ContractStatus(BaseModel):
    id: int
    po_number: str
    order_date: str
    quantity: int
    total_amount: float
    invoiced_amount: float
    invoiced_quantity: int
    status: str  # 'complete' (green) or 'incomplete' (yellow)
    invoice_count: int

# API路由
@app.get("/")
def read_root():
    return {"message": "发票检查器 API v0.1.0", "status": "running"}

@app.post("/upload/contract")
async def upload_contract(file: UploadFile = File(...)):
    """上传合同文件"""
    # TODO: OCR识别
    # 模拟OCR结果
    mock_ocr_result = {
        "po_number": f"PO-2024{len(get_all_contracts()) + 1:03d}",
        "order_date": "2024-01-15",
        "quantity": 100,
        "total_amount": 50000.00
    }
    
    # 保存文件
    file_path = f"uploads/contracts/{mock_ocr_result['po_number']}.pdf"
    os.makedirs("uploads/contracts", exist_ok=True)
    
    # 插入数据库
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO contracts (po_number, order_date, quantity, total_amount, file_path)
                     VALUES (?, ?, ?, ?, ?)''',
                  (mock_ocr_result['po_number'], mock_ocr_result['order_date'], 
                   mock_ocr_result['quantity'], mock_ocr_result['total_amount'], file_path))
        conn.commit()
        contract_id = c.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="采购单号已存在")
    finally:
        conn.close()
    
    return {"message": "合同上传成功", "contract_id": contract_id, **mock_ocr_result}

@app.post("/upload/invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """上传发票文件"""
    # TODO: OCR识别
    # 模拟OCR结果
    mock_ocr_result = {
        "contract_number": "PO-2024001",  # 从发票备注栏识别
        "spec_model": "SKU-A001",
        "quantity": 50,
        "amount": 25000.00
    }
    
    # 查找对应合同
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, po_number, quantity, total_amount FROM contracts WHERE po_number = ?", 
              (mock_ocr_result['contract_number'],))
    contract = c.fetchone()
    
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="未找到对应合同")
    
    contract_id, po_number, contract_qty, contract_amount = contract
    
    # TODO: 验证规格型号
    # 简化版：直接插入
    file_path = f"uploads/invoices/{po_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    os.makedirs("uploads/invoices", exist_ok=True)
    
    c.execute('''INSERT INTO invoices (contract_id, contract_number, spec_model, quantity, amount, file_path, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (contract_id, mock_ocr_result['contract_number'], mock_ocr_result['spec_model'],
               mock_ocr_result['quantity'], mock_ocr_result['amount'], file_path, 'verified'))
    conn.commit()
    conn.close()
    
    return {"message": "发票验证通过", **mock_ocr_result}

@app.get("/contracts", response_model=List[ContractStatus])
def get_all_contracts():
    """获取所有合同及状态"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            c.id, c.po_number, c.order_date, c.quantity, c.total_amount,
            COALESCE(SUM(i.amount), 0) as invoiced_amount,
            COALESCE(SUM(i.quantity), 0) as invoiced_quantity,
            COUNT(i.id) as invoice_count
        FROM contracts c
        LEFT JOIN invoices i ON c.id = i.contract_id
        GROUP BY c.id
        ORDER BY c.order_date ASC
    ''')
    
    results = []
    for row in c.fetchall():
        contract_id, po_number, order_date, qty, total_amt, invoiced_amt, invoiced_qty, inv_count = row
        status = 'complete' if abs(total_amt - invoiced_amt) < 0.01 else 'incomplete'
        results.append({
            "id": contract_id,
            "po_number": po_number,
            "order_date": order_date,
            "quantity": qty,
            "total_amount": total_amt,
            "invoiced_amount": invoiced_amt,
            "invoiced_quantity": invoiced_qty,
            "status": status,
            "invoice_count": inv_count
        })
    
    conn.close()
    return results

@app.get("/contracts/{contract_id}/invoices")
def get_contract_invoices(contract_id: int):
    """获取某个合同的所有发票"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, spec_model, quantity, amount, status, created_at 
                 FROM invoices WHERE contract_id = ?''', (contract_id,))
    invoices = []
    for row in c.fetchall():
        invoices.append({
            "id": row[0],
            "spec_model": row[1],
            "quantity": row[2],
            "amount": row[3],
            "status": row[4],
            "created_at": row[5]
        })
    conn.close()
    return invoices

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
