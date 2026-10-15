import Link from 'next/link'
import { getTree, items } from '@/lib/content'
import { locales } from '@/lib/i18n'
import { overview, RANGES, type Range } from '@/lib/stats'
import { BarList, Kpi, RangePicker, TrafficChart, dur, fmt } from '@/components/admin'

export const dynamic = 'force-dynamic'

export default async function Admin({ searchParams }: { searchParams: Promise<{ range?: string }> }) {
  const sp = await searchParams
  const range = (sp.range && sp.range in RANGES ? sp.range : '7d') as Range
  const o = overview(range)
  const tree = getTree()
  const its = items(tree)
  const lessons = tree.all.filter((n) => n.kind === 'lesson')
  const docs = [...its, ...lessons]
  const coverage = locales.map((l) => [l, Math.round((docs.filter((n) => n.docs[l]).length / Math.max(1, docs.length)) * 100)] as const)

  return (
    <div className="page admin-page">
      <header className="admin-head">
        <div>
          <h1 className="display display-sm">Vue d’ensemble</h1>
          <p className="live"><span className="pulse" aria-hidden="true" /> {o.live} visiteur{o.live > 1 ? 's' : ''} actif{o.live > 1 ? 's' : ''} (5 dernières minutes)</p>
        </div>
        <RangePicker range={range} base="/admin" />
      </header>

      <div className="kpis">
        <Kpi label="Visiteurs uniques" value={o.now.visitors} prev={o.prev.visitors} />
        <Kpi label="Pages vues" value={o.now.views} prev={o.prev.views} />
        <Kpi label="Sessions" value={o.now.sessions} prev={o.prev.sessions} />
        <Kpi label="Temps moyen par page" value={o.now.avgTime} prev={o.prev.avgTime} display={dur(o.now.avgTime)} />
        <Kpi label="Défilement moyen" value={o.now.avgScroll} display={`${Math.round(o.now.avgScroll)} %`} />
        <Kpi label="Clics" value={o.now.clicks} prev={o.prev.clicks} />
        <Kpi label="Téléchargements" value={o.now.downloads} prev={o.prev.downloads} />
      </div>

      <section className="panel panel-wide">
        <h2 className="panel-title">Trafic</h2>
        <TrafficChart series={o.series} hourly={range === '24h'} />
      </section>

      <section className="panel panel-wide">
        <h2 className="panel-title">Pages les plus lues</h2>
        {o.pages.length ? (
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th>Page</th><th>Vues</th><th>Visiteurs</th><th>Temps moyen</th><th>Défilement</th><th>Clics</th><th /></tr></thead>
              <tbody>
                {o.pages.map((p) => (
                  <tr key={String(p.path)}>
                    <td><a href={String(p.path)} target="_blank" rel="noreferrer">{String(p.path)}</a></td>
                    <td>{fmt(Number(p.views))}</td>
                    <td>{fmt(Number(p.visitors))}</td>
                    <td>{p.avgTime ? dur(Number(p.avgTime)) : '—'}</td>
                    <td>{p.scroll != null ? `${Math.round(Number(p.scroll))} %` : '—'}</td>
                    <td>{fmt(Number(p.clicks))}</td>
                    <td><Link href={`/admin/heatmap?path=${encodeURIComponent(String(p.path))}&range=${range}`}>Carte des clics</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="empty">Aucune visite sur la période. Ouvrez le site dans un autre onglet pour voir les premières données arriver.</p>}
      </section>

      <div className="panels">
        <BarList title="Éléments les plus cliqués" rows={o.clicks.map((c, i) => ({ key: String(i), label: String(c.target), sub: String(c.path), n: Number(c.n) }))} />
        <BarList title="Téléchargements" rows={o.downloads.map((c) => ({ key: String(c.path), label: decodeURIComponent(String(c.path).split('/').pop() || ''), sub: String(c.path), n: Number(c.n) }))} />
        <BarList title="Liens externes suivis" rows={o.outbound.map((c) => ({ key: String(c.href), label: String(c.href).replace(/^https?:\/\/(www\.)?/, ''), n: Number(c.n) }))} />
        <BarList title="Sources de trafic" rows={o.referrers.map(([k, n]) => ({ key: k, label: k, n }))} empty="Uniquement du trafic direct pour l’instant." />
        <BarList title="Progression des lecteurs" rows={o.completions.map((c) => ({ key: String(c.item), label: String(c.item), sub: `${c.done} terminé(s)`, n: Number(c.readers) }))} />
        <BarList title="Langues" rows={o.locales.map((c) => ({ key: String(c.k), label: String(c.k), n: Number(c.n) }))} />
        <BarList title="Appareils" rows={o.devices.map((c) => ({ key: String(c.k), label: String(c.k), n: Number(c.n) }))} />
        <BarList title="Navigateurs" rows={o.browsers.map((c) => ({ key: String(c.k), label: String(c.k), n: Number(c.n) }))} />
        <BarList title="Pays" rows={o.countries.map((c) => ({ key: String(c.k), label: String(c.k), n: Number(c.n) }))} empty="Le pays apparaît derrière un CDN qui transmet l’en-tête cf-ipcountry." />
      </div>

      <div className="panels">
        <section className="panel">
          <h2 className="panel-title">Catalogue</h2>
          <dl className="stats-dl">
            <dt>Formations</dt><dd>{its.filter((n) => n.kind === 'course').length}</dd>
            <dt>Leçons</dt><dd>{lessons.length}</dd>
            <dt>Articles</dt><dd>{its.filter((n) => n.kind === 'article').length}</dd>
            <dt>Premium</dt><dd>{its.filter((n) => Object.values(n.docs)[0]?.meta.access === 'premium').length}</dd>
            <dt>Fichiers joints</dt><dd>{its.reduce((s, n) => s + n.files.length, 0)}</dd>
          </dl>
          <h3 className="panel-sub">Couverture des traductions</h3>
          <ul className="barlist">
            {coverage.map(([l, p]) => <li key={l}><span className="barlist-fill" style={{ width: `${p}%` }} /><span className="barlist-label">{l}</span><span className="barlist-n">{p} %</span></li>)}
          </ul>
        </section>
        <section className="panel panel-span2">
          <h2 className="panel-title">Activité récente</h2>
          <ol className="feed">
            {o.recent.map((e, i) => (
              <li key={i}>
                <time>{new Date(Number(e.ts)).toLocaleTimeString('fr-FR')}</time>
                <span className={`ev ev-${e.type}`}>{String(e.type)}</span>
                <span className="feed-path">{String(e.path)}</span>
                {e.target && <span className="feed-target">{String(e.target)}</span>}
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  )
}
