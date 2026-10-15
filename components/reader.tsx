'use client'
import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Icon } from './Icon'
import type { Dict } from '@/lib/i18n'
import type { TocItem } from '@/lib/markdown'

/* ---------------- Prose: mermaid, copy buttons, image zoom ---------------- */
let mermaidP: Promise<typeof import('mermaid').default> | null = null
let mid = 0

async function renderMermaid(root: HTMLElement) {
  const blocks = [...root.querySelectorAll<HTMLElement>('.mermaid-block')]
  if (!blocks.length) return
  mermaidP ??= import('mermaid').then((m) => m.default)
  const mermaid = await mermaidP
  const dark = document.documentElement.dataset.theme === 'dark'
  const css = getComputedStyle(document.documentElement)
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    fontFamily: css.getPropertyValue('--font-body'),
    themeVariables: {
      darkMode: dark,
      background: 'transparent',
      primaryColor: css.getPropertyValue('--surface-2').trim(),
      primaryBorderColor: css.getPropertyValue('--ink-3').trim(),
      primaryTextColor: css.getPropertyValue('--ink').trim(),
      lineColor: css.getPropertyValue('--ink-3').trim(),
      secondaryColor: css.getPropertyValue('--mark-soft').trim(),
      tertiaryColor: css.getPropertyValue('--surface').trim(),
      fontSize: '15px',
      pie1: css.getPropertyValue('--c1').trim(),
      pie2: css.getPropertyValue('--c2').trim(),
      pie3: css.getPropertyValue('--k-article').trim(),
      pie4: css.getPropertyValue('--k-slides').trim(),
      pieStrokeColor: css.getPropertyValue('--surface').trim(),
      pieOuterStrokeColor: css.getPropertyValue('--line').trim(),
      pieSectionTextColor: '#ffffff',
      xyChart: { plotColorPalette: ['--c1', '--c2', '--k-article', '--k-slides'].map((v) => css.getPropertyValue(v).trim()).join(', ') },
    },
  })
  for (const b of blocks) {
    const src = b.querySelector('.mermaid-src')?.textContent ?? b.dataset.code ?? ''
    b.dataset.code = src
    try {
      const { svg } = await mermaid.render(`mmd-${++mid}`, src)
      b.innerHTML = svg
      b.dataset.rendered = 'true'
    } catch (e) {
      b.innerHTML = ''
      const err = document.createElement('div')
      err.className = 'mermaid-error'
      err.textContent = 'Mermaid: ' + (e as Error).message.split('\n')[0]
      const pre = document.createElement('pre')
      pre.textContent = src
      b.append(err, pre)
      b.dataset.rendered = 'error'
    }
  }
}

