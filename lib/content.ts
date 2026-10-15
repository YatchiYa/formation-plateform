import fs from 'node:fs'
import path from 'node:path'
import matter from 'gray-matter'
import { defaultLocale, locales, type Locale } from './i18n'

export const CONTENT_DIR = path.resolve(process.env.CONTENT_DIR || path.join(/* turbopackIgnore: true */ process.cwd(), 'content'))
const RESERVED = new Set(['images', 'assets', 'files', 'node_modules'])
const DOC_EXT = new Set(['.example', '.html', '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.csv', '.zip', '.ipynb', '.json', '.txt', '.mp4', '.webm', '.mp3', '.py', '.ts', '.js', '.sh', '.tf', '.yaml', '.yml', '.odt', '.odp', '.epub', '.key'])

export type Kind = 'category' | 'course' | 'article' | 'module' | 'lesson'

export interface Reference { title: string; url: string; note?: string; kind: 'github' | 'video' | 'paper' | 'docs' | 'article' }
export interface Meta {
  title: string
  description?: string
  icon?: string
  cover?: string
  tags: string[]
  level?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  duration?: string
  date?: string
  updated?: string
  authors: string[]
  access: 'public' | 'premium'
  draft: boolean
  slides: boolean
  /** Declared `type:` (skill, video, link, slides...) — the format is derived from it, see formatOf(). */
  type?: string
  /** video: the video URL (YouTube, Vimeo or a local file) */
  video?: string
  /** link: the external resource it points to */
  link?: string
  /** skill: phrases that trigger it, parsed from its description */
  triggers: string[]
  /** Slugs of platform / use-case pages this content relates to */
  platforms: string[]
  usecases: string[]
  order?: number
  references: Reference[]
}
export interface Doc { file: string; locale: Locale; meta: Meta; body: string }
export interface Asset { name: string; url: string; ext: string; size: number }
export interface Node {
  kind: Kind
  /** URL segments under /[locale]/ */
  path: string[]
  url: string
  dir: string
  order: number
  docs: Partial<Record<Locale, Doc>>
  children: Node[]
  files: Asset[]
  parent?: Node
  /** course only: lessons in reading order */
  lessons?: Node[]
  mtime: number
}

const splitPrefix = (name: string) => {
  const m = /^(\d+)[-_.\s]+(.*)$/.exec(name)
  return m ? { order: Number(m[1]), rest: m[2] } : { order: 9999, rest: name }
}
export const slugify = (s: string) =>
  s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'x'
const humanize = (s: string) => {
  const t = s.replace(/[-_]+/g, ' ').trim()
  return t.charAt(0).toUpperCase() + t.slice(1)
}
const toDate = (v: unknown) => (v instanceof Date ? v.toISOString().slice(0, 10) : v ? String(v) : undefined)
const list = (v: unknown) => (Array.isArray(v) ? v.map(String) : v ? String(v).split(',').map((s) => s.trim()) : [])

export const fileUrl = (abs: string) =>
  '/files/' + path.relative(CONTENT_DIR, abs).split(path.sep).map(encodeURIComponent).join('/')

