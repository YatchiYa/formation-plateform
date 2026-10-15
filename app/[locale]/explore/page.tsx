import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import { searchIndex, themes } from '@/lib/catalog'
import { isLocale, t } from '@/lib/i18n'
import { Explore } from '@/components/explore'

export const dynamic = 'force-dynamic'

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  return { title: isLocale(locale) ? t(locale).explore : 'Explore' }
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!isLocale(locale)) notFound()
  const d = t(locale)
  const cards = searchIndex(locale).filter((c) => c.kind === 'course' || c.kind === 'article')
  return (
    <div className="page">
      <Suspense><Explore cards={cards} themes={themes(locale)} d={d} l={locale} /></Suspense>
    </div>
  )
}
