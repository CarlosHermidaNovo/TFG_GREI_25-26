import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'

import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'SOS Food - Seguridad Alimentaria y Agricultura',
  description:
    'Dashboard interactivo para monitoreo de seguridad alimentaria, agricultura sostenible y datos de población rural.',
}

export const viewport: Viewport = {
  themeColor: '#16a34a',
}

import { ChatProvider } from "@/context/chat-context"

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es">
      <body className={`${inter.variable} font-sans antialiased`}>
        <ChatProvider>
          {children}
        </ChatProvider>
      </body>
    </html>
  )
}
