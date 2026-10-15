import { courseOf, countItems, crumbs, formatOf, getTree, items, localized, plain, readingMinutes, type Format, type Node } from './content'
import type { Locale } from './i18n'

export interface Crumb { url: string; title: string; icon?: string }
export interface Card {
  url: string
  kind: Node['kind']
  format: Format | 'category' | 'module' | 'lesson'
  slides: boolean
  title: string
  description?: string
  icon?: string
  cover?: string
  tags: string[]
  level?: string
  duration?: string
  date?: string
  premium: boolean
  lessons?: number
  minutes: number
  section?: string
  /** Theme path from the top: [level 1, level 2, ...] */
  trail: Crumb[]
  video?: string
  link?: string
  platforms: string[]
  usecases: string[]
}

const crumb = (n: Node, l: Locale): Crumb => {
  const m = localized(n, l).meta
  return { url: `/${l}${n.url}`, title: m.title, icon: m.icon }
}

/** Flat, serializable view of a node for listings and search. */
export function card(n: Node, l: Locale): Card {
  const d = localized(n, l)
  const trail = crumbs(n).filter((c) => c.kind === 'category' && c.path.length).map((c) => crumb(c, l))
  const course = n.kind === 'lesson' ? courseOf(n) : undefined
  const body = n.kind === 'course' ? n.lessons!.map((x) => localized(x, l).body).join('\n') : d.body
  return {
    url: `/${l}${n.url}`,
    kind: n.kind,
    format: formatOf(n, d.meta),
    slides: d.meta.slides,
    title: d.meta.title,
    description: d.meta.description,
    icon: d.meta.icon,
    cover: d.meta.cover,
    tags: d.meta.tags,
    level: d.meta.level,
    duration: d.meta.duration,
    date: d.meta.updated ?? d.meta.date,
    premium: d.meta.access === 'premium',
    lessons: n.lessons?.length,
    minutes: readingMinutes(body),
    // Closest context: the course for a lesson, else the nearest theme.
    section: course ? localized(course, l).meta.title : trail.at(-1)?.title,
    trail,
    video: d.meta.video,
    link: d.meta.link,
    platforms: d.meta.platforms,
    usecases: d.meta.usecases,
  }
}

export function searchIndex(l: Locale) {
  return getTree()
    .all.filter((n) => n.kind !== 'module' && n.path.length)
    .map((n) => {
      const body = localized(n, l).body
      const headings = [...body.matchAll(/^#{2,3}\s+(.+)$/gm)].map((m) => m[1]).join(' · ')
      return { ...card(n, l), headings, text: plain(body).slice(0, 1500) }
    })
}

export interface ThemeCard extends Crumb {
  description?: string
  count: number
  formats: Partial<Record<Format, number>>
  children: ThemeCard[]
}

/** Theme hierarchy with per-format counts, for browsing by cards. */
export function themes(l: Locale, n: Node = getTree().root): ThemeCard[] {
  return n.children
    .filter((c) => c.kind === 'category')
    .map((c) => {
      const formats: Partial<Record<Format, number>> = {}
      const walk = (x: Node) => {
        if (x.kind === 'course' || x.kind === 'article') {
          const f = formatOf(x, localized(x, l).meta) as Format
          formats[f] = (formats[f] ?? 0) + 1
        }
        x.children.forEach(walk)
      }
      walk(c)
      return { ...crumb(c, l), description: localized(c, l).meta.description, count: countItems(c), formats, children: themes(l, c) }
    })
}

/** Items to show first to someone new: beginner level, then courses. */
export function starters(l: Locale, max = 4) {
  const rank = (c: Card) => (c.level === 'beginner' ? 0 : c.level === 'intermediate' ? 1 : c.level === 'advanced' ? 2 : 3) * 2 + (c.format === 'course' ? 0 : 1)
  return items(getTree())
    .map((n) => card(n, l))
    .filter((c) => c.format === 'course' || c.format === 'article' || c.format === 'video')
    .sort((a, b) => rank(a) - rank(b))
    .slice(0, max)
}
