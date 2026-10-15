import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import '../globals.css'
import 'katex/dist/katex.min.css'
import { fontVars, themeScript } from '../fonts'
import { dirOf, isLocale, locales, t } from '@/lib/i18n'
import { LocaleSwitcher, SearchPalette, ThemeToggle, Tracker } from '@/components/client'

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }))
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params
  const d = t(isLocale(locale) ? locale : 'fr')
  return {
    title: { default: `${d.siteName} — ${d.tagline}`, template: `%s · ${d.siteName}` },
    description: d.heroText,
    metadataBase: new URL(process.env.SITE_URL || 'http://localhost:3000'),
    alternates: { languages: Object.fromEntries(locales.map((l) => [l, `/${l}`])) },
  }
}

export default async function LocaleLayout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!isLocale(locale)) notFound()
  const d = t(locale)
  return (
    <html lang={locale} dir={dirOf(locale)} className={fontVars} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <header className="site-header">
          <div className="bar">
            <Link href={`/${locale}`} className="brand" data-track="brand">
              <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><rect x="3" y="7" width="26" height="20" rx="3" fill="var(--ink)" /><path d="M3 10a3 3 0 0 1 3-3h7l3 3" fill="var(--mark)" /><path d="M9 21l4-8 3 5 2-3 4 6" stroke="var(--paper)" strokeWidth="2" fill="none" strokeLinejoin="round" /></svg>
              <span>{d.siteName}</span>
            </Link>
            <nav className="main-nav" aria-label="main">
              <Link href={`/${locale}/explore`} data-track="nav-explore">{d.explore}</Link>
              <Link href={`/${locale}/me`} data-track="nav-me">{d.myLearning}</Link>
            </nav>
            <div className="bar-tools">
              <SearchPalette locale={locale} d={d} />
              <LocaleSwitcher locale={locale} label={d.language} />
              <ThemeToggle label={d.theme} />
            </div>
          </div>
        </header>
        <main id="main">{children}</main>
        <footer className="site-footer">
          <div className="bar">
            <span>{d.siteName} — {d.footer}</span>
            <span>© {new Date().getFullYear()}</span>
          </div>
        </footer>
        <Tracker locale={locale} />
      </body>
    </html>
  )
}
