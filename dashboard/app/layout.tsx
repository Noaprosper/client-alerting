import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Scaleway Client Alerting Dashboard',
  description: 'Monitor active incident alerts across all clients',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}