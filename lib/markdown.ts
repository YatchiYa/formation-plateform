import fs from 'node:fs'
import path from 'node:path'
import { unified } from 'unified'
import remarkParse from 'remark-parse'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import remarkRehype from 'remark-rehype'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import rehypeKatex from 'rehype-katex'
import rehypeShiki from '@shikijs/rehype'
import rehypeStringify from 'rehype-stringify'
import { visit, SKIP } from 'unist-util-visit'
import { toString } from 'hast-util-to-string'
import mammoth from 'mammoth'
import matter from 'gray-matter'
import type { Root as MdRoot, Blockquote, Paragraph, Text } from 'mdast'
import type { Root, Element, ElementContent } from 'hast'
import { fileUrl, findBySuffix, getTree, CONTENT_DIR } from './content'
import type { Locale } from './i18n'

export interface TocItem { id: string; text: string; depth: number }
export interface Rendered { html: string; toc: TocItem[] }

const VIDEO = new Set(['.mp4', '.webm', '.mov', '.m4v'])
const AUDIO = new Set(['.mp3', '.wav', '.ogg', '.m4a'])
const OFFICE = new Set(['.pptx', '.ppt', '.xlsx', '.xls', '.odp', '.odt', '.zip', '.ipynb', '.csv', '.key', '.doc'])
const FOOTNOTES: Record<Locale, string> = { fr: 'Notes', en: 'Footnotes', ar: 'الحواشي', es: 'Notas' }
const ALERTS = ['note', 'tip', 'important', 'warning', 'caution']

/** GitHub-style `> [!NOTE]` callouts. */
function remarkAlerts() {
  return (tree: MdRoot) => {
    visit(tree, 'blockquote', (node: Blockquote) => {
      const p = node.children[0] as Paragraph | undefined
      const first = p?.type === 'paragraph' ? (p.children[0] as Text | undefined) : undefined
      const m = first?.type === 'text' ? /^\[!(\w+)\]\s*/.exec(first.value) : null
      if (!m || !ALERTS.includes(m[1].toLowerCase())) return
      const kind = m[1].toLowerCase()
      first!.value = first!.value.slice(m[0].length)
      if (!first!.value && p!.children.length === 1) node.children.shift()
      node.data = { hName: 'aside', hProperties: { className: ['callout', `callout-${kind}`], 'data-kind': kind } }
    })
  }
}

const el = (tagName: string, properties: Record<string, unknown>, children: ElementContent[] = []): Element =>
  ({ type: 'element', tagName, properties: properties as Element['properties'], children })
const txt = (value: string) => ({ type: 'text' as const, value })
const fmtSize = (n: number) => (n > 1e6 ? `${(n / 1e6).toFixed(1)} Mo` : `${Math.max(1, Math.round(n / 1e3))} Ko`)

export const videoEmbed = (href: string) => {
  let m = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]{6,})/.exec(href)
  if (m) return `https://www.youtube-nocookie.com/embed/${m[1]}`
  m = /vimeo\.com\/(\d+)/.exec(href)
  if (m) return `https://player.vimeo.com/video/${m[1]}`
  return null
}

function fileCard(abs: string, url: string, label: string, ext: string): Element {
  const size = fs.existsSync(abs) ? fmtSize(fs.statSync(abs).size) : ''
  return el('a', { className: ['file-card'], href: url + '?dl=1', download: '', 'data-track': 'download' }, [
    el('span', { className: ['file-ext'], 'data-ext': ext }, [txt(ext)]),
    el('span', { className: ['file-name'] }, [txt(label || path.basename(abs))]),
    el('span', { className: ['file-size'] }, [txt(size)]),
  ])
}

// Mammoth output is inserted as raw HTML, parsed by rehype-raw (content is author-trusted, like the markdown itself).
async function docxPreview(abs: string): Promise<ElementContent[]> {
  try {
    const { value } = await mammoth.convertToHtml({ path: abs })
    return [{ type: 'raw', value } as unknown as ElementContent]
  } catch {
    return [el('p', {}, [txt('Aperçu indisponible pour ce document.')])]
  }
}