function refKind(url: string): Reference['kind'] {
  if (/github\.com|gitlab\.com/.test(url)) return 'github'
  if (/youtube\.com|youtu\.be|vimeo\.com/.test(url)) return 'video'
  if (/arxiv\.org|\.pdf($|\?)|doi\.org/.test(url)) return 'paper'
  if (/docs\.|\/docs\//.test(url)) return 'docs'
  return 'article'
}

/**
 * Agent-skill descriptions pack "what it does. Use whenever ... Triggers - a, b, c" into one string:
 * keep the first part as the description and expose the trigger phrases separately.
 */
function skillDescription(file: string, desc?: string): { description?: string; triggers: string[] } {
  if (!desc || !path.basename(file).startsWith('SKILL.')) return { description: desc, triggers: [] }
  const trig = /\s*Triggers?\s*[-:–]\s*(.+)$/i.exec(desc)
  const rest = trig ? desc.slice(0, trig.index) : desc
  const short = rest.split(/\s+(?=Use (?:it )?when(?:ever)?\b)/)[0].trim()
  return { description: short, triggers: trig ? trig[1].replace(/\.$/, '').split(/\s*,\s*/).filter(Boolean).slice(0, 30) : [] }
}

function readDoc(file: string, locale: Locale, fallbackTitle: string, dir: string): Doc {
  const raw = fs.readFileSync(file, 'utf8')
  let parsed: matter.GrayMatterFile<string>
  try {
    parsed = matter(raw)
  } catch (e) {
    // Broken frontmatter must not take the whole site down: show the error in the page.
    parsed = { data: {}, content: `> [!CAUTION]\n> Frontmatter invalide dans \`${path.basename(file)}\` : ${(e as Error).message}\n\n${raw}` } as never
  }
  const d = parsed.data as Record<string, unknown>
  let body = parsed.content
  let title = d.title ? String(d.title) : ''
  if (!title) {
    // First "# heading" doubles as title and is removed from the body to avoid showing it twice.
    const h = /^\s*#\s+(.+)\n?/.exec(body)
    if (h) { title = h[1].trim(); body = body.slice(h[0].length) }
  }
  const cover = d.cover ? String(d.cover) : undefined
  return {
    file,
    locale,
    body,
    meta: {
      title: title || fallbackTitle,
      ...skillDescription(file, d.description ? String(d.description) : undefined),
      icon: d.icon ? String(d.icon) : undefined,
      cover: cover && !/^https?:/.test(cover) ? fileUrl(path.resolve(dir, cover)) : cover,
      tags: list(d.tags).map((s) => s.toLowerCase()),
      level: ['beginner', 'intermediate', 'advanced', 'expert'].includes(String(d.level)) ? (d.level as Meta['level']) : undefined,
      duration: d.duration ? String(d.duration) : undefined,
      date: toDate(d.date),
      updated: toDate(d.updated),
      authors: list(d.authors ?? d.author),
      access: d.access === 'premium' ? 'premium' : 'public',
      draft: d.draft === true,
      slides: d.type === 'slides' || d.slides === true,
      type: d.type ? String(d.type) : path.basename(file).startsWith('SKILL.') ? 'skill' : undefined,
      video: d.video ? String(d.video) : undefined,
      platforms: list(d.platforms).map(slugify),
      usecases: list(d.usecases ?? d.usecase).map(slugify),
      link: d.url ? String(d.url) : d.link ? String(d.link) : undefined,
      order: typeof d.order === 'number' ? d.order : undefined,
      references: (Array.isArray(d.references) ? d.references : [])
        .map((r) => (typeof r === 'string' ? { url: r } : r) as Record<string, unknown>)
        .filter((r) => r && r.url)
        .map((r) => ({ title: String(r.title || r.url), url: String(r.url), note: r.note ? String(r.note) : undefined, kind: refKind(String(r.url)) })),
    },
  }
}

/** `intro.en.md` -> { base: 'intro', locale: 'en' } */
function parseMdName(name: string): { base: string; locale: Locale } | null {
  if (!name.endsWith('.md') && !name.endsWith('.mdx')) return null
  const stem = name.replace(/\.mdx?$/, '')
  const m = /^(.*)\.([a-z]{2})$/.exec(stem)
  if (m && (locales as readonly string[]).includes(m[2])) return { base: m[1], locale: m[2] as Locale }
  return { base: stem, locale: defaultLocale }
}

const isHidden = (n: string) => n.startsWith('.') || n.startsWith('_')

function collectFiles(dir: string, recurseReserved: boolean): Asset[] {
  const out: Asset[] = []
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (isHidden(e.name) && !SAFE_DOTFILES.has(e.name)) continue
    const abs = path.join(dir, e.name)
    if (e.isDirectory()) {
      if (recurseReserved && (e.name === 'files' || e.name === 'assets')) out.push(...collectFiles(abs, false))
      continue
    }
    const ext = path.extname(e.name).toLowerCase()
    // Markdown is a page at the top level, but a download inside files/ (e.g. a skill to upload).
    if (!DOC_EXT.has(ext) && !(ext === '.md' && !recurseReserved)) continue
    out.push({ name: e.name, url: fileUrl(abs), ext: ext.slice(1), size: fs.statSync(abs).size })
  }
  return out.sort((a, b) => a.name.localeCompare(b.name))
}

