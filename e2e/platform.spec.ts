import fs from 'node:fs'
import path from 'node:path'
import { test, expect, type Page } from '@playwright/test'
import { unzipSync } from 'fflate'

const ADMIN = { Authorization: 'Basic ' + Buffer.from('admin:test').toString('base64') }
const RAG = '/ia-generative/rag-gcp'
const errorsOf = (page: Page) => {
  const errs: string[] = []
  page.on('pageerror', (e) => errs.push(e.message))
  return errs
}
async function mermaidSettled(page: Page) {
  await page.waitForFunction(() => [...document.querySelectorAll('.mermaid-block')].every((b) => (b as HTMLElement).dataset.rendered))
}

test.describe('routing & i18n', () => {
  test('root redirects to the preferred language', async ({ browser }) => {
    const ctx = await browser.newContext({ locale: 'es-ES', extraHTTPHeaders: { 'accept-language': 'es-ES,es;q=0.9' } })
    const page = await ctx.newPage()
    await page.goto('/')
    await expect(page).toHaveURL(/\/es$/)
    await expect(page.locator('h1')).toHaveText('Aprende IA y cloud construyendo.')
    await ctx.close()
  })

  for (const [l, dir, title] of [['fr', 'ltr', 'Apprendre'], ['en', 'ltr', 'Learn AI'], ['ar', 'rtl', 'تعلّم'], ['es', 'ltr', 'Aprende']] as const) {
    test(`home renders in ${l}`, async ({ page }) => {
      const errs = errorsOf(page)
      await page.goto(`/${l}`)
      await expect(page.locator('html')).toHaveAttribute('dir', dir)
      await expect(page.locator('html')).toHaveAttribute('lang', l)
      await expect(page.locator('.hero-title')).toContainText(title)
      expect(await page.locator('.theme-tile').count()).toBeGreaterThanOrEqual(3)
      expect(errs).toEqual([])
    })
  }

  test('translated content is used, missing translations fall back with a notice', async ({ page }) => {
    await page.goto(`/en${RAG}/fondamentaux/introduction`)
    await expect(page.locator('.note-banner')).toHaveCount(0)
    await page.goto(`/en${RAG}/fondamentaux/embeddings`)
    await expect(page.locator('.note-banner')).toBeVisible()
    await page.goto('/ar/ia-generative')
    await expect(page.locator('h1')).not.toHaveText('IA générative')
  })

  test('language switcher keeps the current page', async ({ page }) => {
    await page.goto(`/fr${RAG}`)
    await page.locator('.locale-switch select').selectOption('ar')
    await expect(page).toHaveURL(new RegExp(`/ar${RAG}$`))
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl')
  })
})

test.describe('content structure from folders', () => {
  test('modular course, flat course, nested category, loose file and draft', async ({ page, request }) => {
    await page.goto(`/fr${RAG}`)
    await expect(page.locator('.curriculum .module')).toHaveCount(2)
    await expect(page.locator('.curriculum [data-lesson]')).toHaveCount(5)
    await page.goto('/fr/cloud/terraform-cloud-run')
    await expect(page.locator('.curriculum [data-lesson]')).toHaveCount(3)
    await page.goto('/fr/experimentations/agents-llm')
    await expect(page.locator('.ccard')).toHaveCount(2)
    await page.goto('/fr/notes-rapides')
    await expect(page.locator('h1')).toHaveText('Notes rapides')
    expect((await request.get('/fr/experimentations/brouillon-secret')).status()).toBe(404)
    const index = await (await request.get('/api/search?locale=fr')).text()
    expect(index).not.toContain('SECRET-DRAFT-MARKER')
  })

  test('a new folder dropped into content/ is live without rebuild', async ({ page }) => {
    const dir = path.join(process.cwd(), 'content', '98-e2e-live')
    fs.mkdirSync(path.join(dir, '01-mini-cours'), { recursive: true })
    fs.writeFileSync(path.join(dir, 'index.md'), '---\ntitle: Thème E2E\ntype: category\nicon: "🧪"\n---\n')
    fs.writeFileSync(path.join(dir, '01-mini-cours', '01-debut.md'), '# Début\n\nPremière leçon **E2E**.\n')
    fs.writeFileSync(path.join(dir, '01-mini-cours', '02-fin.md'), '# Fin\n\n```mermaid\nflowchart LR\n  A --> B\n```\n')
    try {
      await expect(async () => {
        await page.goto('/fr')
        await expect(page.locator('.theme-tile', { hasText: 'Thème E2E' })).toBeVisible({ timeout: 1000 })
      }).toPass({ timeout: 15_000 })
      await page.goto('/fr/e2e-live/mini-cours')
      await expect(page.locator('.curriculum [data-lesson]')).toHaveCount(2)
      await page.goto('/fr/e2e-live/mini-cours/fin')
      await expect(page.locator('.mermaid-block svg')).toBeVisible()
    } finally {
      fs.rmSync(dir, { recursive: true, force: true })
    }
  })
})