/* ---------------- Quizzes ---------------- */
const quizKey = () => `atl_quiz:${location.pathname}`
function enhanceQuizzes(root: HTMLElement, d: Dict) {
  const quizzes = [...root.querySelectorAll<HTMLElement>('.quiz')]
  if (!quizzes.length) return () => {}
  let saved: Record<string, boolean> = {}
  try { saved = JSON.parse(localStorage.getItem(quizKey()) || '{}') } catch {}
  const score = document.createElement('p')
  score.className = 'quiz-score'
  const updateScore = () => {
    const ok = Object.values(saved).filter(Boolean).length
    score.textContent = `${d.quizScore} : ${ok} / ${quizzes.length}`
    score.dataset.full = String(ok === quizzes.length)
  }
  quizzes.forEach((q, qi) => {
    if (q.dataset.ready) return
    q.dataset.ready = '1'
    const answer = q.dataset.answer!.split(',').map(Number)
    const multi = q.dataset.multi === 'true'
    const opts = [...q.querySelectorAll<HTMLButtonElement>('.quiz-opt')]
    const expl = q.querySelector<HTMLElement>('.quiz-expl')
    const verdict = document.createElement('p')
    verdict.className = 'quiz-verdict'
    verdict.setAttribute('aria-live', 'polite')
    const label = document.createElement('span')
    label.className = 'quiz-label'
    label.textContent = multi ? `${d.quiz} · ${d.quizMulti}` : d.quiz
    q.prepend(label)
    const picked = new Set<number>()
    const finish = () => {
      const right = picked.size === answer.length && answer.every((a) => picked.has(a))
      opts.forEach((o, i) => {
        o.disabled = true
        o.classList.toggle('is-right', answer.includes(i))
        o.classList.toggle('is-wrong', picked.has(i) && !answer.includes(i))
      })
      verdict.textContent = right ? d.quizRight : d.quizWrong
      q.dataset.state = right ? 'right' : 'wrong'
      if (expl) expl.hidden = false
      saved[qi] = right
      try { localStorage.setItem(quizKey(), JSON.stringify(saved)) } catch {}
      updateScore()
      retry.hidden = right
      check.hidden = true
    }
    const check = document.createElement('button')
    check.type = 'button'
    check.className = 'btn btn-primary quiz-check'
    check.textContent = d.quizCheck
    check.hidden = !multi
    check.onclick = () => picked.size && finish()
    const retry = document.createElement('button')
    retry.type = 'button'
    retry.className = 'btn btn-ghost quiz-retry'
    retry.textContent = d.quizRetry
    retry.hidden = true
    retry.onclick = () => {
      picked.clear()
      opts.forEach((o) => { o.disabled = false; o.classList.remove('is-right', 'is-wrong', 'is-picked'); o.setAttribute('aria-pressed', 'false') })
      verdict.textContent = ''
      delete q.dataset.state
      if (expl) expl.hidden = true
      retry.hidden = true
      check.hidden = !multi
    }
    opts.forEach((o, i) => {
      o.setAttribute('aria-pressed', 'false')
      o.onclick = () => {
        if (multi) {
          picked.has(i) ? picked.delete(i) : picked.add(i)
          o.classList.toggle('is-picked', picked.has(i))
          o.setAttribute('aria-pressed', String(picked.has(i)))
        } else { picked.add(i); finish() }
      }
    })
    const bar = document.createElement('div')
    bar.className = 'quiz-bar'
    bar.append(verdict, check, retry)
    q.append(bar)
  })
  updateScore()
  quizzes.at(-1)!.after(score)
  return () => score.remove()
}

/** GFM task lists become real checkboxes, remembered per page in this browser. */
function enhanceTasks(root: HTMLElement) {
  const boxes = [...root.querySelectorAll<HTMLInputElement>('.task-list-item input[type=checkbox]')]
  if (!boxes.length) return
  const key = `atl_tasks:${location.pathname}`
  let state: Record<string, boolean> = {}
  try { state = JSON.parse(localStorage.getItem(key) || '{}') } catch {}
  boxes.forEach((b, i) => {
    b.disabled = false
    if (i in state) b.checked = state[i]
    b.onchange = () => {
      state[i] = b.checked
      try { localStorage.setItem(key, JSON.stringify(state)) } catch {}
    }
  })
}

export function Prose({ html, d, className = '' }: { html: string; d: Dict; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [zoom, setZoom] = useState<{ src: string; alt: string } | null>(null)
  const dlg = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const root = ref.current!
    renderMermaid(root)
    // Re-theme diagrams when the theme flips.
    const obs = new MutationObserver(() => renderMermaid(root))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })

    for (const fig of root.querySelectorAll<HTMLElement>('figure.code-block')) {
      if (fig.querySelector('.copy-btn')) continue
      const btn = document.createElement('button')
      btn.className = 'copy-btn'
      btn.type = 'button'
      btn.textContent = d.copy
      btn.dataset.track = 'copy-code'
      btn.onclick = async () => {
        await navigator.clipboard?.writeText(fig.querySelector('pre')?.innerText ?? '').catch(() => {})
        btn.textContent = d.copied
        setTimeout(() => (btn.textContent = d.copy), 1500)
      }
      fig.append(btn)
    }
    const cleanupQuiz = enhanceQuizzes(root, d)
    enhanceTasks(root)
    const onClick = (e: MouseEvent) => {
      const b = (e.target as HTMLElement).closest('button.zoomable')
      const img = b?.querySelector('img')
      if (img) setZoom({ src: img.src, alt: img.alt })
    }
    root.addEventListener('click', onClick)
    return () => { obs.disconnect(); root.removeEventListener('click', onClick); cleanupQuiz() }
  }, [html, d])

  useEffect(() => { if (zoom) dlg.current?.showModal() }, [zoom])

  return (
    <>
      <div ref={ref} className={`prose ${className}`} dangerouslySetInnerHTML={{ __html: html }} />
      {zoom && (
        <dialog ref={dlg} className="lightbox" onClose={() => setZoom(null)} onClick={() => dlg.current?.close()}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={zoom.src} alt={zoom.alt} />
          {zoom.alt && <p>{zoom.alt}</p>}
        </dialog>
      )}
    </>
  )
}

