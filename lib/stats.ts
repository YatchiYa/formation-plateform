import { db } from './db'

export const RANGES = { '24h': 864e5, '7d': 7 * 864e5, '30d': 30 * 864e5, '90d': 90 * 864e5 } as const
export type Range = keyof typeof RANGES

type Row = Record<string, number | string | null>
// node:sqlite returns null-prototype rows; spread them into plain objects so they can cross to client components.
const all = (sql: string, ...p: (number | string)[]) => db().prepare(sql).all(...p).map((r) => ({ ...r })) as Row[]
const one = (sql: string, ...p: (number | string)[]) => ({ ...db().prepare(sql).get(...p) }) as Row

function kpis(from: number, to: number) {
  const r = one(`SELECT
      SUM(type='pageview') views,
      COUNT(DISTINCT CASE WHEN type='pageview' THEN visitor END) visitors,
      COUNT(DISTINCT CASE WHEN type='pageview' THEN session END) sessions,
      SUM(type='click') clicks,
      SUM(type='download') downloads,
      AVG(CASE WHEN type='leave' AND value BETWEEN 1 AND 3600 THEN value END) avgTime,
      AVG(CASE WHEN type='leave' THEN x END) avgScroll
    FROM events WHERE ts >= ? AND ts < ?`, from, to)
  return Object.fromEntries(Object.entries(r).map(([k, v]) => [k, Number(v ?? 0)])) as Record<'views' | 'visitors' | 'sessions' | 'clicks' | 'downloads' | 'avgTime' | 'avgScroll', number>
}

export function overview(range: Range) {
  const now = Date.now()
  const span = RANGES[range]
  const from = now - span
  const hourly = range === '24h'
  const bucket = hourly ? `strftime('%Y-%m-%d %H:00', ts/1000, 'unixepoch')` : `date(ts/1000, 'unixepoch')`

  // Fill empty buckets so the chart has a continuous time axis.
  const raw = new Map(all(`SELECT ${bucket} b, SUM(type='pageview') views, COUNT(DISTINCT CASE WHEN type='pageview' THEN visitor END) visitors FROM events WHERE ts >= ? GROUP BY b`, from).map((r) => [String(r.b), r]))
  const series: { b: string; views: number; visitors: number }[] = []
  const step = hourly ? 36e5 : 864e5
  for (let t = from - (from % step) + step; t <= now + 1; t += step) {
    const iso = new Date(t).toISOString()
    const b = hourly ? `${iso.slice(0, 10)} ${iso.slice(11, 13)}:00` : iso.slice(0, 10)
    const r = raw.get(b)
    series.push({ b, views: Number(r?.views ?? 0), visitors: Number(r?.visitors ?? 0) })
  }

  const referrers = new Map<string, number>()
  for (const r of all(`SELECT referrer, COUNT(*) n FROM events WHERE type='pageview' AND ts >= ? AND referrer IS NOT NULL GROUP BY referrer`, from)) {
    let host = 'direct'
    try { host = new URL(String(r.referrer)).host.replace(/^www\./, '') } catch {}
    referrers.set(host, (referrers.get(host) ?? 0) + Number(r.n))
  }

  return {
    now: kpis(from, now),
    prev: kpis(from - span, from),
    live: Number(one(`SELECT COUNT(DISTINCT visitor) n FROM events WHERE ts >= ?`, now - 5 * 6e4).n),
    series,
    pages: all(`SELECT path, SUM(type='pageview') views, COUNT(DISTINCT CASE WHEN type='pageview' THEN visitor END) visitors,
        AVG(CASE WHEN type='leave' AND value BETWEEN 1 AND 3600 THEN value END) avgTime, AVG(CASE WHEN type='leave' THEN x END) scroll,
        SUM(type='click') clicks
      FROM events WHERE ts >= ? AND type IN ('pageview','leave','click') GROUP BY path HAVING views > 0 ORDER BY views DESC LIMIT 25`, from),
    clicks: all(`SELECT target, path, COUNT(*) n FROM events WHERE type='click' AND ts >= ? GROUP BY target, path ORDER BY n DESC LIMIT 20`, from),
    outbound: all(`SELECT href, COUNT(*) n FROM events WHERE type='click' AND ts >= ? AND href LIKE 'http%' GROUP BY href ORDER BY n DESC LIMIT 15`, from),
    downloads: all(`SELECT path, COUNT(*) n FROM events WHERE type='download' AND ts >= ? GROUP BY path ORDER BY n DESC LIMIT 15`, from),
    referrers: [...referrers].sort((a, b) => b[1] - a[1]).slice(0, 10),
    locales: all(`SELECT COALESCE(locale,'?') k, COUNT(*) n FROM events WHERE type='pageview' AND ts >= ? GROUP BY k ORDER BY n DESC`, from),
    devices: all(`SELECT COALESCE(device,'?') k, COUNT(DISTINCT visitor) n FROM events WHERE type='pageview' AND ts >= ? GROUP BY k ORDER BY n DESC`, from),
    browsers: all(`SELECT COALESCE(browser,'?') k, COUNT(DISTINCT visitor) n FROM events WHERE type='pageview' AND ts >= ? GROUP BY k ORDER BY n DESC`, from),
    countries: all(`SELECT COALESCE(country,'—') k, COUNT(DISTINCT visitor) n FROM events WHERE type='pageview' AND ts >= ? GROUP BY k ORDER BY n DESC LIMIT 10`, from),
    completions: all(`SELECT item, SUM(status='completed') done, COUNT(*) readers FROM progress WHERE updated >= ? GROUP BY item ORDER BY readers DESC LIMIT 15`, from),
    recent: all(`SELECT ts, type, path, target, device, locale FROM events ORDER BY id DESC LIMIT 25`),
  }
}

export function heatmap(path: string, range: Range) {
  const from = Date.now() - RANGES[range]
  return {
    points: all(`SELECT x, y, vw, dh FROM events WHERE type='click' AND path = ? AND ts >= ? AND x IS NOT NULL ORDER BY id DESC LIMIT 5000`, path, from) as { x: number; y: number; vw: number; dh: number }[],
    paths: all(`SELECT path, COUNT(*) n FROM events WHERE type='click' AND ts >= ? GROUP BY path ORDER BY n DESC LIMIT 50`, from),
    targets: all(`SELECT target, COUNT(*) n FROM events WHERE type='click' AND path = ? AND ts >= ? GROUP BY target ORDER BY n DESC LIMIT 15`, path, from),
  }
}