type Entry = { name: string; abs: string; isDir: boolean }

/** Group `x.md`, `x.en.md` ... into one localized doc set. */
function groupMd(entries: Entry[]) {
  const groups = new Map<string, Partial<Record<Locale, string>>>()
  for (const e of entries) {
    if (e.isDir) continue
    const p = parseMdName(e.name)
    if (!p) continue
    const g = groups.get(p.base) ?? {}
    g[p.locale] = e.abs
    groups.set(p.base, g)
  }
  return groups
}

function docsOf(files: Partial<Record<Locale, string>>, fallbackTitle: string, dir: string) {
  const docs: Partial<Record<Locale, Doc>> = {}
  for (const [l, f] of Object.entries(files)) docs[l as Locale] = readDoc(f!, l as Locale, fallbackTitle, dir)
  // A translation without its own metadata inherits the original's (tags, level, refs...).
  const base = docs[defaultLocale] ?? Object.values(docs)[0]
  if (base) for (const d of Object.values(docs)) {
    if (d === base) continue
    const own = matter(fs.readFileSync(d!.file, 'utf8')).data as Record<string, unknown>
    for (const k of Object.keys(base.meta) as (keyof Meta)[]) if (!(k in own) && k !== 'title') (d!.meta as unknown as Record<string, unknown>)[k] = base.meta[k]
    if (!own.title && d!.meta.title === fallbackTitle) d!.meta.title = base.meta.title
  }
  return docs
}

const mtimeOf = (files: Partial<Record<Locale, string>>, dir: string) =>
  Math.max(fs.statSync(dir).mtimeMs, ...Object.values(files).map((f) => fs.statSync(f!).mtimeMs))

function leaf(kind: Kind, base: string, files: Partial<Record<Locale, string>>, parentPath: string[], dir: string): Node {
  const { order, rest } = splitPrefix(base)
  const p = [...parentPath, slugify(rest)]
  const docs = docsOf(files, humanize(rest), dir)
  return { kind, path: p, url: '/' + p.join('/'), dir, order: metaOrder(docs) ?? order, docs, children: [], files: [], mtime: mtimeOf(files, dir) }
}

const metaOrder = (docs: Partial<Record<Locale, Doc>>) => (docs[defaultLocale] ?? Object.values(docs)[0])?.meta.order
const metaOf = (n: Node) => (n.docs[defaultLocale] ?? Object.values(n.docs)[0])?.meta

const INDEX_NAMES = ['index', 'README', 'SKILL']
const NON_CONTENT_DIRS = new Set([...RESERVED, 'venv', 'node_modules', '__pycache__', 'dist', 'build'])

/**
 * Every markdown file under a module folder, at any depth, in reading order:
 * the module's README first, then folders and files in natural order (01, 02, ... 10).
 * A nested README/SKILL becomes a lesson named after its folder.
 */
