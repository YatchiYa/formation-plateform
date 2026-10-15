import { record, type TrackEvent } from '@/lib/track'

export async function POST(req: Request) {
  let body: unknown
  try { body = JSON.parse(await req.text()) } catch { return new Response('Bad JSON', { status: 400 }) }
  const events = (Array.isArray(body) ? body : [body]) as TrackEvent[]
  return Response.json({ stored: record(req, events) })
}
