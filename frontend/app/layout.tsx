import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: '发票检查器',
  description: '采购发票自动化验证系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