function moduleLessons(moduleDir: string, parentPath: string[]): Node[] {
  const found: { key: string; slug: string; files: Partial<Record<Locale, string>>; dir: string; fallback: string }[] = []
  const walk = (dir: string, rel: string[]) => {
    const es = fs.readdirSync(dir, { withFileTypes: true }).filter((e) => !isHidden(e.name))
    const entries = es.map((e) => ({ name: e.name, abs: path.join(dir, e.name), isDir: e.isDirectory() }))
    for (const [base, files] of groupMd(entries)) {
      if (!rel.length && base === 'index') continue
      const indexLike = INDEX_NAMES.includes(base)
      const relSlug = rel.map((r) => splitPrefix(r).rest).join('-')
      const rest = splitPrefix(base).rest
      found.push({
        key: [...rel, indexLike ? '' : base].join('/'),
        slug: indexLike ? relSlug || 'readme' : [relSlug, rest].filter(Boolean).join('-'),
        files,
        dir,
        fallback: humanize(indexLike ? (rel.at(-1) ? splitPrefix(rel.at(-1)!).rest : path.basename(moduleDir)) : rest),
      })
    }
    for (const e of es) if (e.isDirectory() && !NON_CONTENT_DIRS.has(e.name)) walk(path.join(dir, e.name), [...rel, e.name])
  }
  walk(moduleDir, [])
  found.sort((a, b) => a.key.localeCompare(b.key, undefined, { numeric: true }))
  const used = new Set<string>()
  return found.map((f, i) => {
    const docs = docsOf(f.files, f.fallback, f.dir)
    // Root README: slug from its title (e.g. "kit-rag-google-drive"), unique within the module.
    let slug = slugify(f.slug === 'readme' ? (docs[defaultLocale] ?? Object.values(docs)[0])!.meta.title : f.slug)
    while (used.has(slug)) slug += '-' + i
    used.add(slug)
    const p = [...parentPath, slug]
    return { kind: 'lesson', path: p, url: '/' + p.join('/'), dir: f.dir, order: i, docs, children: [], files: [], mtime: mtimeOf(f.files, f.dir) } as Node
  })
}

/** Lesson container = folder with lesson .md files and no sub-pages of its own. */
function isModuleDir(dir: string) {
  const es = fs.readdirSync(dir, { withFileTypes: true }).filter((e) => !isHidden(e.name))
  const md = es.filter((e) => e.isFile() && parseMdName(e.name) && !INDEX_NAMES.includes(parseMdName(e.name)!.base))
  return md.length > 0 && !es.some((e) => e.isDirectory() && !RESERVED.has(e.name))
}

/**
 * A folder with only sub-folders is a course (sub-folders = modules) when every sub-folder holds
 * lessons and its index.md reads like a course (level, duration, cover or references). Otherwise a category.
 */
function looksLikeModularCourse(indexFile: string | undefined, subdirs: Entry[]) {
  if (!indexFile || !subdirs.length || !subdirs.every((d) => isModuleDir(d.abs))) return false
  const d = matter(fs.readFileSync(indexFile, 'utf8')).data
  return ['level', 'duration', 'cover', 'references'].some((k) => k in d)
}

function readDir(dir: string, parentPath: string[], forced?: Kind): Node | null {
  const name = path.basename(dir)
  const entries: Entry[] = fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => !isHidden(e.name))
    .map((e) => ({ name: e.name, abs: path.join(dir, e.name), isDir: e.isDirectory() }))
  const groups = groupMd(entries)
  // In a module, README/SKILL are lessons (collected below); only index.md holds the module's metadata.
  const index = (forced === 'module' ? groups.get('index') : groups.get('index') ?? groups.get('README') ?? groups.get('SKILL')) ?? {}
  for (const k of INDEX_NAMES) groups.delete(k)
  const subdirs = entries.filter((e) => e.isDir && !RESERVED.has(e.name))
  const { order, rest } = splitPrefix(name)
  const p = [...parentPath, slugify(rest)]
  const isRoot = dir === CONTENT_DIR
  const docs = docsOf(index, isRoot ? 'Catalogue' : humanize(rest), dir)
  const indexFile = index[defaultLocale] ?? Object.values(index)[0]
  const declared = indexFile ? (matter(fs.readFileSync(indexFile, 'utf8')).data.type as string | undefined) : undefined

  let kind: Kind
  if (forced === 'module') kind = 'module'
  else if (isRoot || declared === 'category') kind = 'category'
  else if (declared === 'course') kind = 'course'
  else if (declared && ['article', 'slides', 'skill', 'video', 'link', 'platform', 'usecase'].includes(declared)) kind = 'article'
  else if (groups.size > 0 || looksLikeModularCourse(indexFile, subdirs)) kind = 'course'
  else if (subdirs.length > 0) kind = 'category'
  else kind = 'article'

  const node: Node = {
    kind, path: isRoot ? [] : p, url: isRoot ? '/' : '/' + p.join('/'), dir, order: metaOrder(docs) ?? order, docs, children: [], files: [],
    mtime: Object.keys(index).length ? mtimeOf(index, dir) : fs.statSync(dir).mtimeMs,
  }
  const add = (c: Node | null) => {
    if (!c || metaOf(c)?.draft) return
    c.parent = node
    node.children.push(c)
  }

  if (kind === 'category') {
    for (const [base, files] of groups) add(leaf('article', base, files, node.path, dir))
    for (const d of subdirs) add(readDir(d.abs, node.path))
  } else if (kind === 'course') {
    for (const [base, files] of groups) add(leaf('lesson', base, files, node.path, dir))
    for (const d of subdirs) add(readDir(d.abs, node.path, 'module'))
  } else if (kind === 'module') {
    moduleLessons(dir, node.path).forEach(add)
  }
  if (kind === 'course' || kind === 'article') node.files = collectFiles(dir, true)
  // Modules keep the reading order computed by moduleLessons; elsewhere: prefix number, then natural name order.
  if (kind !== 'module') node.children.sort((a, b) => a.order - b.order || a.path.at(-1)!.localeCompare(b.path.at(-1)!, undefined, { numeric: true }))
  if (kind === 'course') node.lessons = node.children.flatMap((c) => (c.kind === 'module' ? c.children : [c]))
  if (kind === 'module' && node.children.length === 0) return null
  if (!isRoot && kind === 'category' && node.children.length === 0) return null
  return node
}

