'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Icon } from './Icon'
import { locales, localeNames, type Locale, type Dict } from '@/lib/i18n'
import type { Card } from '@/lib/catalog'

/* ---------------- Theme ---------------- */
export function ThemeToggle({ label }: { label: string }) {
  const [mode, setMode] = useState<'light' | 'dark' | null>(null)
  useEffect(() => setMode(document.documentElement.dataset.theme as 'light' | 'dark'), [])
  const flip = () => {
    const next = mode === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = next
    try { localStorage.setItem('atl_theme', next) } catch {}
    setMode(next)
  }
  return (
    <button className="icon-btn" onClick={flip} aria-label={label} title={label} data-track="theme-toggle">
      <Icon name={mode === 'dark' ? 'sun' : 'moon'} />
    </button>
  )
}

/* ---------------- Locale ---------------- */
export function LocaleSwitcher({ locale, label }: { locale: Locale; label: string }) {
  const pathname = usePathname()
  const router = useRouter()
  return (
    <label className="locale-switch" title={label}>
      <Icon name="globe" />
      <select
        aria-label={label}
        value={locale}
        data-track="locale-switch"
        onChange={(e) => {
          const l = e.target.value
          document.cookie = `atl_locale=${l};path=/;max-age=31536000;samesite=lax`
          router.push(pathname.replace(/^\/[a-z]{2}(?=\/|$)/, '/' + l) + location.hash)
        }}
      >
        {locales.map((l) => <option key={l} value={l}>{localeNames[l]}</option>)}
      </select>
    </label>
  )
}

/* ---------------- Search (Ctrl/Cmd+K) ---------------- */
type Hit = Card & { text: string; headings?: string }
let indexCache: { l: string; data: Promise<Hit[]> } | null = null
export const loadIndex = (l: string) => {
  if (!indexCache || indexCache.l !== l) indexCache = { l, data: fetch(`/api/search?locale=${l}`).then((r) => r.json()) }
  return indexCache.data
}
const norm = (s: string) => s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()

// ponytail: linear scan with naive scoring; fine for a few thousand pages, swap for MiniSearch beyond that.
export function score(h: Hit, q: string) {
  const terms = norm(q).split(/\s+/).filter(Boolean)
  let s = 0
  for (const t of terms) {
    const title = norm(h.title), tags = h.tags.join(' '), desc = norm(h.description ?? ''), heads = norm(h.headings ?? ''), text = norm(h.text)
    const ts = (title.startsWith(t) ? 12 : title.includes(t) ? 8 : 0) + (tags.includes(t) ? 5 : 0) + (heads.includes(t) ? 4 : 0) + (desc.includes(t) ? 3 : 0) + (text.includes(t) ? 1 : 0)
    if (!ts) return 0
    s += ts
  }
  return s + (h.kind === 'course' ? 1 : 0)
}

export function excerpt(text: string, q: string) {
  const t = norm(q).split(/\s+/)[0]
  const i = t ? norm(text).indexOf(t) : -1
  if (i < 0) return ''
  return (i > 40 ? '…' : '') + text.slice(Math.max(0, i - 40), i + 110) + '…'
}

export function SearchPalette({ locale, d }: { locale: Locale; d: Dict }) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const [data, setData] = useState<Hit[]>([])
  const [sel, setSel] = useState(0)
  const ref = useRef<HTMLDialogElement>(null)
  const router = useRouter()

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setOpen(true) }
      if (e.key === '/' && !/input|textarea|select/i.test((e.target as HTMLElement).tagName)) { e.preventDefault(); setOpen(true) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  useEffect(() => {
    if (!open) return
    ref.current?.showModal()
    loadIndex(locale).then(setData)
  }, [open, locale])

  const hits = useMemo(() => {
    if (!q.trim()) return data.filter((h) => h.format === 'course' || h.format === 'article' || h.format === 'video').slice(0, 8)
    return data.map((h) => [h, score(h, q)] as const).filter(([, s]) => s > 0).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([h]) => h)
  }, [data, q])

  const close = () => { ref.current?.close(); setOpen(false); setQ(''); setSel(0) }
  const go = (h: Hit) => { close(); router.push(h.url) }

  return (
    <>
      <button className="search-trigger" onClick={() => setOpen(true)} data-track="search-open">
        <Icon name="search" size={16} />
        <span>{d.search}</span>
        <kbd>Ctrl K</kbd>
      </button>
      {open && (
        <dialog ref={ref} className="palette" onClose={close} onClick={(e) => e.target === ref.current && close()}>
          <div className="palette-box">
            <div className="palette-input">
              <Icon name="search" />
              <input
                autoFocus
                value={q}
                placeholder={d.searchPlaceholder}
                aria-label={d.search}
                onChange={(e) => { setQ(e.target.value); setSel(0) }}
                onKeyDown={(e) => {
                  if (e.key === 'ArrowDown') { e.preventDefault(); setSel((s) => Math.min(s + 1, hits.length - 1)) }
                  if (e.key === 'ArrowUp') { e.preventDefault(); setSel((s) => Math.max(s - 1, 0)) }
                  if (e.key === 'Enter' && hits[sel]) go(hits[sel])
                }}
              />
              <kbd>Esc</kbd>
            </div>
            <ul className="palette-list" role="listbox">
              {hits.map((h, i) => (
                <li key={h.url} role="option" aria-selected={i === sel}>
                  <a href={h.url} onClick={(e) => { e.preventDefault(); go(h) }} onMouseEnter={() => setSel(i)} data-track="search-result">
                    <span className={`kind kind-${h.format}`}>{(d as Record<string, string>)[h.format]}</span>
                    <span className="palette-title">{h.title}</span>
                    {h.section && <span className="palette-section">{h.section}</span>}
                    {q && excerpt(h.text, q) && <span className="palette-excerpt">{excerpt(h.text, q)}</span>}
                  </a>
                </li>
              ))}
              {!hits.length && <li className="palette-empty">{d.noResults}</li>}
            </ul>
          </div>
        </dialog>
      )}
    </>
  )
}

