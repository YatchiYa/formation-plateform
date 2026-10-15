import Link from 'next/link'
import path from 'node:path'
import { notFound } from 'next/navigation'
import { getTree, items, localized, countItems, formatOf, type Format, type Node } from '@/lib/content'
import { card, starters, themes } from '@/lib/catalog'
import { isLocale, t, type Dict, type Locale } from '@/lib/i18n'
import { ContentCard, FormatTiles, ThemeTile } from '@/components/cards'
import { Icon } from '@/components/Icon'

export const dynamic = 'force-dynamic'

function TreeNode({ n, l, d, depth }: { n: Node; l: Locale; d: Dict; depth: number }) {
  const m = localized(n, l).meta
  const doc = Object.values(n.docs)[0]
  const loose = doc && !/^(index|README)(\.\w\w)?\.mdx?$/.test(path.basename(doc.file))
  const fsName = loose ? path.basename(doc.file) : path.basename(n.dir) + '/'
  const label = (
    <>
      <span className="tn-icon" aria-hidden="true">{n.kind === 'category' ? (m.icon ?? '📁') : n.kind === 'course' ? '▤' : m.slides ? '▭' : '¶'}</span>
      <span className="tn-title">{m.title}</span>
      <span className="tn-path">{fsName}</span>
      <span className="tn-meta">{n.kind === 'category' ? countItems(n) : n.kind === 'course' ? `${n.lessons!.length} ${d.lessons}` : ''}</span>
    </>
  )
  if (n.kind !== 'category')
    return <li className={`tn tn-${n.kind}`}><Link href={`/${l}${n.url}`} className="tn-row" data-track="tree-item">{label}</Link></li>
  return (
    <li className="tn tn-category">
      <details open={depth < 1}>
        <summary className="tn-row" data-track="tree-folder">{label}</summary>
        <ul>{n.children.map((c) => <TreeNode key={c.url} n={c} l={l} d={d} depth={depth + 1} />)}</ul>
      </details>
    </li>
  )
}

export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!isLocale(locale)) notFound()
  const l = locale
  const d = t(l)
  const tree = getTree()
  const all = items(tree)
  const counts: Partial<Record<Format, number>> = {}
  for (const n of all) { const f = formatOf(n, localized(n, l).meta) as Format; counts[f] = (counts[f] ?? 0) + 1 }
  // Skills come by the hundred: keep them out of "latest" so courses and articles stay visible.
  const latest = all.map((n) => card(n, l)).filter((c) => c.format !== 'skill').sort((a, b) => (b.date ?? '').localeCompare(a.date ?? '')).slice(0, 6)
  const lessonCount = tree.all.filter((n) => n.kind === 'lesson').length

  return (
    <div className="home">
      <section className="hero">
        <div className="hero-text">
          <h1 className="hero-title">{d.heroTitle}</h1>
          <p className="hero-lede">{d.heroText}</p>
          <div className="hero-cta">
            <Link className="btn btn-primary btn-lg" href={`/${l}/explore`} data-track="hero-explore">{d.heroCta}</Link>
            <Link className="btn btn-ghost btn-lg" href={`/${l}/me`} data-track="hero-resume">{d.heroSecondary}</Link>
          </div>
          <p className="hero-stats">
            <strong>{counts.course ?? 0}</strong> {d.pl_course.toLowerCase()} · <strong>{lessonCount}</strong> {d.lessons} · <strong>{counts.skill ?? 0}</strong> {d.pl_skill.toLowerCase()} · <strong>{all.length}</strong> {d.items}
          </p>
        </div>
        <div className="hero-tree" aria-label={d.browseTree}>
          <div className="window-bar"><span /><span /><span /><code>content/</code></div>
          <ul className="tree">{tree.root.children.map((c) => <TreeNode key={c.url} n={c} l={l} d={d} depth={0} />)}</ul>
          <p className="tree-caption">{d.browseTree}</p>
        </div>
      </section>

      <section className="home-section">
        <div className="section-head">
          <h2 className="section-title">{d.whatToLearn}</h2>
          <Link href={`/${l}/explore`} className="text-link">{d.explore} <Icon name="right" size={14} className="flip-rtl" /></Link>
        </div>
        <ul className="theme-tiles">{themes(l).map((th) => <ThemeTile key={th.url} t={th} d={d} />)}</ul>
      </section>

      <section className="home-section">
        <h2 className="section-title">{d.startHere}</h2>
        <p className="section-sub">{d.startHereText}</p>
        <ul className="card-grid">{starters(l).map((c) => <ContentCard key={c.url} c={c} d={d} />)}</ul>
      </section>

      <section className="home-section">
        <h2 className="section-title">{d.browseFormats}</h2>
        <FormatTiles counts={counts} d={d} hrefFor={(f) => `/${l}/explore?format=${f}`} />
      </section>

      <section className="home-section">
        <div className="section-head">
          <h2 className="section-title">{d.latest}</h2>
          <Link href={`/${l}/explore`} className="text-link">{d.seeAll} <Icon name="right" size={14} className="flip-rtl" /></Link>
        </div>
        <ul className="card-grid">{latest.map((c) => <ContentCard key={c.url} c={c} d={d} />)}</ul>
      </section>
    </div>
  )
}
