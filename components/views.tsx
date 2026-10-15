import Link from 'next/link'
import { Icon } from './Icon'
import { Prose, Toc, ReadingProgress, CourseProgress, SlideDeck } from './reader'
import { card, themes, type Card } from '@/lib/catalog'
import { ContentCard, FORMAT_ORDER, ThemeTile, plural, FORMAT_ICON } from './cards'
import { countItems, courseOf, crumbs, fileUrl, getTree, hubs, items, localized, type Asset, type Format, type Node, type Reference } from '@/lib/content'
import path from 'node:path'
import { render, splitSlides, videoEmbed } from '@/lib/markdown'
import { canRead, getViewer } from '@/lib/viewer'
import type { Dict, Locale } from '@/lib/i18n'

const L = (d: Dict, k: string) => (d as Record<string, string>)[k] ?? k
const fmtSize = (n: number) => (n > 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`)
const fmtDate = (s: string | undefined, l: Locale) => {
  if (!s) return ''
  const dt = new Date(s)
  return isNaN(+dt) ? s : dt.toLocaleDateString(l === 'ar' ? 'ar' : l, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function KindTag({ c, d }: { c: Pick<Card, 'format'>; d: Dict }) {
  return <span className={`kind kind-${c.format}`}><Icon name={FORMAT_ICON[c.format] ?? 'file'} size={12} /> {L(d, c.format)}</span>
}

export function MetaLine({ c, d, l }: { c: Card; d: Dict; l: Locale }) {
  const bits: React.ReactNode[] = []
  if (c.level) bits.push(<span key="lv" className={`level level-${c.level}`}><i /><i /><i />{L(d, c.level)}</span>)
  if (c.lessons) bits.push(<span key="ls"><Icon name="book" size={14} /> {c.lessons} {d.lessons}</span>)
  if (c.duration) bits.push(<span key="du"><Icon name="clock" size={14} /> {c.duration}</span>)
  else if (['course', 'article', 'slides', 'lesson'].includes(c.format)) bits.push(<span key="mn"><Icon name="clock" size={14} /> {c.minutes} {d.minRead}</span>)
  if (c.date) bits.push(<time key="dt" dateTime={c.date}>{fmtDate(c.date, l)}</time>)
  if (c.premium) bits.push(<span key="pr" className="premium"><Icon name="lock" size={13} /> {d.premium}</span>)
  return <div className="meta-line">{bits}</div>
}

export function ItemRow({ c, d, l }: { c: Card; d: Dict; l: Locale }) {
  return (
    <li className="item-row">
      <Link href={c.url} className="item-link" data-track="item-open">
        <div className="item-head">
          <KindTag c={c} d={d} />
          {c.section && <span className="item-section">{c.section}</span>}
        </div>
        <h3 className="item-title">{c.title}</h3>
        {c.description && <p className="item-desc">{c.description}</p>}
        <MetaLine c={c} d={d} l={l} />
      </Link>
    </li>
  )
}

function Breadcrumbs({ n, l, d }: { n: Node; l: Locale; d: Dict }) {
  const cs = crumbs(n)
  return (
    <nav className="crumbs" aria-label="breadcrumb">
      <Link href={`/${l}`}>{d.home}</Link>
      {cs.filter((c) => c.path.length).map((c) => (
        <span key={c.url}><span className="sep" aria-hidden="true">/</span><Link href={`/${l}${c.url}`}>{localized(c, l).meta.title}</Link></span>
      ))}
    </nav>
  )
}

function TranslationNote({ translated, d }: { translated: boolean; d: Dict }) {
  return translated ? null : <p className="note-banner" role="note"><Icon name="globe" size={16} /> {d.notTranslated}</p>
}

function Tags({ tags, l }: { tags: string[]; l: Locale }) {
  if (!tags.length) return null
  return <ul className="tags">{tags.map((t) => <li key={t}><Link href={`/${l}/explore?tag=${encodeURIComponent(t)}`}>#{t}</Link></li>)}</ul>
}

const refIcon: Record<Reference['kind'], string> = { github: 'github', video: 'video', paper: 'paper', docs: 'book', article: 'link' }
export function References({ refs, d }: { refs: Reference[]; d: Dict }) {
  if (!refs.length) return null
  return (
    <section className="block" aria-labelledby="refs">
      <h2 id="refs" className="block-title">{d.references}</h2>
      <ul className="refs">
        {refs.map((r) => (
          <li key={r.url}>
            <a href={r.url} target="_blank" rel="noopener noreferrer" className={`ref ref-${r.kind}`} data-track="reference">
              <Icon name={refIcon[r.kind]} />
              <span className="ref-body">
                <span className="ref-title">{r.title}</span>
                <span className="ref-host">{new URL(r.url).host.replace(/^www\./, '')}{r.note ? ` — ${r.note}` : ''}</span>
              </span>
              <Icon name="external" size={14} className="flip-rtl" />
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}

export function Resources({ files, d, zip }: { files: Asset[]; d: Dict; zip?: string }) {
  if (!files.length && !zip) return null
  return (
    <section className="block" aria-labelledby="res">
      <h2 id="res" className="block-title">{d.resources}</h2>
      <ul className="files">
        {files.map((f) => (
          <li key={f.url}>
            <a className="file-card" href={`${f.url}?dl=1`} download data-track="download">
              <span className="file-ext" data-ext={f.ext}>{f.ext}</span>
              <span className="file-name">{f.name}</span>
              <span className="file-size">{fmtSize(f.size)}</span>
            </a>
          </li>
        ))}
      </ul>
      {zip && <a className="btn btn-ghost" href={zip} download data-track="download-zip"><Icon name="download" /> {d.downloadAll}</a>}
    </section>
  )
}

/** Links from a course/article to the platforms and use cases it relates to. */
function HubChips({ meta, l, d }: { meta: { platforms: string[]; usecases: string[] }; l: Locale; d: Dict }) {
  if (!meta.platforms.length && !meta.usecases.length) return null
  const h = hubs(getTree())
  const row = (label: string, kind: 'platform' | 'usecase', slugs: string[]) => {
    const nodes = slugs.map((s) => h[kind].get(s)).filter(Boolean) as Node[]
    if (!nodes.length) return null
    return (
      <div className="hub-row">
        <span className="hub-label">{label}</span>
        {nodes.map((n) => {
          const m = localized(n, l).meta
          return <Link key={n.url} href={`/${l}${n.url}`} className={`hub-chip hub-${kind}`} data-track={`hub-${kind}`}>{m.icon ?? ''} {m.title}</Link>
        })}
      </div>
    )
  }
  return <div className="hubs">{row(d.forUsecases, 'usecase', meta.usecases)}{row(d.onPlatforms, 'platform', meta.platforms)}</div>
}

/** On a platform / use-case page: everything that points to it. */
function Related({ n, kind, l, d }: { n: Node; kind: 'platform' | 'usecase'; l: Locale; d: Dict }) {
  const list = hubs(getTree()).related(kind, n.path.at(-1)!).map((x) => card(x, l))
  if (!list.length) return null
  return (
    <section className="fsection">
      <h2 className="section-title">{d.related} <small>{list.length}</small></h2>
      <ul className="card-grid">{list.map((c) => <ContentCard key={c.url} c={c} d={d} />)}</ul>
    </section>
  )
}

function Locked({ d }: { d: Dict }) {
  return (
    <div className="locked">
      <Icon name="lock" size={28} />
      <p><strong>{d.premiumLocked}</strong></p>
      <p>{d.premiumCta}</p>
    </div>
  )
}

/** Premium content behind the gate keeps its first paragraphs as a teaser. */
const teaser = (body: string) => body.split(/\n(?=#{2}\s)/)[0].slice(0, 1200)

/* ---------------- Category ---------------- */
export async function CategoryView({ n, l, d }: { n: Node; l: Locale; d: Dict }) {
  const doc = localized(n, l)
  const intro = doc.body.trim() ? await render(doc.body, { file: doc.file, locale: l }) : null
  const longIntro = doc.body.length > 1500
  const subs = themes(l, n)
  const leaves = n.children.filter((c) => c.kind !== 'category').map((c) => card(c, l))
  const byFormat = FORMAT_ORDER.map((f) => [f, leaves.filter((c) => c.format === f)] as const).filter(([, list]) => list.length)
  return (
    <div className="page">
      <Breadcrumbs n={n} l={l} d={d} />
      <header className="page-head">
        {doc.meta.icon && <span className="page-icon" aria-hidden="true">{doc.meta.icon}</span>}
        <h1 className="display">{doc.meta.title}</h1>
        {doc.meta.description && <p className="lede">{doc.meta.description}</p>}
        <div className="head-actions">
          <span className="count">{countItems(n)} {d.items}</span>
          <a className="btn btn-ghost" href={`/api/download${n.url}`} download data-track="download-theme"><Icon name="download" /> {d.downloadAll}</a>
        </div>
      </header>
      <TranslationNote translated={doc.translated || !doc.file} d={d} />
      {intro && !longIntro && <Prose html={intro.html} d={d} />}
      {subs.length > 0 && (
        <section className="block">
          {leaves.length > 0 && <h2 className="block-title">{d.subThemes}</h2>}
          <ul className="theme-tiles">{subs.map((t) => <ThemeTile key={t.url} t={t} d={d} />)}</ul>
        </section>
      )}
      {byFormat.map(([f, list]) => (
        <section key={f} className="fsection">
          <h2 className="section-title"><span className={`ficon ficon-${f}`}><Icon name={FORMAT_ICON[f]} size={16} /></span>{plural(d, f)} <small>{list.length}</small></h2>
          <ul className={`card-grid ${f === 'skill' ? 'card-grid-dense' : ''}`}>
            {list.map((c) => <ContentCard key={c.url} c={c} d={d} compact={f === 'skill'} showTrail={false} />)}
          </ul>
        </section>
      ))}
      {/* A long theme guide (e.g. an imported README) comes after the contents, so they stay one glance away. */}
      {intro && longIntro && <section className="block"><Prose html={intro.html} d={d} /></section>}
    </div>
  )
}

/* ---------------- Course overview ---------------- */
export async function CourseView({ n, l, d }: { n: Node; l: Locale; d: Dict }) {
  const doc = localized(n, l)
  const c = card(n, l)
  const viewer = await getViewer()
  const ok = canRead(doc.meta, viewer)
  const intro = doc.body.trim() ? await render(ok ? doc.body : teaser(doc.body), { file: doc.file, locale: l }) : null
  const lessons = n.lessons!.map((x) => ({ item: x.url, href: `/${l}${x.url}` }))
  const groups = n.children.some((x) => x.kind === 'module') ? n.children.map((x) => (x.kind === 'module' ? x : null)) : [null]
  let k = 0
  return (
    <div className="page page-course">
      <Breadcrumbs n={n} l={l} d={d} />
      <header className="course-head">
        <div className="course-head-text">
          <KindTag c={c} d={d} />
          <h1 className="display">{doc.meta.title}</h1>
          {doc.meta.description && <p className="lede">{doc.meta.description}</p>}
          <MetaLine c={c} d={d} l={l} />
          {doc.meta.authors.length > 0 && <p className="byline">{d.by} {doc.meta.authors.join(', ')}</p>}
          <HubChips meta={doc.meta} l={l} d={d} />
          {ok ? <CourseProgress course={n.url} lessons={lessons} d={d} /> : <Locked d={d} />}
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {doc.meta.cover && <img className="course-cover" src={doc.meta.cover} alt="" />}
      </header>
      <TranslationNote translated={doc.translated} d={d} />
      <div className="course-grid">
        <div>
          {intro && <Prose html={intro.html} d={d} />}
          <Tags tags={doc.meta.tags} l={l} />
        </div>
        <aside>
          <section className="block curriculum" aria-labelledby="cur">
            <h2 id="cur" className="block-title">{d.curriculum}</h2>
            {groups.map((g, gi) => {
              const ls = g ? g.children : n.children.filter((x) => x.kind === 'lesson')
              if (!ls.length) return null
              return (
                <div key={gi} className="module" id={g ? `module-${g.path.at(-1)}` : undefined}>
                  {g && <h3 className="module-title"><span>{d.module} {gi + 1}</span>{localized(g, l).meta.title}</h3>}
                  <ol className="lesson-rail" start={k + 1}>
                    {ls.map((x) => {
                      k++
                      const lm = localized(x, l).meta
                      return (
                        <li key={x.url} data-lesson={x.url}>
                          <Link href={`/${l}${x.url}`} data-track="lesson-open">
                            <span className="rail-dot" aria-hidden="true">{k}</span>
                            <span className="rail-title">{lm.title}</span>
                            {lm.slides && <Icon name="slides" size={14} />}
                          </Link>
                        </li>
                      )
                    })}
                  </ol>
                </div>
              )
            })}
          </section>
        </aside>
      </div>
      <Resources files={n.files} d={d} zip={ok ? `/api/download${n.url}` : undefined} />
      <References refs={doc.meta.references} d={d} />
    </div>
  )
}

/* ---------------- Article (document or slides) ---------------- */
export async function ArticleView({ n, l, d }: { n: Node; l: Locale; d: Dict }) {
  const doc = localized(n, l)
  const c = card(n, l)
  const ok = canRead(doc.meta, await getViewer())
  const body = ok ? doc.body : teaser(doc.body)
  return (
    <div className="page">
      <Breadcrumbs n={n} l={l} d={d} />
      <header className="page-head article-head">
        <KindTag c={c} d={d} />
        <h1 className="display">{doc.meta.title}</h1>
        {doc.meta.description && <p className="lede">{doc.meta.description}</p>}
        <MetaLine c={c} d={d} l={l} />
        {doc.meta.authors.length > 0 && <p className="byline">{d.by} {doc.meta.authors.join(', ')}</p>}
      </header>
      <TranslationNote translated={doc.translated} d={d} />
      {ok && c.format === 'video' && doc.meta.video && <VideoHero url={doc.meta.video} dir={n.dir} title={doc.meta.title} />}
      {ok && (c.format === 'link' || c.format === 'platform') && doc.meta.link && <LinkHero url={doc.meta.link} d={d} label={c.format === 'platform' ? d.visit : undefined} />}
      <HubChips meta={doc.meta} l={l} d={d} />
      {ok && c.format === 'skill' && <SkillPanel files={n.files} triggers={doc.meta.triggers} d={d} />}
      {doc.meta.slides && ok ? (
        <Deck md={body} file={doc.file} l={l} d={d} title={doc.meta.title} />
      ) : !body.trim() ? null : (
        <Reading md={body} file={doc.file} l={l} d={d} item={n.url} track={ok && !['link', 'platform', 'usecase'].includes(c.format)}>
          {!ok && <Locked d={d} />}
        </Reading>
      )}
      <Tags tags={doc.meta.tags} l={l} />
      {/* Skills carry their downloads in the panel; a video or a link has nothing worth zipping. */}
      {(c.format === 'platform' || c.format === 'usecase') && <Related n={n} kind={c.format} l={l} d={d} />}
      {(c.format === 'article' || c.format === 'slides') && <Resources files={n.files} d={d} zip={ok ? `/api/download${n.url}` : undefined} />}
      <References refs={doc.meta.references} d={d} />
    </div>
  )
}

function VideoHero({ url, dir, title }: { url: string; dir: string; title: string }) {
  const embed = videoEmbed(url)
  if (embed) return <figure className="embed embed-video video-hero"><iframe src={embed} title={title} allow="accelerometer; encrypted-media; picture-in-picture; fullscreen" allowFullScreen /></figure>
  const src = /^https?:/.test(url) ? url : fileUrl(path.resolve(dir, url))
  return <figure className="embed embed-media video-hero"><video src={src} controls preload="metadata" playsInline /></figure>
}

function LinkHero({ url, d, label }: { url: string; d: Dict; label?: string }) {
  const u = new URL(url)
  const gh = /github\.com$/.test(u.host) ? u.pathname.split('/').filter(Boolean).slice(0, 2).join('/') : null
  return (
    <a className={`link-hero ${gh ? 'link-hero-gh' : ''}`} href={url} target="_blank" rel="noopener noreferrer" data-track="open-link">
      <Icon name={gh ? 'github' : 'link'} size={28} />
      <span className="link-hero-body">
        <span className="link-hero-title">{gh ?? u.host.replace(/^www\./, '')}</span>
        <span className="link-hero-url">{url}</span>
      </span>
      <span className="btn btn-primary">{label ?? d.openLink} <Icon name="external" size={14} className="flip-rtl" /></span>
    </a>
  )
}

/** How to use a skill: the ready-to-import downloads first, then the 3 steps and its trigger phrases. */
function SkillPanel({ files, triggers, d }: { files: Asset[]; triggers: string[]; d: Dict }) {
  const pkgs = files.filter((f) => f.ext === 'zip' || f.ext === 'md')
  return (
    <section className="skill-panel" aria-labelledby="use-skill">
      <h2 id="use-skill" className="skill-panel-title"><Icon name="spark" /> {d.useSkill}</h2>
      <div className="skill-panel-grid">
        <ol className="skill-steps">{d.skillSteps.split('|').map((s, i) => <li key={i}>{s}</li>)}</ol>
        <div className="skill-downloads">
          {pkgs.map((f) => (
            <a key={f.url} className="btn btn-primary" href={`${f.url}?dl=1`} download data-track="download-skill"><Icon name="download" /> {f.name}</a>
          ))}
        </div>
      </div>
      {triggers.length > 0 && (
        <>
          <p className="skill-trig-label">{d.skillTriggers}</p>
          <ul className="skill-triggers">{triggers.map((t) => <li key={t}>« {t} »</li>)}</ul>
        </>
      )}
    </section>
  )
}

async function Deck({ md, file, l, d, title }: { md: string; file: string; l: Locale; d: Dict; title: string }) {
  const slides = await Promise.all(splitSlides(md).map(async (s) => (await render(s, { file, locale: l })).html))
  return <SlideDeck slides={slides} d={d} title={title} />
}

async function Reading({ md, file, l, d, item, course, nextHref, track, children }: { md: string; file: string; l: Locale; d: Dict; item: string; course?: string; nextHref?: string; track: boolean; children?: React.ReactNode }) {
  const r = await render(md, { file, locale: l })
  return (
    <div className="reading">
      <article className="reading-main">
        <Prose html={r.html} d={d} />
        {children}
        {track && <ReadingProgress item={item} course={course} d={d} nextHref={nextHref} />}
      </article>
      <aside className="reading-aside"><Toc toc={r.toc} title={d.onThisPage} /></aside>
    </div>
  )
}

/* ---------------- Lesson inside a course ---------------- */
export async function LessonView({ n, l, d }: { n: Node; l: Locale; d: Dict }) {
  const course = courseOf(n)!
  const cdoc = localized(course, l)
  const doc = localized(n, l)
  const ok = canRead(cdoc.meta, await getViewer()) && canRead(doc.meta, await getViewer())
  const list = course.lessons!
  const idx = list.indexOf(n)
  const prev = list[idx - 1]
  const next = list[idx + 1]
  const mod = n.parent?.kind === 'module' ? n.parent : null
  return (
    <div className="lesson-layout">
      <aside className="lesson-nav" aria-label={d.curriculum}>
        <details open>
          <summary>
            <Link href={`/${l}${course.url}`} className="lesson-nav-course">{cdoc.meta.title}</Link>
            <span className="lesson-nav-count">{idx + 1}/{list.length}</span>
          </summary>
          {(course.children.some((c) => c.kind === 'module') ? course.children : [course]).map((g) => (
            <div key={g.url} className="module">
              {g !== course && <p className="module-title">{localized(g, l).meta.title}</p>}
              <ol className="lesson-rail compact">
                {(g === course ? g.children.filter((c) => c.kind === 'lesson') : g.children).map((x) => (
                  <li key={x.url} data-lesson={x.url} className={x === n ? 'current' : ''}>
                    <Link href={`/${l}${x.url}`} aria-current={x === n ? 'page' : undefined} data-track="lesson-nav">
                      <span className="rail-dot" aria-hidden="true">{list.indexOf(x) + 1}</span>
                      <span className="rail-title">{localized(x, l).meta.title}</span>
                    </Link>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </details>
        <CourseProgressMarks course={course} l={l} d={d} />
      </aside>
      <div className="lesson-main">
        <Breadcrumbs n={n} l={l} d={d} />
        <header className="page-head lesson-head">
          <p className="lesson-kicker">{d.lesson} {idx + 1}{mod ? ` — ${localized(mod, l).meta.title}` : ''}</p>
          <h1 className="display display-sm">{doc.meta.title}</h1>
          <MetaLine c={card(n, l)} d={d} l={l} />
        </header>
        <TranslationNote translated={doc.translated} d={d} />
        {!ok ? (
          <Locked d={d} />
        ) : doc.meta.slides ? (
          <>
            <Deck md={doc.body} file={doc.file} l={l} d={d} title={doc.meta.title} />
            <ReadingProgress item={n.url} course={course.url} d={d} nextHref={next ? `/${l}${next.url}` : undefined} />
          </>
        ) : (
          <Reading md={doc.body} file={doc.file} l={l} d={d} item={n.url} course={course.url} nextHref={next ? `/${l}${next.url}` : undefined} track />
        )}
        <References refs={doc.meta.references} d={d} />
        <nav className="pager" aria-label="pagination">
          {prev ? (
            <Link href={`/${l}${prev.url}`} className="pager-link" data-track="prev-lesson">
              <small><Icon name="left" size={14} className="flip-rtl" /> {d.previous}</small>
              <span>{localized(prev, l).meta.title}</span>
            </Link>
          ) : <span />}
          {next && (
            <Link href={`/${l}${next.url}`} className="pager-link pager-next" data-track="next-lesson-pager">
              <small>{d.next} <Icon name="right" size={14} className="flip-rtl" /></small>
              <span>{localized(next, l).meta.title}</span>
            </Link>
          )}
        </nav>
      </div>
    </div>
  )
}

function CourseProgressMarks({ course, l, d }: { course: Node; l: Locale; d: Dict }) {
  return <CourseProgress course={course.url} lessons={course.lessons!.map((x) => ({ item: x.url, href: `/${l}${x.url}` }))} d={d} />
}
