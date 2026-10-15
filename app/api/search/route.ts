import { gzipSync } from 'node:zlib'
import { searchIndex } from '@/lib/catalog'
import { defaultLocale, isLocale } from '@/lib/i18n'

export const dynamic = 'force-dynamic'
export function GET(req: Request) {
  const l = new URL(req.url).searchParams.get('locale') || ''
  const body = JSON.stringify(searchIndex(isLocale(l) ? l : defaultLocale))
  const headers: Record<string, string> = { 'Content-Type': 'application/json', 'Cache-Control': 'private, max-age=30', Vary: 'Accept-Encoding' }
  // The index is a few hundred KB of text: gzip it (~5x smaller) when the client allows.
  if (/\bgzip\b/.test(req.headers.get('accept-encoding') || '')) {
    return new Response(gzipSync(body), { headers: { ...headers, 'Content-Encoding': 'gzip' } })
  }
  return new Response(body, { headers })
}