export interface Tree { root: Node; byUrl: Map<string, Node>; byFile: Map<string, Node>; all: Node[]; version: number }

let cache: { at: number; tree: Tree } | null = null
const TTL = Number(process.env.CONTENT_CACHE_MS ?? 1500)

/** Scans content/ on demand (cheap) so a new folder shows up without rebuild or restart. */
export function getTree(): Tree {
  if (cache && Date.now() - cache.at < TTL) return cache.tree
  const root = fs.existsSync(/* turbopackIgnore: true */ CONTENT_DIR) ? readDir(CONTENT_DIR, [], 'category')! : ({ kind: 'category', path: [], url: '/', dir: CONTENT_DIR, order: 0, docs: {}, children: [], files: [], mtime: 0 } as Node)
  const byUrl = new Map<string, Node>()
  const byFile = new Map<string, Node>()
  const all: Node[] = []
  const walk = (n: Node) => {
    byUrl.set(n.url, n)
    all.push(n)
    for (const d of Object.values(n.docs)) byFile.set(d!.file, n)
    n.children.forEach(walk)
  }
  walk(root)
  const version = Math.max(0, ...all.map((n) => n.mtime))
  cache = { at: Date.now(), tree: { root, byUrl, byFile, all, version } }
  return cache.tree
}

export function localized(n: Node, l: Locale): Doc & { translated: boolean } {
  const d = n.docs[l] ?? n.docs[defaultLocale] ?? Object.values(n.docs)[0]
  if (!d) return { file: '', locale: l, body: '', meta: emptyMeta(n), translated: true }
  return { ...d, translated: d.locale === l }
}
function emptyMeta(n: Node): Meta {
  const raw = n === getTree().root ? 'Catalogue' : humanize(splitPrefix(path.basename(n.dir)).rest)
  return { title: raw, tags: [], authors: [], access: 'public', draft: false, slides: false, triggers: [], platforms: [], usecases: [], references: [] }
}

export const FORMATS = ['course', 'article', 'slides', 'skill', 'video', 'link', 'usecase', 'platform'] as const
export type Format = (typeof FORMATS)[number]
/** What the learner sees a piece of content as. Structure (kind) and format are separate: a skill is an article-shaped page. */
export function formatOf(n: Node, meta: Meta): Format | 'category' | 'module' | 'lesson' {
  if (n.kind === 'course') return 'course'
  if (n.kind !== 'article') return n.kind
  if (meta.type === 'skill') return 'skill'
  if (meta.type === 'platform') return 'platform'
  if (meta.type === 'usecase') return 'usecase'
  if (meta.type === 'video' || (meta.video && meta.type !== 'link')) return 'video'
  if (meta.type === 'link' || meta.link) return 'link'
  if (meta.slides) return 'slides'
  return 'article'
}

