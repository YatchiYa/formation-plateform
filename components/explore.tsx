'use client'
import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Icon } from './Icon'
import { score, loadIndex } from './client'
import { fetchProgress, type ProgressItem } from './reader'
import { ContentCard, FORMAT_ICON, FORMAT_ORDER, FormatTiles, ThemeTile, countLabel, plural } from './cards'
import type { Card, ThemeCard } from '@/lib/catalog'
import type { Format } from '@/lib/content'
import type { Dict, Locale } from '@/lib/i18n'

type Hit = Card & { text: string; headings?: string }
const L = (d: Dict, k: string) => (d as Record<string, string>)[k] ?? k

function findTheme(ts: ThemeCard[], url: string): ThemeCard[] | null {
  for (const t of ts) {
    if (t.url === url) return [t]
    const sub = findTheme(t.children, url)
    if (sub) return [t, ...sub]
  }
  return null
}

const PREVIEW = 6

export function Explore({ cards, themes, d, l }: { cards: Hit[]; themes: ThemeCard[]; d: Dict; l: Locale }) {
  const sp = useSearchParams()
  const [q, setQ] = useState(sp.get('q') ?? '')
  const [format, setFormat] = useState<string>(sp.get('format') ?? sp.get('type') ?? '')
  const [level, setLevel] = useState(sp.get('level') ?? '')
  const [tag, setTag] = useState(sp.get('tag') ?? '')
  const [uc, setUc] = useState(sp.get('usecase') ?? '')
  const [pf, setPf] = useState(sp.get('platform') ?? '')
  const [theme, setTheme] = useState(sp.get('theme') ? `/${l}/${sp.get('theme')}` : '')
  const [showTags, setShowTags] = useState(!!sp.get('tag'))
  const [limit, setLimit] = useState(24)

  // Keep the URL shareable (and the back button meaningful) as filters change.
  useEffect(() => {
    const u = new URLSearchParams()
    if (q) u.set('q', q)
    if (theme) u.set('theme', theme.slice(l.length + 2))
    if (format) u.set('format', format)
    if (level) u.set('level', level)
    if (tag) u.set('tag', tag)
    if (uc) u.set('usecase', uc)
    if (pf) u.set('platform', pf)
    history.replaceState(null, '', `${location.pathname}${u.size ? '?' + u : ''}`)
  }, [q, theme, format, level, tag, uc, pf, l])
  useEffect(() => setLimit(24), [q, theme, format, level, tag, uc, pf])
  const slugOf = (c: Hit) => c.url.split('/').pop()!
  const usecaseCards = useMemo(() => cards.filter((c) => c.format === 'usecase'), [cards])
  const platformCards = useMemo(() => cards.filter((c) => c.format === 'platform'), [cards])

  const themePath = theme ? findTheme(themes, theme) : null
  const current = themePath?.at(-1)
  const subThemes = current ? current.children : []

  // Everything but the format filter: used both for results and for the per-format counts.
  const scoped = useMemo(() => {
    let r = cards.filter((c) => (!theme || c.trail.some((t) => t.url === theme)) && (!level || c.level === level) && (!tag || c.tags.includes(tag))
      && (!uc || c.usecases.includes(uc) || (c.format === 'usecase' && slugOf(c) === uc))
      && (!pf || c.platforms.includes(pf) || (c.format === 'platform' && slugOf(c) === pf)))
    if (q.trim()) r = r.map((c) => [c, score(c, q)] as const).filter(([, s]) => s > 0).sort((a, b) => b[1] - a[1]).map(([c]) => c)
    return r
  }, [cards, q, theme, level, tag, uc, pf])
  const counts = useMemo(() => {
    const m: Partial<Record<Format, number>> = {}
    scoped.forEach((c) => { m[c.format as Format] = (m[c.format as Format] ?? 0) + 1 })
    return m
  }, [scoped])
  const results = format ? scoped.filter((c) => c.format === format) : scoped

  const tags = useMemo(() => {
    const m = new Map<string, number>()
    scoped.forEach((c) => c.tags.forEach((t) => m.set(t, (m.get(t) ?? 0) + 1)))
    return [...m].sort((a, b) => b[1] - a[1]).slice(0, 30)
  }, [scoped])

  const landing = !q && !format && !theme && !level && !tag && !uc && !pf
  const reset = () => { setQ(''); setFormat(''); setLevel(''); setTag(''); setTheme(''); setUc(''); setPf('') }

  const section = (f: Format, list: Hit[]) => {
    if (!list.length) return null
    const shown = list.slice(0, f === 'skill' ? PREVIEW + 2 : PREVIEW)
    return (
      <section key={f} className="fsection">
        <div className="section-head">
          <h2 className="section-title"><span className={`ficon ficon-${f}`}><Icon name={FORMAT_ICON[f]} size={16} /></span>{plural(d, f)} <small>{list.length}</small></h2>
          {list.length > shown.length && <button className="text-link" onClick={() => setFormat(f)} data-track={`see-all-${f}`}>{d.seeAll} ({list.length}) <Icon name="right" size={14} className="flip-rtl" /></button>}
        </div>
        <ul className={`card-grid ${f === 'skill' ? 'card-grid-dense' : ''}`}>
          {shown.map((c) => <ContentCard key={c.url} c={c} d={d} compact={f === 'skill'} />)}
        </ul>
      </section>
    )
  }

  return (
    <div className="explore">
      <div className="explore-hero">
        <h1 className="display">{d.whatToLearn}</h1>
        <div className="explore-search">
          <Icon name="search" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={d.searchPlaceholder} aria-label={d.search} data-track="explore-search" />
          {q && <button className="icon-btn" onClick={() => setQ('')} aria-label={d.clearFilters}><Icon name="x" size={16} /></button>}
        </div>
      </div>

      {/* Entry by need: for someone who doesn't know the vocabulary yet */}
      {usecaseCards.length > 0 && (
        <nav className="intent-row" aria-label={d.pl_usecase}>
          <span className="intent-label">{d.iWantTo}</span>
          {usecaseCards.map((c) => (
            <button key={c.url} className={`chip chip-intent ${uc === slugOf(c) ? 'on' : ''}`} onClick={() => setUc(uc === slugOf(c) ? '' : slugOf(c))} data-track="usecase-chip">
              {c.icon} {c.title}
            </button>
          ))}
        </nav>
      )}

      {/* Level 1: topics */}
      <nav className="theme-chips" aria-label={d.browseThemes}>
        <button className={`chip chip-lg ${!theme ? 'on' : ''}`} onClick={() => setTheme('')} data-track="theme-all">{d.allThemes}</button>
        {themes.map((t) => (
          <button key={t.url} className={`chip chip-lg ${themePath?.[0]?.url === t.url ? 'on' : ''}`} onClick={() => setTheme(themePath?.[0]?.url === t.url && themePath.length === 1 ? '' : t.url)} data-track="theme-chip">
            <span aria-hidden="true">{t.icon}</span> {t.title}
          </button>
        ))}
      </nav>

      {themePath && themePath.length > 0 && (
        <div className="theme-focus">
          <nav className="crumbs" aria-label="breadcrumb">
            <button className="crumb-btn" onClick={() => setTheme('')}>{d.allThemes}</button>
            {themePath.map((t) => (
              <span key={t.url}><span className="sep" aria-hidden="true">/</span><button className="crumb-btn" onClick={() => setTheme(t.url)}>{t.icon} {t.title}</button></span>
            ))}
          </nav>
          {current?.description && <p className="lede">{current.description}</p>}
          {subThemes.length > 0 && (
            <ul className="theme-tiles theme-tiles-sm">
              {subThemes.map((t) => (
                <li key={t.url} className="theme-tile">
                  <button onClick={() => setTheme(t.url)} data-track="subtheme-tile">
                    <span className="theme-tile-icon" aria-hidden="true">{t.icon ?? '📁'}</span>
                    <span className="theme-tile-title">{t.title}</span>
                    <span className="theme-tile-formats">
                      {FORMAT_ORDER.filter((f) => t.formats[f]).map((f) => <span key={f} className={`fcount fcount-${f}`}>{countLabel(d, f, t.formats[f]!)}</span>)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Format + level filters */}
      <div className="filter-bar">
        <div className="segmented" role="group" aria-label={d.type}>
          <button className={!format ? 'on' : ''} onClick={() => setFormat('')} data-track="format-all">{d.all} <small>{scoped.length}</small></button>
          {FORMAT_ORDER.filter((f) => counts[f] || format === f).map((f) => (
            <button key={f} className={format === f ? 'on' : ''} onClick={() => setFormat(format === f ? '' : f)} data-track={`format-${f}`}>
              <Icon name={FORMAT_ICON[f]} size={14} /> {plural(d, f)} <small>{counts[f] ?? 0}</small>
            </button>
          ))}
        </div>
        <div className="filter-group" role="group" aria-label={d.level}>
          {['beginner', 'intermediate', 'advanced', 'expert'].map((k) => (
            <button key={k} type="button" className={`chip ${level === k ? 'on' : ''}`} aria-pressed={level === k} onClick={() => setLevel(level === k ? '' : k)} data-track={`level-${k}`}>
              <span className={`level level-${k}`}><i /><i /><i /></span>{L(d, k)}
            </button>
          ))}
          <button type="button" className={`chip ${showTags ? 'on' : ''}`} onClick={() => setShowTags(!showTags)} aria-expanded={showTags} data-track="more-filters">#{' '}{d.tags}</button>
          {platformCards.map((c) => (
            <button key={c.url} type="button" className={`chip ${pf === slugOf(c) ? 'on' : ''}`} aria-pressed={pf === slugOf(c)} onClick={() => setPf(pf === slugOf(c) ? '' : slugOf(c))} data-track="platform-chip">
              <Icon name="monitor" size={13} /> {c.title}
            </button>
          ))}
          {!landing && <button type="button" className="chip chip-clear" onClick={reset} data-track="clear-filters"><Icon name="x" size={13} /> {d.clearFilters}</button>}
        </div>
        {showTags && (
          <div className="filter-group tags-group" role="group" aria-label={d.tags}>
            {tags.map(([t, n]) => (
              <button key={t} type="button" className={`chip ${tag === t ? 'on' : ''}`} aria-pressed={tag === t} onClick={() => setTag(tag === t ? '' : t)} data-track="filter-tag">#{t} <small>{n}</small></button>
            ))}
          </div>
        )}
      </div>

      {landing ? (
        <>
          <section className="fsection">
            <h2 className="section-title">{d.browseThemes}</h2>
            <ul className="theme-tiles">
              {themes.map((t) => <ThemeTile key={t.url} t={t} d={d} href={`/${l}/explore?theme=${t.url.slice(l.length + 2)}`} />)}
            </ul>
          </section>
          <section className="fsection">
            <h2 className="section-title">{d.browseFormats}</h2>
            <FormatTiles counts={counts} d={d} hrefFor={(f) => `/${l}/explore?format=${f}`} />
          </section>
          {FORMAT_ORDER.map((f) => section(f, cards.filter((c) => c.format === f)))}
        </>
      ) : (
        <>
          <p className="result-count" aria-live="polite">{results.length} {d.items}</p>
          {!results.length && <div className="empty-state"><p>{d.noResults}</p><button className="btn btn-ghost" onClick={reset}>{d.clearFilters}</button></div>}
          {format ? (
            <>
              <ul className={`card-grid ${format === 'skill' ? 'card-grid-dense' : ''}`}>
                {results.slice(0, limit).map((c) => <ContentCard key={c.url} c={c} d={d} compact={format === 'skill'} />)}
              </ul>
              {results.length > limit && <div className="more-row"><button className="btn btn-ghost" onClick={() => setLimit(limit + 48)} data-track="show-more">{d.showMore} ({results.length - limit})</button></div>}
            </>
          ) : (
            FORMAT_ORDER.map((f) => section(f, results.filter((c) => c.format === f)))
          )}
        </>
      )}
    </div>
  )
}

export function MyLearning({ d, l }: { d: Dict; l: Locale }) {
  const [p, setP] = useState<ProgressItem[] | null>(null)
  const [idx, setIdx] = useState<Map<string, Hit>>(new Map())
  useEffect(() => {
    fetchProgress().then(setP)
    loadIndex(l).then((all: Hit[]) => setIdx(new Map(all.map((h) => [h.url.slice(l.length + 1), h]))))
  }, [l])
  if (!p) return <p className="empty">…</p>
  if (!p.length) return <div className="empty-state"><p>{d.emptyLearning}</p><Link className="btn btn-primary" href={`/${l}/explore`}>{d.heroCta}</Link></div>
  const courses = [...new Set(p.map((x) => x.course).filter(Boolean) as string[])]
  return (
    <>
      {courses.length > 0 && (
        <section className="block">
          <h2 className="block-title">{d.continueLearning}</h2>
          <ul className="item-list">
            {courses.map((c) => {
              const h = idx.get(c)
              if (!h) return null
              const done = p.filter((x) => x.course === c && x.status === 'completed').length
              const last = p.find((x) => x.course === c)!
              const pct = h.lessons ? Math.round((done / h.lessons) * 100) : 0
              return (
                <li key={c} className="item-row">
                  <Link className="item-link" href={`/${l}${last.item}`} data-track="me-resume">
                    <div className="item-head"><span className="kind kind-course">{d.course}</span></div>
                    <h3 className="item-title">{h.title}</h3>
                    <div className="meter"><span style={{ width: `${pct}%` }} /></div>
                    <p className="meter-label">{d.progress} {pct}% · {done}/{h.lessons} — {d.resumeCourse}: {idx.get(last.item)?.title}</p>
                  </Link>
                </li>
              )
            })}
          </ul>
        </section>
      )}
      <section className="block">
        <h2 className="block-title">{d.history}</h2>
        <ol className="history">
          {p.map((x) => {
            const h = idx.get(x.item)
            if (!h) return null
            return (
              <li key={x.item}>
                <Link href={h.url}>{h.title}</Link>
                {h.section && <span className="item-section">{h.section}</span>}
                <span className={`status ${x.status}`}>{x.status === 'completed' ? <><Icon name="check" size={14} /> {d.completed}</> : `${x.pct}%`}</span>
                <time>{new Date(x.updated).toLocaleString(l)}</time>
              </li>
            )
          })}
        </ol>
      </section>
    </>
  )
}