/* ---------------- Analytics ---------------- */
type Ev = Record<string, unknown>
const queue: Ev[] = []
const flush = (beacon = false) => {
  if (!queue.length) return
  const body = JSON.stringify(queue.splice(0))
  if (beacon && navigator.sendBeacon) navigator.sendBeacon('/api/track', new Blob([body], { type: 'application/json' }))
  else fetch('/api/track', { method: 'POST', body, keepalive: true, headers: { 'content-type': 'application/json' } }).catch(() => {})
}

export function Tracker({ locale }: { locale: string }) {
  const pathname = usePathname()
  const st = useRef({ start: Date.now(), maxScroll: 0, path: '' })
  // Off for Do-Not-Track and inside iframes (the admin heatmap previews pages in one).
  const off = typeof window !== 'undefined' && (navigator.doNotTrack === '1' || window.top !== window)
  const session = useMemo(() => {
    if (typeof window === 'undefined') return ''
    try {
      let s = sessionStorage.getItem('atl_sid')
      if (!s) { s = crypto.randomUUID(); sessionStorage.setItem('atl_sid', s) }
      return s
    } catch { return '' }
  }, [])

  useEffect(() => {
    if (off) return
    const leave = (beacon: boolean) => {
      const s = st.current
      if (!s.path) return
      queue.push({ type: 'leave', path: s.path, session, locale, value: Math.round((Date.now() - s.start) / 1000), x: s.maxScroll })
      flush(beacon)
    }
    if (st.current.path) leave(false)
    st.current = { start: Date.now(), maxScroll: 0, path: pathname }
    queue.push({ type: 'pageview', path: pathname, session, locale, referrer: document.referrer || undefined, vw: innerWidth })
    flush()
    const onHide = () => document.visibilityState === 'hidden' && leave(true)
    document.addEventListener('visibilitychange', onHide)
    return () => document.removeEventListener('visibilitychange', onHide)
  }, [pathname, locale, session, off])

  useEffect(() => {
    if (off) return
    const onScroll = () => {
      const h = document.documentElement
      const pct = Math.round(((h.scrollTop + innerHeight) / h.scrollHeight) * 100)
      if (pct > st.current.maxScroll) st.current.maxScroll = Math.min(100, pct)
    }
    const onClick = (e: MouseEvent) => {
      const el = e.target as HTMLElement
      const t = el.closest<HTMLElement>('a,button,summary,select,[data-track],[role=button],input')
      const h = document.documentElement
      queue.push({
        type: 'click',
        path: location.pathname,
        session, locale,
        x: Math.round((e.pageX / h.scrollWidth) * 1000) / 10,
        y: Math.round(e.pageY),
        vw: innerWidth,
        dh: h.scrollHeight,
        target: t ? (t.dataset.track || t.getAttribute('aria-label') || t.textContent || t.tagName).trim().replace(/\s+/g, ' ').slice(0, 80) : el.tagName.toLowerCase(),
        href: t instanceof HTMLAnchorElement ? t.getAttribute('href') : undefined,
      })
      if (queue.length >= 10) flush()
    }
    const timer = setInterval(() => flush(), 4000)
    addEventListener('scroll', onScroll, { passive: true })
    addEventListener('click', onClick, true)
    return () => { clearInterval(timer); removeEventListener('scroll', onScroll); removeEventListener('click', onClick, true) }
  }, [locale, session, off])
  return null
}