/** Media embeds, link rewriting, mermaid, code titles. Relative paths resolve from the markdown file. */
function rehypeContent(opts: { dir: string; locale: Locale }) {
  return async (tree: Root) => {
    const tasks: Promise<void>[] = []
    const resolveRel = (src: string) => {
      if (/^([a-z]+:|\/|#)/i.test(src)) return null
      const clean = decodeURI(src.split(/[?#]/)[0])
      const abs = path.resolve(opts.dir, clean)
      return abs.startsWith(CONTENT_DIR) ? abs : null
    }

    visit(tree, 'element', (node: Element, index, parent) => {
      // Paragraph that is just one media element or one video link -> block embed.
      if (node.tagName === 'p' && parent && index !== undefined) {
        const kids = node.children.filter((c) => !(c.type === 'text' && !c.value.trim()))
        const only = kids.length === 1 && kids[0].type === 'element' ? (kids[0] as Element) : null
        if (only?.tagName === 'a') {
          const href = String(only.properties.href || '')
          const e = videoEmbed(href)
          if (e && toString(only).trim() === href) {
            parent.children[index] = el('figure', { className: ['embed', 'embed-video'] }, [
              el('iframe', { src: e, title: 'video', loading: 'lazy', allow: 'accelerometer; encrypted-media; picture-in-picture; fullscreen', allowFullScreen: true }),
            ])
            return SKIP
          }
        }
        if (only?.tagName === 'img') {
          const block = mediaBlock(only)
          if (block) { parent.children[index] = block; return SKIP }
        }
      }
      if (node.tagName === 'img') {
        let abs = resolveRel(String(node.properties.src || ''))
        if (abs && !fs.existsSync(abs)) abs = findBySuffix(abs) ?? abs
        if (abs) node.properties.src = fileUrl(abs)
        node.properties.loading = 'lazy'
        node.properties.decoding = 'async'
      }
      if (node.tagName === 'a') {
        const href = String(node.properties.href || '')
        if (/^https?:\/\//.test(href)) {
          node.properties.target = '_blank'
          node.properties.rel = ['noopener', 'noreferrer']
          node.properties.className = ['external']
        } else {
          let abs = resolveRel(href)
          if (abs && !fs.existsSync(abs)) abs = findBySuffix(abs) ?? abs
          if (abs) {
            const t = getTree()
            const dirIndex = ['index.md', 'README.md', 'SKILL.md'].map((f) => t.byFile.get(path.join(abs!, f))).find(Boolean)
            const target = t.byFile.get(abs) ?? dirIndex
            const hash = href.includes('#') ? href.slice(href.indexOf('#')) : ''
            node.properties.href = target ? `/${opts.locale}${target.url}${hash}` : fileUrl(abs)
          }
        }
      }
      if (node.tagName === 'pre') {
        const code = node.children[0] as Element | undefined
        if (code?.tagName !== 'code') return
        const cls = (code.properties.className as string[] | undefined) ?? []
        if (cls.includes('language-quiz')) {
          parent!.children[index!] = quizBlock(toString(code))
          return SKIP
        }
        if (cls.includes('language-mermaid')) {
          parent!.children[index!] = el('div', { className: ['mermaid-block'] }, [el('pre', { className: ['mermaid-src'] }, [txt(toString(code))])])
          return SKIP
        }
        const meta = String((code.data as { meta?: string } | undefined)?.meta ?? '')
        const title = /title=["']([^"']+)["']/.exec(meta)?.[1]
        const lang = cls.find((c) => c.startsWith('language-'))?.slice(9)
        parent!.children[index!] = el('figure', { className: ['code-block'], 'data-lang': lang ?? 'text' }, [
          ...(title ? [el('figcaption', {}, [txt(title)])] : []),
          node,
        ])
        return SKIP
      }
    })

    function mediaBlock(img: Element): Element | null {
      const src = String(img.properties.src || '')
      const alt = String(img.properties.alt || '')
      const abs = resolveRel(src)
      const ext = path.extname(src.split(/[?#]/)[0]).toLowerCase()
      const url = abs ? fileUrl(abs) : src
      const caption = alt ? [el('figcaption', {}, [txt(alt)])] : []
      if (VIDEO.has(ext)) return el('figure', { className: ['embed', 'embed-media'] }, [el('video', { src: url, controls: true, preload: 'metadata', playsInline: true }), ...caption])
      if (AUDIO.has(ext)) return el('figure', { className: ['embed', 'embed-media'] }, [el('audio', { src: url, controls: true, preload: 'metadata' }), ...caption])
      if (!abs) return el('figure', { className: ['figure'] }, [img, ...caption])
      if (ext === '.pdf') {
        return el('figure', { className: ['embed', 'embed-doc', 'embed-pdf'] }, [
          el('iframe', { src: url + '#view=FitH', title: alt || path.basename(abs), loading: 'lazy' }),
          fileCard(abs, url, alt, 'pdf'),
        ])
      }
      if (ext === '.docx') {
        const preview = el('div', { className: ['docx-preview', 'prose-inner'] })
        tasks.push(docxPreview(abs).then((c) => { preview.children = c }))
        return el('figure', { className: ['embed', 'embed-doc', 'embed-docx'] }, [
          el('details', { open: true }, [el('summary', {}, [txt(alt || path.basename(abs))]), preview]),
          fileCard(abs, url, alt, 'docx'),
        ])
      }
      if (OFFICE.has(ext)) {
        const pdf = abs.replace(/\.[^.]+$/, '.pdf')
        const kids: Element[] = []
        if (ext !== '.pdf' && fs.existsSync(pdf)) kids.push(el('iframe', { src: fileUrl(pdf) + '#view=FitH', title: alt || path.basename(pdf), loading: 'lazy' }))
        kids.push(fileCard(abs, url, alt, ext.slice(1)))
        return el('figure', { className: ['embed', 'embed-doc', `embed-${ext.slice(1)}`] }, kids)
      }
      img.properties.src = url
      img.properties.loading = 'lazy'
      img.properties.decoding = 'async'
      return el('figure', { className: ['figure'] }, [el('button', { className: ['zoomable'], type: 'button', 'aria-label': alt || 'image' }, [img]), ...caption])
    }

    await Promise.all(tasks)
  }
}

/**
 * ```quiz blocks (YAML: question, options, answer index or list, explanation) → markup the
 * reader component makes interactive. Built from text nodes only, so nothing is injected as HTML.
 */
function quizBlock(src: string): Element {
  let q: { question?: unknown; options?: unknown; answer?: unknown; explanation?: unknown }
  try {
    q = matter(`---\n${src}\n---\n`).data
  } catch (e) {
    return el('aside', { className: ['callout', 'callout-caution'] }, [el('p', {}, [txt('Quiz invalide (YAML) : ' + (e as Error).message.split('\n')[0])])])
  }
  const options = Array.isArray(q.options) ? q.options.map(String) : []
  const answers = (Array.isArray(q.answer) ? q.answer : [q.answer]).map(Number).filter((n) => Number.isInteger(n) && n >= 0 && n < options.length)
  if (!q.question || options.length < 2 || !answers.length)
    return el('aside', { className: ['callout', 'callout-caution'] }, [el('p', {}, [txt('Quiz incomplet : il faut question, au moins 2 options et answer.')])])
  return el('div', { className: ['quiz'], 'data-answer': answers.join(','), 'data-multi': answers.length > 1 ? 'true' : 'false' }, [
    el('p', { className: ['quiz-q'] }, [txt(String(q.question))]),
    el('ol', { className: ['quiz-options'] }, options.map((o, i) => el('li', {}, [el('button', { type: 'button', className: ['quiz-opt'], 'data-i': String(i), 'data-track': 'quiz-answer' }, [txt(o)])]))),
    ...(q.explanation ? [el('p', { className: ['quiz-expl'], hidden: true }, [txt(String(q.explanation))])] : []),
  ])
}

function rehypeToc(out: TocItem[]) {
  return () => (tree: Root) => {
    visit(tree, 'element', (n: Element) => {
      if ((n.tagName === 'h2' || n.tagName === 'h3') && n.properties.id) out.push({ id: String(n.properties.id), text: toString(n), depth: Number(n.tagName[1]) })
    })
  }
}

const cache = new Map<string, Rendered>()

export async function render(md: string, opts: { file: string; locale: Locale }): Promise<Rendered> {
  // Tree version in the key: links are resolved against the tree, so moving/adding content re-renders.
  const key = `${opts.file}:${opts.locale}:${getTree().version}:${md.length}:${hash(md)}`
  const hit = cache.get(key)
  if (hit) return hit
  const toc: TocItem[] = []
  const file = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkMath)
    .use(remarkAlerts)
    .use(remarkRehype, { allowDangerousHtml: true, footnoteLabel: FOOTNOTES[opts.locale], footnoteBackLabel: '↩' })
    // Before rehype-raw: raw re-parsing drops the code `meta` (titles) this plugin reads.
    .use(rehypeContent, { dir: path.dirname(opts.file), locale: opts.locale })
    .use(rehypeRaw)
    .use(rehypeSlug)
    .use(rehypeToc(toc))
    .use(rehypeKatex, { throwOnError: false, strict: false })
    .use(rehypeShiki, {
      themes: { light: 'github-light', dark: 'github-dark-dimmed' },
      defaultColor: false,
      lazy: true,
      fallbackLanguage: 'text',
      onError: () => {},
    })
    .use(rehypeStringify)
    .process(md)
  const out = { html: String(file), toc }
  if (cache.size > 500) cache.clear() // ponytail: crude bound, LRU if content grows past a few hundred pages
  cache.set(key, out)
  return out
}

function hash(s: string) {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0
  return h
}

/** Slides: split on lines that are exactly `---` (outside code fences). */
export function splitSlides(md: string): string[] {
  const out: string[] = []
  let cur: string[] = []
  let fence = false
  for (const line of md.split('\n')) {
    if (/^\s*(```|~~~)/.test(line)) fence = !fence
    if (!fence && line.trim() === '---') { out.push(cur.join('\n')); cur = [] } else cur.push(line)
  }
  out.push(cur.join('\n'))
  return out.filter((s) => s.trim())
}
