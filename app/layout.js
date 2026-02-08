import './globals.css'

export const metadata = {
  title: 'مولد الثمبنيل - Thumbnail Generator',
  description: 'Generate emotional YouTube thumbnails with AI',
}

export default function RootLayout({ children }) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  )
}
