import { heatmap, RANGES, type Range } from '@/lib/stats'
import { BarList, RangePicker } from '@/components/admin'
import { HeatmapView } from '@/components/heatmap'

export const dynamic = 'force-dynamic'

export default async function Page({ searchParams }: { searchParams: Promise<{ path?: string; range?: string }> }) {
  const sp = await searchParams
  const range = (sp.range && sp.range in RANGES ? sp.range : '30d') as Range
  const first = heatmap('', range).paths
  const path = sp.path || String(first[0]?.path ?? '/fr')
  const h = heatmap(path, range)
  return (
    <div className="page admin-page">
      <header className="admin-head">
        <div>
          <h1 className="display display-sm">Carte des clics</h1>
          <p className="lede">Chaque point est un clic, placé là où il a eu lieu sur la page (largeur relative, hauteur réelle).</p>
        </div>
        <RangePicker range={range} base="/admin/heatmap" extra={`&path=${encodeURIComponent(path)}`} />
      </header>
      <form className="heat-form" action="/admin/heatmap">
        <input type="hidden" name="range" value={range} />
        <label>Page
          <select name="path" defaultValue={path}>
            {!h.paths.some((p) => p.path === path) && <option value={path}>{path}</option>}
            {h.paths.map((p) => <option key={String(p.path)} value={String(p.path)}>{String(p.path)} ({String(p.n)} clics)</option>)}
          </select>
        </label>
        <button className="btn btn-primary" type="submit">Afficher</button>
      </form>
      <div className="heat-layout">
        <HeatmapView path={path} points={h.points} />
        <BarList title="Cibles les plus cliquées" rows={h.targets.map((t, i) => ({ key: String(i), label: String(t.target), n: Number(t.n) }))} />
      </div>
    </div>
  )
}
