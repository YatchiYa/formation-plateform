import Link from 'next/link'
import { Icon } from './Icon'
import type { Card, ThemeCard } from '@/lib/catalog'
import type { Dict, Locale } from '@/lib/i18n'
import type { Format } from '@/lib/content'

export const FORMAT_ORDER: Format[] = ['course', 'article', 'slides', 'video', 'link', 'skill', 'usecase', 'platform']
export const FORMAT_ICON: Record<string, string> = { course: 'book', article: 'paper', slides: 'slides', skill: 'spark', video: 'play', link: 'link', usecase: 'grid', platform: 'monitor', lesson: 'paper', category: 'folder' }
const L = (d: Dict, k: string) => (d as Record<string, string>)[k] ?? k

export function FormatBadge({ format, d }: { format: string; d: Dict }) {
  return (
    <span className={`kind kind-${format}`}>
      <Icon name={FORMAT_ICON[format] ?? 'file'} size={12} /> {L(d, format)}
    </span>
  )
}

function Level({ level, d }: { level: string; d: Dict }) {
  return <span className={`level level-${level}`}><i /><i /><i />{L(d, level)}</span>
}

/** One content item. `compact` is for long lists such as the 160 skills. */
export function ContentCard({ c, d, compact = false, showTrail = true }: { c: Card; d: Dict; compact?: boolean; showTrail?: boolean }) {
  const host = c.link ? safeHost(c.link) : null
  return (
    <li className={`ccard ccard-${c.format} ${compact ? 'ccard-compact' : ''}`}>
      <Link href={c.url} className="ccard-a" data-track={`card-${c.format}`}>
        <div className="ccard-top">
          <FormatBadge format={c.format} d={d} />
          {c.premium && <span className="premium"><Icon name="lock" size={12} /> {d.premium}</span>}
        </div>
        <h3 className="ccard-title">{c.title}</h3>
        {c.description && <p className="ccard-desc">{c.description}</p>}
        <div className="ccard-meta">
          {c.level && <Level level={c.level} d={d} />}
          {c.format === 'course' && c.lessons ? <span><Icon name="book" size={13} /> {c.lessons} {d.lessons}</span> : null}
          {host ? <span><Icon name={host.includes('github') ? 'github' : 'link'} size={13} /> {host}</span>
            : c.format === 'video' ? <span><Icon name="play" size={12} /> {d.watch}</span>
            : !['skill', 'usecase', 'platform'].includes(c.format) && <span><Icon name="clock" size={13} /> {c.duration ?? `${c.minutes} ${d.minRead}`}</span>}
        </div>
        {showTrail && c.trail.length > 0 && <p className="ccard-trail">{c.trail.map((t) => t.title).join(' › ')}</p>}
      </Link>
    </li>
  )
}

const safeHost = (u: string) => { try { return new URL(u).host.replace(/^www\./, '') } catch { return null } }

/** A topic, shown with how much of each format it holds. */
export function ThemeTile({ t, d, href }: { t: ThemeCard; d: Dict; href?: string }) {
  return (
    <li className="theme-tile">
      <Link href={href ?? t.url} data-track="theme-tile">
        <span className="theme-tile-icon" aria-hidden="true">{t.icon ?? '📁'}</span>
        <span className="theme-tile-title">{t.title}</span>
        {t.description && <span className="theme-tile-desc">{t.description}</span>}
        <span className="theme-tile-formats">
          {FORMAT_ORDER.filter((f) => t.formats[f]).map((f) => (
            <span key={f} className={`fcount fcount-${f}`}><Icon name={FORMAT_ICON[f]} size={12} /> {countLabel(d, f, t.formats[f]!)}</span>
          ))}
        </span>
        {t.children.length > 0 && <span className="theme-tile-subs">{t.children.map((c) => c.title).join(' · ')}</span>}
      </Link>
    </li>
  )
}

export function FormatTiles({ counts, d, hrefFor }: { counts: Partial<Record<Format, number>>; d: Dict; hrefFor: (f: Format) => string }) {
  return (
    <ul className="format-tiles">
      {FORMAT_ORDER.filter((f) => counts[f]).map((f) => (
        <li key={f} className={`ftile ftile-${f}`}>
          <Link href={hrefFor(f)} data-track={`format-${f}`}>
            <span className="ftile-icon"><Icon name={FORMAT_ICON[f]} size={20} /></span>
            <span className="ftile-n">{counts[f]}</span>
            <span className="ftile-label">{L(d, 'pl_' + f)}</span>
            <span className="ftile-desc">{L(d, 'desc_' + f)}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

export const plural = (d: Dict, f: string) => L(d, 'pl_' + f)
/** "1 vidéo", "5 vidéos" */
export const countLabel = (d: Dict, f: string, n: number) => `${n} ${(n === 1 ? L(d, f === 'course' ? 'course' : f === 'slides' ? 'slides' : f) : L(d, 'pl_' + f)).toLowerCase()}`
export type { Locale }
