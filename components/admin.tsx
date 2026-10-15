import Link from 'next/link'
import { RANGES, type Range } from '@/lib/stats'

export const fmt = (n: number) => new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n)
export const dur = (s: number) => (s >= 60 ? `${Math.floor(s / 60)} min ${Math.round(s % 60)} s` : `${Math.round(s)} s`)

export function RangePicker({ range, base, extra = '' }: { range: Range; base: string; extra?: string }) {
  return (
    <div className="filter-group" role="group" aria-label="Période">
      {(Object.keys(RANGES) as Range[]).map((r) => (
        <Link key={r} href={`${base}?range=${r}${extra}`} className={`chip ${r === range ? 'on' : ''}`} aria-current={r === range ? 'true' : undefined}>{r}</Link>
      ))}
    </div>
  )
}

export function Kpi({ label, value, prev, display }: { label: string; value: number; prev?: number; display?: string }) {
  const delta = prev !== undefined && prev > 0 ? Math.round(((value - prev) / prev) * 100) : null
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{display ?? fmt(value)}</span>
      {delta !== null && <span className={`kpi-delta ${delta >= 0 ? 'up' : 'down'}`}>{delta >= 0 ? '▲' : '▼'} {Math.abs(delta)} % vs période précédente</span>}
    </div>
  )
}

/** Page views as bars, unique visitors as a line, on one shared count axis. Hover a column for exact values. */
export function TrafficChart({ series, hourly }: { series: { b: string; views: number; visitors: number }[]; hourly: boolean }) {
  const W = 960, H = 260, pl = 40, pr = 12, pt = 16, pb = 28
  const max = Math.max(4, ...series.map((s) => Math.max(s.views, s.visitors)))
  const nice = Math.ceil(max / 4) * 4
  const iw = W - pl - pr, ih = H - pt - pb
  const bw = iw / series.length
  const y = (v: number) => pt + ih - (v / nice) * ih
  const label = (b: string) => (hourly ? b.slice(11, 13) + 'h' : new Date(b).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }))
  const every = Math.ceil(series.length / 8)
  const line = series.map((s, i) => `${i ? 'L' : 'M'}${pl + bw * i + bw / 2},${y(s.visitors)}`).join(' ')
  return (
    <figure className="chart">
      <div className="legend">
        <span><i className="sw sw-1" /> Pages vues</span>
        <span><i className="sw sw-2 sw-line" /> Visiteurs uniques</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Trafic sur la période">
        {[0, 1, 2, 3, 4].map((k) => (
          <g key={k}>
            <line x1={pl} x2={W - pr} y1={y((nice / 4) * k)} y2={y((nice / 4) * k)} className="grid" />
            <text x={pl - 8} y={y((nice / 4) * k) + 4} className="axis" textAnchor="end">{fmt((nice / 4) * k)}</text>
          </g>
        ))}
        {series.map((s, i) => {
          const h = (s.views / nice) * ih
          const x = pl + bw * i + Math.max(1, bw * 0.15)
          const w = Math.max(2, bw * 0.7)
          return (
            <g key={s.b} className="col">
              <rect className="hit" x={pl + bw * i} y={pt} width={bw} height={ih} />
              {h > 0 && <path className="bar" d={`M${x},${pt + ih} v${-Math.max(0, h - 4)} q0,-4 4,-4 h${w - 8} q4,0 4,4 v${Math.max(0, h - 4)} z`} />}
              <title>{`${label(s.b)} — ${s.views} pages vues, ${s.visitors} visiteurs`}</title>
              {i % every === 0 && <text x={pl + bw * i + bw / 2} y={H - 8} className="axis" textAnchor="middle">{label(s.b)}</text>}
            </g>
          )
        })}
        <path d={line} className="line" />
        {series.map((s, i) => s.visitors > 0 && <circle key={s.b} cx={pl + bw * i + bw / 2} cy={y(s.visitors)} r={4} className="dot" />)}
      </svg>
      <details className="chart-table">
        <summary>Voir les données</summary>
        <table><thead><tr><th>Période</th><th>Pages vues</th><th>Visiteurs</th></tr></thead>
          <tbody>{series.filter((s) => s.views).map((s) => <tr key={s.b}><td>{s.b}</td><td>{s.views}</td><td>{s.visitors}</td></tr>)}</tbody></table>
      </details>
    </figure>
  )
}

export function BarList({ title, rows, empty = 'Aucune donnée sur la période.' }: { title: string; rows: { label: React.ReactNode; n: number; sub?: React.ReactNode; key: string }[]; empty?: string }) {
  const max = Math.max(1, ...rows.map((r) => r.n))
  return (
    <section className="panel">
      <h2 className="panel-title">{title}</h2>
      {rows.length ? (
        <ul className="barlist">
          {rows.map((r) => (
            <li key={r.key}>
              <span className="barlist-fill" style={{ width: `${(r.n / max) * 100}%` }} />
              <span className="barlist-label">{r.label}{r.sub && <small>{r.sub}</small>}</span>
              <span className="barlist-n">{fmt(r.n)}</span>
            </li>
          ))}
        </ul>
      ) : <p className="empty">{empty}</p>}
    </section>
  )
}
