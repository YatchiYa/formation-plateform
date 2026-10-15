import { cookies } from 'next/headers'
import { db } from '@/lib/db'
import { VISITOR_COOKIE } from '@/lib/constants'

export const dynamic = 'force-dynamic'

async function visitor() {
  return (await cookies()).get(VISITOR_COOKIE)?.value ?? null
}

export async function GET() {
  const v = await visitor()
  if (!v) return Response.json({ items: [] })
  const items = db().prepare('SELECT item, course, status, pct, updated FROM progress WHERE visitor = ? ORDER BY updated DESC LIMIT 500').all(v)
  return Response.json({ items })
}

export async function POST(req: Request) {
  const v = await visitor()
  if (!v) return Response.json({ ok: false }, { status: 400 })
  const { item, course, status, pct } = (await req.json()) as { item?: string; course?: string; status?: string; pct?: number }
  if (typeof item !== 'string' || !item.startsWith('/') || item.length > 512) return Response.json({ ok: false }, { status: 400 })
  const st = status === 'completed' ? 'completed' : 'started'
  const p = Math.max(0, Math.min(100, Math.round(Number(pct) || 0)))
  // "completed" is sticky: scrolling back up never downgrades a finished lesson.
  db().prepare(`INSERT INTO progress (visitor, item, course, status, pct, updated) VALUES (?,?,?,?,?,?)
    ON CONFLICT(visitor, item) DO UPDATE SET
      status = CASE WHEN progress.status = 'completed' THEN 'completed' ELSE excluded.status END,
      pct = MAX(progress.pct, excluded.pct), updated = excluded.updated, course = COALESCE(excluded.course, progress.course)`)
    .run(v, item, typeof course === 'string' ? course.slice(0, 512) : null, st, st === 'completed' ? 100 : p, Date.now())
  return Response.json({ ok: true })
}
