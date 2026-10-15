import fs from 'node:fs'
import path from 'node:path'
import { zipSync } from 'fflate'
import { getTree, localized } from '@/lib/content'
import { recordServerEvent } from '@/lib/track'

function addDir(dir: string, base: string, out: Record<string, Uint8Array>) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue
    const abs = path.join(dir, e.name)
    if (e.isDirectory()) addDir(abs, `${base}${e.name}/`, out)
    else out[base + e.name] = fs.readFileSync(abs)
  }
}

/** Download a whole topic / course / article folder as a zip, exactly as authored. */
export async function GET(req: Request, ctx: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await ctx.params
  const node = getTree().byUrl.get('/' + slug.join('/'))
  if (!node || node.kind === 'lesson' || node.kind === 'module' || localized(node, 'fr').meta.access === 'premium' && process.env.PREMIUM_GATE === 'on')
    return new Response('Not found', { status: 404 })
  const files: Record<string, Uint8Array> = {}
  const name = path.basename(node.dir)
  // Loose-file articles live inside their category folder: zip only that file.
  const docs = Object.values(node.docs)
  const loose = docs.length > 0 && !/^(index|README)(\.[a-z]{2})?\.mdx?$/.test(path.basename(docs[0]!.file))
  if (loose) {
    for (const d of docs) files[path.basename(d!.file)] = fs.readFileSync(d!.file)
  } else addDir(node.dir, `${name}/`, files)
  // ponytail: in-memory zip, fine up to a few hundred MB per folder; switch to a streaming zip for bigger trees.
  const zip = zipSync(files, { level: 6 })
  recordServerEvent(req, 'download', `/api/download/${slug.join('/')}`)
  const fname = `${node.path.at(-1) ?? 'catalogue'}.zip`
  return new Response(zip as unknown as BodyInit, {
    headers: { 'Content-Type': 'application/zip', 'Content-Disposition': `attachment; filename="${fname}"`, 'Content-Length': String(zip.length) },
  })
}
