import { getTree } from '@/lib/content'
import { db } from '@/lib/db'

export const dynamic = 'force-dynamic'
export function GET() {
  db().prepare('SELECT 1').get()
  return Response.json({ ok: true, nodes: getTree().all.length })
}
