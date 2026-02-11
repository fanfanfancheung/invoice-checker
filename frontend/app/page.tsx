'use client'

import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Contract {
  id: number
  po_number: string
  order_date: string
  quantity: number
  total_amount: number
  invoiced_amount: number
  invoiced_quantity: number
  status: 'complete' | 'incomplete'
  invoice_count: number
}

interface Invoice {
  id: number
  spec_model: string
  quantity: number
  amount: number
  status: string
  created_at: string
}

export default function Home() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [expandedContract, setExpandedContract] = useState<number | null>(null)
  const [contractInvoices, setContractInvoices] = useState<{ [key: number]: Invoice[] }>({})
  const [uploadType, setUploadType] = useState<'contract' | 'invoice'>('contract')
  const [uploading, setUploading] = useState(false)

  // 加载合同列表
  const loadContracts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/contracts`)
      setContracts(res.data)
    } catch (error) {
      console.error('加载合同失败:', error)
    }
  }

  // 加载某个合同的发票
  const loadContractInvoices = async (contractId: number) => {
    try {
      const res = await axios.get(`${API_BASE}/contracts/${contractId}/invoices`)
      setContractInvoices(prev => ({ ...prev, [contractId]: res.data }))
    } catch (error) {
      console.error('加载发票失败:', error)
    }
  }

  useEffect(() => {
    loadContracts()
  }, [])

  // 文件上传
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    
    setUploading(true)
    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    try {
      const endpoint = uploadType === 'contract' ? '/upload/contract' : '/upload/invoice'
      const res = await axios.post(`${API_BASE}${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      alert(`${uploadType === 'contract' ? '合同' : '发票'}上传成功！`)
      loadContracts()
    } catch (error: any) {
      alert(`上传失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
    }
  }, [uploadType])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg']
    },
    maxFiles: 1
  })

  // 展开/折叠合同
  const toggleContract = (contractId: number) => {
    if (expandedContract === contractId) {
      setExpandedContract(null)
    } else {
      setExpandedContract(contractId)
      if (!contractInvoices[contractId]) {
        loadContractInvoices(contractId)
      }
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* 标题 */}
        <h1 className="text-4xl font-bold text-gray-800 mb-2">📋 发票检查器</h1>
        <p className="text-gray-600 mb-8">采购发票自动化验证系统</p>

        {/* 上传区域 */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setUploadType('contract')}
              className={`px-6 py-2 rounded-lg font-semibold transition ${
                uploadType === 'contract'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              📄 上传合同
            </button>
            <button
              onClick={() => setUploadType('invoice')}
              className={`px-6 py-2 rounded-lg font-semibold transition ${
                uploadType === 'invoice'
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              🧾 上传发票
            </button>
          </div>

          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
              isDragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <p className="text-gray-600">上传中...</p>
            ) : isDragActive ? (
              <p className="text-blue-600 text-lg">松开鼠标上传文件</p>
            ) : (
              <>
                <p className="text-gray-600 text-lg mb-2">
                  📁 将{uploadType === 'contract' ? '合同' : '发票'}拖到这里
                </p>
                <p className="text-gray-400 text-sm">或点击选择文件（支持 PDF、图片）</p>
              </>
            )}
          </div>
        </div>

        {/* 合同列表 */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">合同列表</h2>
          
          {contracts.length === 0 ? (
            <p className="text-gray-400 text-center py-8">暂无合同数据</p>
          ) : (
            <div className="space-y-3">
              {contracts.map((contract) => (
                <div key={contract.id} className="border rounded-lg overflow-hidden">
                  {/* 合同主行 */}
                  <div
                    onClick={() => toggleContract(contract.id)}
                    className={`p-4 cursor-pointer transition flex items-center justify-between ${
                      contract.status === 'complete'
                        ? 'bg-green-50 hover:bg-green-100'
                        : 'bg-yellow-50 hover:bg-yellow-100'
                    }`}
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`w-3 h-3 rounded-full ${
                        contract.status === 'complete' ? 'bg-green-500' : 'bg-yellow-500'
                      }`} />
                      <div className="font-mono font-bold text-lg">{contract.po_number}</div>
                      <div className="text-gray-600">{contract.order_date}</div>
                      <div className="text-gray-600">数量: {contract.quantity}</div>
                      <div className="font-semibold">
                        ¥{contract.total_amount.toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        contract.status === 'complete'
                          ? 'bg-green-200 text-green-800'
                          : 'bg-yellow-200 text-yellow-800'
                      }`}>
                        {contract.status === 'complete'
                          ? '✓ 金额一致'
                          : `欠 ¥${(contract.total_amount - contract.invoiced_amount).toLocaleString()}`
                        }
                      </div>
                      <div className="text-gray-500">
                        {contract.invoice_count} 张发票
                      </div>
                      <svg
                        className={`w-5 h-5 transition-transform ${
                          expandedContract === contract.id ? 'rotate-180' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>

                  {/* 发票明细 */}
                  {expandedContract === contract.id && (
                    <div className="bg-gray-50 p-4 border-t">
                      <h3 className="font-semibold text-gray-700 mb-2">发票明细</h3>
                      {contractInvoices[contract.id]?.length > 0 ? (
                        <div className="space-y-2">
                          {contractInvoices[contract.id].map((invoice) => (
                            <div key={invoice.id} className="bg-white p-3 rounded border flex justify-between">
                              <div className="flex gap-4">
                                <span className="text-gray-600">规格: {invoice.spec_model}</span>
                                <span className="text-gray-600">数量: {invoice.quantity}</span>
                                <span className="font-semibold">¥{invoice.amount.toLocaleString()}</span>
                              </div>
                              <span className="text-green-600">✓ 已验证</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-400">暂无发票</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