/* ---------------- Table of contents with scroll-spy ---------------- */
export function Toc({ toc, title }: { toc: TocItem[]; title: string }) {
  const [active, setActive] = useState('')
  useEffect(() => {
    const els = toc.map((t) => document.getElementById(t.id)).filter(Boolean) as HTMLElement[]
    const io = new IntersectionObserver(
      (entries) => {
        const vis = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0]
        if (vis) setActive(vis.target.id)
      },
      { rootMargin: '-80px 0px -70% 0px' },
    )
    els.forEach((e) => io.observe(e))
    return () => io.disconnect()
  }, [toc])
  if (toc.length < 2) return null
  return (
    <nav className="toc" aria-label={title}>
      <p className="toc-title">{title}</p>
      <ul>
        {toc.map((t) => (
          <li key={t.id} className={`d${t.depth} ${active === t.id ? 'active' : ''}`}>
            <a href={`#${t.id}`}>{t.text}</a>
          </li>
        ))}
      </ul>
    </nav>
  )
}

/* ---------------- Progress ---------------- */
export type ProgressItem = { item: string; course: string | null; status: 'started' | 'completed'; pct: number; updated: number }
const saveProgress = (body: Record<string, unknown>) =>
  fetch('/api/progress', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), keepalive: true }).catch(() => {})
export const fetchProgress = (): Promise<ProgressItem[]> => fetch('/api/progress').then((r) => r.json()).then((j) => j.items).catch(() => [])

/** Reading bar + automatic "started"/scroll %, and "completed" at the end of the page or by button. */
export function ReadingProgress({ item, course, d, nextHref }: { item: string; course?: string; d: Dict; nextHref?: string }) {
  const [pct, setPct] = useState(0)
  const [done, setDone] = useState(false)
  const sent = useRef(0)
  useEffect(() => {
    fetchProgress().then((all) => setDone(all.some((p) => p.item === item && p.status === 'completed')))
    saveProgress({ item, course, status: 'started', pct: 0 })
    sent.current = 0
    const onScroll = () => {
      const h = document.documentElement
      const p = Math.min(100, Math.round(((h.scrollTop + innerHeight) / h.scrollHeight) * 100))
      setPct(p)
      const step = Math.floor(p / 25) * 25
      if (step > sent.current) {
        sent.current = step
        if (step >= 100) { saveProgress({ item, course, status: 'completed', pct: 100 }); setDone(true) }
        else saveProgress({ item, course, status: 'started', pct: step })
      }
    }
    onScroll()
    addEventListener('scroll', onScroll, { passive: true })
    return () => removeEventListener('scroll', onScroll)
  }, [item, course])
  const complete = () => { saveProgress({ item, course, status: 'completed', pct: 100 }); setDone(true) }
  return (
    <>
      <div className="read-bar" style={{ transform: `scaleX(${pct / 100})` }} aria-hidden="true" />
      <div className="complete-row">
        <button className={`btn ${done ? 'btn-done' : 'btn-ghost'}`} onClick={complete} data-track="mark-complete" aria-pressed={done}>
          <Icon name="check" /> {done ? d.completed : d.markComplete}
        </button>
        {nextHref && (
          <Link className="btn btn-primary" href={nextHref} onClick={complete} data-track="next-lesson">
            {d.next} <Icon name="right" className="flip-rtl" />
          </Link>
        )}
      </div>
    </>
  )
}

