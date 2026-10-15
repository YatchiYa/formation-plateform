import { notFound } from 'next/navigation'
import { isLocale, t } from '@/lib/i18n'
import { MyLearning } from '@/components/explore'

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  return { title: isLocale(locale) ? t(locale).myLearning : 'Me' }
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!isLocale(locale)) notFound()
  const d = t(locale)
  return (
    <div className="page">
      <header className="page-head"><h1 className="display">{d.myLearning}</h1></header>
      <MyLearning d={d} l={locale} />
    </div>
  )
}