/** Platform / use-case hub pages by slug, and the content that points to each. */
export function hubs(t: Tree) {
  const by = { platform: new Map<string, Node>(), usecase: new Map<string, Node>() }
  for (const n of items(t)) {
    const m = localized(n, defaultLocale).meta
    const f = formatOf(n, m)
    if (f === 'platform' || f === 'usecase') by[f].set(n.path.at(-1)!, n)
  }
  const related = (kind: 'platform' | 'usecase', slug: string) =>
    items(t).filter((n) => localized(n, defaultLocale).meta[kind === 'platform' ? 'platforms' : 'usecases'].includes(slug))
  return { ...by, related }
}

/** Publishable items = what a learner opens (no categories/modules/lessons). */
export const items = (t: Tree) => t.all.filter((n) => n.kind === 'course' || n.kind === 'article')
export const courseOf = (n: Node): Node | undefined => (n.kind === 'course' ? n : n.parent ? courseOf(n.parent) : undefined)
export const crumbs = (n: Node) => {
  const out: Node[] = []
  for (let c: Node | undefined = n.parent; c; c = c.parent) out.unshift(c)
  return out
}
export const countItems = (n: Node): number =>
  n.kind === 'course' || n.kind === 'article' ? 1 : n.children.reduce((s, c) => s + countItems(c), 0)
export const words = (s: string) => s.split(/\s+/).filter(Boolean).length
export const readingMinutes = (body: string) => Math.max(1, Math.round(words(body) / 200))

/** Strip markdown into rough plain text for search. */
export const plain = (md: string) =>
  md.replace(/```[\s\S]*?```/g, ' ').replace(/!\[[^\]]*\]\([^)]*\)/g, ' ').replace(/\[([^\]]*)\]\([^)]*\)/g, '$1').replace(/[#>*_`|~\-$]+/g, ' ').replace(/\s+/g, ' ').trim()

let filesIndex: { version: number; files: string[] } | null = null
/**
 * Finds the file a broken relative link most likely meant, by its trailing path segments
 * (`../01-adk/README.md` still works after the folder moved into a theme). Longest unique suffix wins.
 */
export function findBySuffix(abs: string): string | null {
  const t = getTree()
  if (!filesIndex || filesIndex.version !== t.version) {
    const files: string[] = []
    const walk = (d: string) => {
      for (const e of fs.readdirSync(d, { withFileTypes: true })) {
        if (e.name.startsWith('.') || e.name === 'node_modules') continue
        const a = path.join(d, e.name)
        if (e.isDirectory()) walk(a)
        else files.push(a)
      }
    }
    walk(CONTENT_DIR)
    filesIndex = { version: t.version, files }
  }
  const segs = abs.split(path.sep).filter(Boolean)
  for (let n = Math.min(4, segs.length); n >= 1; n--) {
    const suffix = path.sep + segs.slice(-n).join(path.sep)
    const hits = filesIndex.files.filter((f) => f.endsWith(suffix) || (f.endsWith(suffix + path.sep + 'README.md')))
    if (hits.length === 1) return hits[0]
    if (hits.length > 1 && n === 1) return null
    if (hits.length > 1) return hits.sort((a, b) => a.length - b.length)[0]
  }
  return null
}

export const SAFE_DOTFILES = new Set(['.gitignore', '.dockerignore', '.env.example', '.env.exemple', '.env.sample'])

/** Resolve a URL path from the content root safely (no traversal). */
export function safeContentPath(rel: string[]): string | null {
  const abs = path.resolve(CONTENT_DIR, ...rel.map(decodeURIComponent))
  if (abs !== CONTENT_DIR && !abs.startsWith(CONTENT_DIR + path.sep)) return null
  if (rel.some((s) => decodeURIComponent(s).startsWith('.') && !SAFE_DOTFILES.has(decodeURIComponent(s)))) return null
  return abs
}
