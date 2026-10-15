import type { Metadata } from 'next'
import { notFound, redirect } from 'next/navigation'
import { getTree, localized } from '@/lib/content'
import { isLocale, t, type Locale } from '@/lib/i18n'
import { ArticleView, CategoryView, CourseView, LessonView } from '@/components/views'

export const dynamic = 'force-dynamic'
type P = { params: Promise<{ locale: string; slug: string[] }> }

async function resolve(params: P['params']) {
  const { locale, slug } = await params
  if (!isLocale(locale)) notFound()
  const n = getTree().byUrl.get('/' + slug.map(decodeURIComponent).join('/'))
  if (!n) notFound()
  return { n, l: locale as Locale }
}

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { n, l } = await resolve(params)
  const m = localized(n, l).meta
  return { title: m.title, description: m.description, openGraph: { title: m.title, description: m.description, images: m.cover ? [m.cover] : undefined } }
}

export default async function Page({ params }: P) {
  const { n, l } = await resolve(params)
  const d = t(l)
  switch (n.kind) {
    case 'category': return <CategoryView n={n} l={l} d={d} />
    case 'course': return <CourseView n={n} l={l} d={d} />
    case 'article': return <ArticleView n={n} l={l} d={d} />
    case 'lesson': return <LessonView n={n} l={l} d={d} />
    case 'module': redirect(`/${l}${n.parent!.url}#module-${n.path.at(-1)}`)
  }
}
