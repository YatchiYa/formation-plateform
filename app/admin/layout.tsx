import type { Metadata } from 'next'
import Link from 'next/link'
import '../globals.css'
import { fontVars, themeScript } from '../fonts'
import { ThemeToggle } from '@/components/client'

export const metadata: Metadata = { title: 'Admin · Atelier', robots: { index: false } }

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" dir="ltr" className={fontVars} suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body className="admin">
        <header className="site-header">
          <div className="bar">
            <Link href="/admin" className="brand"><span>Atelier</span><span className="admin-tag">Monitoring</span></Link>
            <nav className="main-nav">
              <Link href="/admin">Vue d’ensemble</Link>
              <Link href="/admin/heatmap">Carte des clics</Link>
              <Link href="/">Voir le site</Link>
            </nav>
            <div className="bar-tools"><ThemeToggle label="Thème" /></div>
          </div>
        </header>
        <main id="main" className="admin-main">{children}</main>
      </body>
    </html>
  )
}
