import fs from 'node:fs'
import path from 'node:path'
import { Readable } from 'node:stream'
import { safeContentPath } from '@/lib/content'
import { recordServerEvent } from '@/lib/track'

const TYPES: Record<string, string> = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.avif': 'image/avif',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.pdf': 'application/pdf', '.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime',
  '.m4v': 'video/mp4', '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  '.zip': 'application/zip', '.csv': 'text/csv; charset=utf-8', '.json': 'application/json', '.ipynb': 'application/x-ipynb+json',
  '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.html': 'text/html; charset=utf-8',
}
// Source files open as readable text in the browser instead of downloading.
const TEXT = /\.(py|tf|tfvars\.example|hcl|sh|ya?ml|toml|ts|tsx|js|mjs|json|ini|cfg|sql|rego|go|rs|java|env\.example|txt|log|csv)$|(^|\/)(Dockerfile|Makefile|requirements\.txt)$/i

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)

/** Plain directory listing so links to code folders (`terraform/`, `scripts/`) stay browsable. */
function listing(dir: string, urlPath: string) {
  const base = urlPath.endsWith('/') ? urlPath : urlPath + '/'
  const rows = fs.readdirSync(dir, { withFileTypes: true })
    .filter((e) => !e.name.startsWith('.') || e.name === '.gitignore' || e.name === '.dockerignore')
    .sort((a, b) => Number(b.isDirectory()) - Number(a.isDirectory()) || a.name.localeCompare(b.name, undefined, { numeric: true }))
    .map((e) => `<li><a href="${esc(base + encodeURIComponent(e.name))}">${e.isDirectory() ? '📁' : '📄'} ${esc(e.name)}${e.isDirectory() ? '/' : ''}</a></li>`)
    .join('')
  const title = esc(decodeURIComponent(base.replace(/^\/files\//, '')))
  const html = `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title>
<style>body{font:15px/1.6 system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 16px;background:#f3f5f2;color:#16202a}
@media(prefers-color-scheme:dark){body{background:#121a22;color:#e6ebee}a{color:#91a4ff}}ul{list-style:none;padding:0}li{border-bottom:1px solid #8883;padding:6px 0}
a{text-decoration:none;color:#2b45c8}code{font:13px ui-monospace,monospace}</style>
<p><a href="${esc(base + '..')}">↑ ..</a></p><h1><code>${title}</code></h1><ul>${rows}</ul>`
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'" } })
}

export async function GET(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const abs = safeContentPath((await ctx.params).path)
  if (!abs || !fs.existsSync(abs)) return new Response('Not found', { status: 404 })
  if (fs.statSync(abs).isDirectory()) return listing(abs, new URL(req.url).pathname)
  const { size, mtimeMs } = fs.statSync(abs)
  const ext = path.extname(abs).toLowerCase()
  const url = new URL(req.url)
  const headers: Record<string, string> = {
    'Content-Type': TYPES[ext] ?? (TEXT.test(abs) ? 'text/plain; charset=utf-8' : 'application/octet-stream'),
    'Accept-Ranges': 'bytes',
    'Cache-Control': 'public, max-age=300',
    'Last-Modified': new Date(mtimeMs).toUTCString(),
    'X-Content-Type-Options': 'nosniff',
  }
  // SVGs are served as images only; block script execution if opened directly.
  if (ext === '.svg') headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'"
  // Authored HTML pages run in a sandbox: own opaque origin, no access to the site's cookies.
  if (ext === '.html') headers['Content-Security-Policy'] = 'sandbox allow-scripts allow-popups allow-forms'
  if (url.searchParams.has('dl')) {
    headers['Content-Disposition'] = `attachment; filename*=UTF-8''${encodeURIComponent(path.basename(abs))}`
    recordServerEvent(req, 'download', url.pathname)
  }

  // Range requests let the browser seek in videos.
  const m = /bytes=(\d*)-(\d*)/.exec(req.headers.get('range') || '')
  if (m) {
    const start = m[1] ? Number(m[1]) : Math.max(0, size - Number(m[2]))
    const end = m[1] && m[2] ? Math.min(Number(m[2]), size - 1) : size - 1
    if (start >= size || start > end) return new Response(null, { status: 416, headers: { 'Content-Range': `bytes */${size}` } })
    return new Response(Readable.toWeb(fs.createReadStream(abs, { start, end })) as ReadableStream, {
      status: 206,
      headers: { ...headers, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': String(end - start + 1) },
    })
  }
  return new Response(Readable.toWeb(fs.createReadStream(abs)) as ReadableStream, { headers: { ...headers, 'Content-Length': String(size) } })
}