test.describe('rich markdown rendering', () => {
  test('every page renders without JS errors or broken mermaid', async ({ page, request }) => {
    test.setTimeout(900_000)
    const index = (await (await request.get('/api/search?locale=fr')).json()) as { url: string; kind: string }[]
    expect(index.length).toBeGreaterThan(15)
    for (const { url } of index) {
      const errs = errorsOf(page)
      const res = await page.goto(url)
      expect(res?.status(), url).toBe(200)
      await mermaidSettled(page)
      await expect(page.locator('.mermaid-error'), url).toHaveCount(0)
      // Authoring errors are shown in the page instead of crashing it: none may ship.
      await expect(page.locator('main'), url).not.toContainText(/Frontmatter invalide|Quiz invalide|Quiz incomplet/)
      expect(errs, url).toEqual([])
      page.removeAllListeners('pageerror')
    }
  })

  test('no broken internal link or file on any page', async ({ request }) => {
    test.setTimeout(900_000)
    const index = (await (await request.get('/api/search?locale=fr')).json()) as { url: string }[]
    const targets = new Map<string, string>()
    for (const { url } of index) {
      const html = await (await request.get(url)).text()
      for (const [, h] of html.matchAll(/(?:href|src)="(\/[^"#]*)/g)) {
        const u = h.replace(/&amp;/g, '&')
        if (!u.startsWith('/_next') && !u.startsWith('//')) targets.set(u.startsWith('/files') ? u.split('?')[0] : u, url)
      }
    }
    expect(targets.size).toBeGreaterThan(100)
    const broken: string[] = []
    for (const [u, from] of targets) {
      const r = await request.get(u, { headers: { Range: 'bytes=0-0' }, maxRedirects: 0 })
      if (![200, 206, 307, 308].includes(r.status())) broken.push(`${r.status()} ${u} <- ${from}`)
    }
    expect(broken).toEqual([])
  })

  test('imported repos: nested docs become lessons, code folders are browsable', async ({ page, request }) => {
    await page.goto('/fr/agents-google-cloud/securite-gemini-enterprise/gemini-enterprise-securite-acme')
    expect(await page.locator('.curriculum [data-lesson]').count()).toBeGreaterThanOrEqual(25)
    await page.goto('/fr/skills-gemini-enterprise/skills/productivity/daily-briefing')
    await expect(page.locator('.skill-panel a', { hasText: 'daily-briefing.zip' })).toBeVisible()
    const dir = await request.get('/files/04-agents-google-cloud/01-construire-des-agents/01-adk-cloud-run-terraform/terraform')
    expect(await dir.text()).toContain('main.tf')
    const code = await request.get('/files/04-agents-google-cloud/01-construire-des-agents/01-adk-cloud-run-terraform/main.py')
    expect(code.headers()['content-type']).toContain('text/plain')
    for (const secret of ['.env', 'terraform/terraform.tfstate', 'terraform/terraform.tfvars'])
      expect((await request.get(`/files/04-agents-google-cloud/01-construire-des-agents/01-adk-cloud-run-terraform/${secret}`)).status()).toBe(404)
  })

  test('lesson: diagram, table, callouts, image, footnote, task list', async ({ page }) => {
    await page.goto(`/fr${RAG}/fondamentaux/introduction`)
    await mermaidSettled(page)
    await expect(page.locator('.mermaid-block svg').first()).toBeVisible()
    await expect(page.locator('.prose table').first()).toBeVisible()
    await expect(page.locator('.callout-note')).toBeVisible()
    await expect(page.locator('.callout-tip')).toBeVisible()
    const img = page.locator('.prose figure img').first()
    await img.scrollIntoViewIfNeeded()
    await expect.poll(() => img.evaluate((i: HTMLImageElement) => i.naturalWidth)).toBeGreaterThan(100)
    await expect(page.locator('.footnotes li')).toHaveCount(1)
    await expect(page.locator('.task-list-item').first()).toBeVisible()
    // Image zoom opens a lightbox.
    await img.click()
    await expect(page.locator('dialog.lightbox img')).toBeVisible()
  })

  test('math, charts and code titles', async ({ page }) => {
    await page.goto(`/fr${RAG}/fondamentaux/embeddings`)
    await mermaidSettled(page)
    await expect(page.locator('.katex-display').first()).toBeVisible()
    expect(await page.locator('.katex').count()).toBeGreaterThan(3)
    expect(await page.locator('.mermaid-block svg').count()).toBeGreaterThanOrEqual(3)
    await expect(page.locator('figure.code-block figcaption', { hasText: 'embed.py' })).toBeVisible()
    expect(await page.locator('figure.code-block pre.shiki span[style*="--shiki"]').count()).toBeGreaterThan(10)
  })

  test('video, youtube embed, copy button', async ({ page, context, request }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    await page.goto(`/fr${RAG}/mise-en-oeuvre/setup`)
    const video = page.locator('figure.embed-media video')
    await expect(video).toHaveAttribute('src', /demo\.mp4$/)
    await expect(page.locator('figure.embed-video iframe')).toHaveAttribute('src', /youtube-nocookie\.com\/embed\//)
    for (const k of ['warning', 'caution', 'important']) await expect(page.locator(`.callout-${k}`).first()).toBeVisible()
    const fig = page.locator('figure.code-block').first()
    await fig.hover()
    await fig.locator('.copy-btn').click()
    await expect(fig.locator('.copy-btn')).toHaveText('Copié')
    // Video seeking needs byte ranges.
    const src = await video.getAttribute('src')
    const r = await request.get(src!, { headers: { Range: 'bytes=0-99' } })
    expect(r.status()).toBe(206)
    expect(r.headers()['content-range']).toMatch(/^bytes 0-99\//)
    expect((await r.body()).length).toBe(100)
  })

  test('pdf viewer, word preview, powerpoint card + pdf export', async ({ page, request }) => {
    await page.goto(`/fr${RAG}/mise-en-oeuvre/deploiement`)
    const pdf = page.locator('figure.embed-pdf iframe')
    const pdfSrc = (await pdf.getAttribute('src'))!.split('#')[0]
    const r = await request.get(pdfSrc)
    expect(r.headers()['content-type']).toBe('application/pdf')
    expect((await r.body()).subarray(0, 5).toString()).toBe('%PDF-')
    await expect(page.locator('figure.embed-docx .docx-preview')).toContainText(/Prérequis/i)
    await expect(page.locator('figure.embed-docx .docx-preview table')).toHaveCount(1)
    await expect(page.locator('figure.embed-pptx .file-card')).toHaveAttribute('href', /presentation\.pptx\?dl=1$/)
    await expect(page.locator('figure.embed-pptx iframe')).toHaveAttribute('src', /presentation\.pdf/)
    await mermaidSettled(page)
    await expect(page.locator('.mermaid-block svg')).toHaveCount(1)
  })

  test('slides: keyboard navigation, document view', async ({ page }) => {
    await page.goto('/fr/cloud/aide-memoire-gcloud')
    const count = page.locator('.deck-count')
    await expect(count).toContainText('1 /')
    await page.keyboard.press('ArrowRight')
    await page.keyboard.press('ArrowRight')
    await expect(count).toContainText('3 /')
    await page.getByRole('button', { name: 'Voir en document' }).click()
    expect(await page.locator('.slide-doc').count()).toBeGreaterThanOrEqual(8)
  })

  test('dark mode toggle persists', async ({ page }) => {
    await page.goto('/fr')
    const before = await page.locator('html').getAttribute('data-theme')
    await page.getByRole('button', { name: 'Thème' }).click()
    const after = await page.locator('html').getAttribute('data-theme')
    expect(after).not.toBe(before)
    await page.reload()
    await expect(page.locator('html')).toHaveAttribute('data-theme', after!)
  })
})

test.describe('downloads, search, explore', () => {
  test('resource download and whole-course zip', async ({ request }) => {
    const f = await request.get('/files/01-ia-generative/01-rag-gcp/files/guide-installation.docx?dl=1')
    expect(f.status()).toBe(200)
    expect(f.headers()['content-disposition']).toContain('attachment')
    const z = await request.get('/api/download/ia-generative/rag-gcp')
    expect(z.headers()['content-type']).toBe('application/zip')
    const names = Object.keys(unzipSync(new Uint8Array(await z.body())))
    expect(names).toContain('01-rag-gcp/files/demo.mp4')
    expect(names).toContain('01-rag-gcp/02-mise-en-oeuvre/03-recap-slides.md')
    const theme = await request.get('/api/download/ia-generative')
    expect(Object.keys(unzipSync(new Uint8Array(await theme.body())))).toContain('01-ia-generative/02-checklist-prompt-engineering/index.md')
  })

  test('path traversal is refused', async ({ request }) => {
    expect((await request.get('/files/..%2Fpackage.json')).status()).toBe(404)
    expect((await request.get('/files/%2E%2E/%2E%2E/etc/passwd')).status()).toBe(404)
  })

  test('command palette search', async ({ page }) => {
    await page.goto('/fr', { waitUntil: 'networkidle' })
    await page.getByRole('button', { name: 'Rechercher' }).click()
    const input = page.getByPlaceholder('Rechercher une formation, un article, un tag…')
    await input.fill('cosinus')
    await expect(page.locator('.palette-list li').first()).toContainText('Embeddings')
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL(/embeddings$/)
    // Keyboard shortcut works too.
    await page.keyboard.press('Control+k')
    await expect(input).toBeVisible()
  })

  test('explore: landing by theme and format, drill-down to sub-themes', async ({ page }) => {
    await page.goto('/fr/explore')
    await expect(page.locator('.theme-tiles .theme-tile').first()).toBeVisible()
    expect(await page.locator('.format-tiles .ftile').count()).toBeGreaterThanOrEqual(5)
    // Level 1 → level 2 → results limited to that sub-theme
    await page.locator('.theme-chips .chip', { hasText: 'Agents IA sur Google Cloud' }).click()
    await expect(page.locator('.theme-focus .theme-tile')).toHaveCount(3)
    await page.locator('.theme-focus .theme-tile', { hasText: 'Serveurs MCP' }).click()
    await expect(page).toHaveURL(/theme=agents-google-cloud%2Fserveurs-mcp|theme=agents-google-cloud\/serveurs-mcp/)
    await expect(page.locator('.ccard')).toHaveCount(2)
    for (const t of await page.locator('.ccard-trail').allInnerTexts()) expect(t).toContain('Serveurs MCP')
  })

  test('explore: format, level and tag filters', async ({ page }) => {
    await page.goto('/fr/explore?format=skill')
    await expect(page.locator('.ccard-skill').first()).toBeVisible()
    expect(await page.locator('.ccard:not(.ccard-skill)').count()).toBe(0)
    await page.getByRole('button', { name: /Afficher plus/ }).click()
    expect(await page.locator('.ccard-skill').count()).toBeGreaterThan(24)
    await page.goto('/fr/explore')
    await page.locator('.segmented button', { hasText: 'Présentations' }).click()
    await expect(page.locator('.ccard')).toHaveCount(1)
    await page.locator('.segmented button', { hasText: 'Tout' }).click()
    await page.getByRole('button', { name: 'Avancé', exact: true }).click()
    expect(await page.locator('.ccard').count()).toBe(await page.locator('.ccard .level-advanced').count())
    await page.goto('/fr/explore?tag=mcp')
    expect(await page.locator('.ccard').count()).toBeGreaterThanOrEqual(3)
  })

  test('formats have their own page: video, link, skill', async ({ page }) => {
    await page.goto('/fr/videotheque-et-ressources/videos/introducing-adk')
    await expect(page.locator('.kind-video').first()).toBeVisible()
    await expect(page.locator('.video-hero iframe')).toHaveAttribute('src', /youtube-nocookie\.com\/embed\/zgrOwow_uTQ/)
    await page.goto('/fr/videotheque-et-ressources/depots-et-outils/adk-python')
    await expect(page.locator('.link-hero')).toHaveAttribute('href', 'https://github.com/google/adk-python')
    await page.goto('/fr/skills-gemini-enterprise/skills/productivity/daily-briefing')
    await expect(page.locator('.skill-panel a', { hasText: 'daily-briefing.zip' })).toBeVisible()
    expect(await page.locator('.skill-triggers li').count()).toBeGreaterThan(3)
    // Skill descriptions are trimmed to what the skill does (triggers moved to the panel).
    await expect(page.locator('.lede')).not.toContainText('Triggers')
  })

})

test.describe('interactive learning', () => {
  test('quiz: instant feedback, explanation, score, retry', async ({ page }) => {
    await page.goto('/fr/contribuer')
    const quiz = page.locator('.quiz').first()
    await quiz.locator('.quiz-opt').nth(0).click()
    await expect(quiz).toHaveAttribute('data-state', 'wrong')
    await expect(quiz.getByRole('button', { name: 'Vérifier' })).toBeHidden()   // single-answer: no check button
    await expect(quiz.locator('.quiz-expl')).toBeVisible()
    await quiz.getByRole('button', { name: 'Réessayer' }).click()
    await quiz.locator('.quiz-opt').nth(1).click()
    await expect(quiz).toHaveAttribute('data-state', 'right')
    await expect(page.locator('.quiz-score')).toContainText('1 / 1')
  })

  test('task lists are checkable and remembered', async ({ page }) => {
    await page.goto('/fr/ia-generative/rag-gcp/fondamentaux/introduction')
    const box = page.locator('.task-list-item input[type=checkbox]').last()
    await expect(box).toBeEnabled()
    const before = await box.isChecked()
    await box.click()
    await page.reload()
    await expect(page.locator('.task-list-item input[type=checkbox]').last()).toBeChecked({ checked: !before })
  })

  test('use cases and platforms link content both ways', async ({ page }) => {
    await page.goto('/fr/plateformes-et-cas-d-usage/plateformes/watpilot')
    await expect(page.locator('.link-hero')).toHaveAttribute('href', 'https://watpilot.com/')
    await page.goto('/fr/plateformes-et-cas-d-usage/cas-d-usage/recherche-documentaire')
    expect(await page.locator('.fsection .ccard').count()).toBeGreaterThanOrEqual(2)
    await page.goto('/fr/ia-generative/rag-documents-google-drive')
    await expect(page.locator('.hub-chip.hub-usecase', { hasText: 'Interroger ses documents' })).toBeVisible()
    await page.goto('/fr/explore')
    await page.locator('.chip-intent', { hasText: 'Interroger ses documents' }).click()
    await expect(page).toHaveURL(/usecase=recherche-documentaire/)
    expect(await page.locator('.ccard').count()).toBeGreaterThanOrEqual(3)
  })
})

test.describe('learning progress', () => {
  test('mark complete, resume, history', async ({ page }) => {
    await page.goto(`/fr${RAG}`)
    await expect(page.getByRole('link', { name: 'Commencer la formation' })).toBeVisible()
    await page.goto(`/fr${RAG}/fondamentaux/introduction`)
    await page.getByRole('button', { name: 'Marquer comme terminé' }).click()
    await expect(page.getByRole('button', { name: 'Terminé' })).toBeVisible()
    await page.goto(`/fr${RAG}`)
    await expect(page.locator('[data-lesson].is-done')).toHaveCount(1)
    const resume = page.getByRole('link', { name: 'Reprendre' })
    await expect(resume).toHaveAttribute('href', /embeddings$/)
    await page.goto('/fr/me')
    await expect(page.locator('.history')).toContainText('Introduction au RAG')
    await expect(page.locator('.meter-label').first()).toContainText('1/5')
  })

  test('premium content is flagged', async ({ page }) => {
    await page.goto('/fr/cloud/securite-avancee')
    await expect(page.locator('.premium').first()).toBeVisible()
  })
})

test.describe('analytics & admin', () => {
  test('admin requires credentials', async ({ request }) => {
    expect((await request.get('/admin')).status()).toBe(401)
    expect((await request.get('/admin', { headers: { Authorization: 'Basic ' + Buffer.from('admin:nope').toString('base64') } })).status()).toBe(401)
  })

  test('visits, clicks and downloads reach the dashboard and heatmap', async ({ page, browser }) => {
    const target = '/fr/cloud/terraform-cloud-run'
    await page.goto(target)
    await page.mouse.click(300, 300)
    await page.locator('.curriculum a').first().click()
    await page.waitForURL(/prerequis$/)
    await page.goto('/fr') // triggers flush of the pending queue
    await page.waitForTimeout(500)
    const ctx = await browser.newContext({ extraHTTPHeaders: ADMIN })
    const admin = await ctx.newPage()
    await admin.goto('/admin?range=24h')
    const views = Number((await admin.locator('.kpi', { hasText: 'Pages vues' }).locator('.kpi-value').innerText()).replace(/\D/g, ''))
    expect(views).toBeGreaterThan(0)
    await expect(admin.locator('table.data')).toContainText(target)
    await expect(admin.locator('.chart svg .bar').first()).toBeVisible()
    await expect(admin.locator('.panel', { hasText: 'Téléchargements' }).locator('li').first()).toBeVisible()
    await admin.goto(`/admin/heatmap?range=24h&path=${encodeURIComponent(target)}`)
    const n = Number((await admin.locator('.heat-count').innerText()).replace(/\D/g, ''))
    expect(n).toBeGreaterThanOrEqual(2)
    await ctx.close()
  })
})

test.describe('responsive', () => {
  for (const url of ['/fr', '/fr/explore', '/ar/explore', `/fr${RAG}`, `/fr${RAG}/mise-en-oeuvre/deploiement`, '/ar/ia-generative/rag-gcp/fondamentaux/introduction', '/fr/ia-generative/construire-un-agent-ia/coder-la-boucle/la-boucle-agentique', '/fr/plateformes-et-cas-d-usage/plateformes/watpilot']) {
    test(`no horizontal scroll on mobile: ${url}`, async ({ browser }) => {
      const ctx = await browser.newContext({ viewport: { width: 375, height: 800 }, isMobile: true })
      const page = await ctx.newPage()
      await page.goto(url)
      await mermaidSettled(page)
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
      expect(overflow).toBeLessThanOrEqual(1)
      await ctx.close()
    })
  }
})