/** Marks lessons as done in a curriculum list and points the CTA to the first unfinished one. */
export function CourseProgress({ course, lessons, d }: { course: string; lessons: { item: string; href: string }[]; d: Dict }) {
  const [done, setDone] = useState<Set<string>>(new Set())
  const [started, setStarted] = useState(false)
  useEffect(() => {
    fetchProgress().then((all) => {
      const mine = all.filter((p) => p.course === course || lessons.some((l) => l.item === p.item))
      setStarted(mine.length > 0)
      setDone(new Set(mine.filter((p) => p.status === 'completed').map((p) => p.item)))
    })
  }, [course, lessons])
  useEffect(() => {
    document.querySelectorAll<HTMLElement>('[data-lesson]').forEach((el) => el.classList.toggle('is-done', done.has(el.dataset.lesson!)))
  }, [done])
  const next = lessons.find((l) => !done.has(l.item)) ?? lessons[0]
  const pct = lessons.length ? Math.round((done.size / lessons.length) * 100) : 0
  if (!next) return null
  return (
    <div className="course-cta">
      <Link className="btn btn-primary btn-lg" href={next.href} data-track={started ? 'resume-course' : 'start-course'}>
        <Icon name="play" size={14} /> {started ? d.resumeCourse : d.startCourse}
      </Link>
      <div className="meter" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={d.progress}>
        <span style={{ width: `${pct}%` }} />
      </div>
      <span className="meter-label">{d.progress} {pct}% · {done.size}/{lessons.length}</span>
    </div>
  )
}

/* ---------------- Slides ---------------- */
export function SlideDeck({ slides, d, title }: { slides: string[]; d: Dict; title: string }) {
  const [i, setI] = useState(0)
  const [asDoc, setAsDoc] = useState(false)
  const box = useRef<HTMLDivElement>(null)
  const n = slides.length
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (asDoc || /input|textarea|select/i.test((e.target as HTMLElement).tagName)) return
      const rtl = document.dir === 'rtl'
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); setI((x) => Math.min(n - 1, x + (rtl && e.key === 'ArrowRight' ? -1 : 1))) }
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); setI((x) => Math.max(0, x + (rtl && e.key === 'ArrowLeft' ? 1 : -1))) }
      if (e.key === 'Home') setI(0)
      if (e.key === 'End') setI(n - 1)
      if (e.key.toLowerCase() === 'f') box.current?.requestFullscreen?.()
    }
    addEventListener('keydown', k)
    return () => removeEventListener('keydown', k)
  }, [n, asDoc])
  if (asDoc)
    return (
      <div className="deck-doc">
        <button className="btn btn-ghost" onClick={() => setAsDoc(false)} data-track="slides-view"><Icon name="slides" /> {d.viewAsSlides}</button>
        {slides.map((s, k) => <Prose key={k} html={s} d={d} className="slide-doc" />)}
      </div>
    )
  return (
    <div className="deck" ref={box} aria-roledescription="carousel" aria-label={title}>
      <div className="deck-stage">
        <Prose key={i} html={slides[i]} d={d} className="slide" />
      </div>
      <div className="deck-bar">
        <button className="icon-btn" onClick={() => setI(Math.max(0, i - 1))} disabled={i === 0} aria-label={d.previous} data-track="slide-prev"><Icon name="left" className="flip-rtl" /></button>
        <span className="deck-count" aria-live="polite">{d.slideOf} {i + 1} / {n}</span>
        <button className="icon-btn" onClick={() => setI(Math.min(n - 1, i + 1))} disabled={i === n - 1} aria-label={d.next} data-track="slide-next"><Icon name="right" className="flip-rtl" /></button>
        <div className="deck-progress"><span style={{ width: `${((i + 1) / n) * 100}%` }} /></div>
        <button className="icon-btn" onClick={() => setAsDoc(true)} aria-label={d.viewAsDoc} title={d.viewAsDoc} data-track="doc-view"><Icon name="book" /></button>
        <button className="icon-btn" onClick={() => box.current?.requestFullscreen?.()} aria-label={d.fullscreen} title={d.fullscreen} data-track="fullscreen"><Icon name="expand" /></button>
      </div>
    </div>
  )
}
