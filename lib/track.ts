import { db, deviceOf, isBot } from './db'
import { VISITOR_COOKIE } from './constants'

export interface TrackEvent {
  type: 'pageview' | 'click' | 'leave' | 'download'
  path: string
  session?: string
  locale?: string
  referrer?: string
  x?: number; y?: number; vw?: number; dh?: number
  target?: string; href?: string
  value?: number
}

const cookie = (req: Request, name: string) =>
  (req.headers.get('cookie') || '').split(/;\s*/).find((c) => c.startsWith(name + '='))?.slice(name.length + 1)

const clip = (v: unknown, n: number) => (v == null ? null : String(v).slice(0, n))
const num = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? v : null)

export function record(req: Request, events: TrackEvent[]) {
  const ua = req.headers.get('user-agent') || ''
  if (isBot(ua) || req.headers.get('dnt') === '1') return 0
  const visitor = cookie(req, VISITOR_COOKIE)
  if (!visitor) return 0
  const { device, browser } = deviceOf(ua)
  const country = req.headers.get('cf-ipcountry') || req.headers.get('x-vercel-ip-country') || req.headers.get('x-country') || null
  const now = Date.now()
  const d = db()
  const ins = d.prepare(`INSERT INTO events (ts,type,visitor,session,path,locale,referrer,device,browser,country,x,y,vw,dh,target,href,value)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`)
  let n = 0
  for (const e of events.slice(0, 50)) {
    if (!['pageview', 'click', 'leave', 'download'].includes(e.type) || typeof e.path !== 'string') continue
    ins.run(now, e.type, visitor, clip(e.session, 64), clip(e.path, 512)!, clip(e.locale, 8), clip(e.referrer, 512), device, browser, country,
      num(e.x), num(e.y), num(e.vw), num(e.dh), clip(e.target, 200), clip(e.href, 512), num(e.value))
    n++
  }
  d.prepare(`INSERT INTO visitors (id, first_seen, last_seen) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET last_seen = excluded.last_seen`).run(visitor, now, now)
  return n
}

export function recordServerEvent(req: Request, type: 'download', path: string) {
  try { record(req, [{ type, path: decodeURIComponent(path), referrer: req.headers.get('referer') || undefined }]) } catch { /* analytics never breaks a download */ }
}
