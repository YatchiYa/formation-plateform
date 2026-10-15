// Teste resumer.gs HORS de Google : les services Google sont remplacés par des doublures.
//   Syntaxe seule : cp resumer.gs /tmp/r.js && node --check /tmp/r.js (ce fichier la vérifie aussi).
//   node test_gs.mjs            -> faux Gemini, aucune clé
//   REEL=1 node test_gs.mjs     -> vrai Gemini via curl (clé lue dans GEMINI_API_KEY)
import { readFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import vm from 'node:vm'
import assert from 'node:assert/strict'

const source = readFileSync(new URL('./resumer.gs', import.meta.url), 'utf8')
new vm.Script(source) // lève une SyntaxError si le .gs est invalide
const REEL = process.env.REEL === '1'

function fauxFetch(url, options) {
  const corps = JSON.parse(options.payload)
  const texte = corps.generationConfig.responseSchema
    ? JSON.stringify({ resume: 'Le client demande un remboursement.', categorie: 'reclamation', priorite: 'haute' })
    : 'Résumé factice.'
  return { getResponseCode: () => 200,
    getContentText: () => JSON.stringify({ candidates: [{ content: { parts: [{ text: texte }] } }] }) }
}

function vraiFetch(url, options) {
  // La clé passe par stdin (-H @-) : elle n'apparaît ni dans la liste des processus ni dans les logs
  const sortie = execFileSync('curl', ['-s', '-w', '\n%{http_code}', '-X', 'POST', url,
    '-H', 'Content-Type: application/json', '-H', '@-', '--data-binary', options.payload],
  { input: 'x-goog-api-key: ' + options.headers['x-goog-api-key'] + '\n' }).toString()
  const i = sortie.lastIndexOf('\n')
  return { getResponseCode: () => Number(sortie.slice(i + 1)), getContentText: () => sortie.slice(0, i) }
}

// Feuille « Emails » en mémoire : en-têtes + 3 lignes, dont une déjà validée
const lignes = [
  ['Objet', 'Texte', 'Résumé', 'Catégorie', 'Priorité', 'Statut'],
  ['Colis abîmé', 'Bonjour, ma commande n° 1042 est arrivée cassée. Je veux être remboursé sous 48 h, sinon je laisse un avis.', '', '', '', ''],
  ['Question horaires', 'Êtes-vous ouverts le samedi matin ?', '', '', '', ''],
  ['Déjà vu', 'Texte', 'ok', 'information', 'basse', 'Validé'],
]
let appels = 0, toast = ''
const cache = new Map()
const ctx = {
  console,
  PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => (REEL ? process.env.GEMINI_API_KEY : 'cle-factice') }) },
  UrlFetchApp: { fetch: (u, o) => { appels++; return (REEL ? vraiFetch : fauxFetch)(u, o) } },
  Utilities: { sleep: () => {}, DigestAlgorithm: { MD5: 'md5' },
    computeDigest: (algo, s) => [...createHash(algo).update(s).digest()],
    base64Encode: (octets) => Buffer.from(octets).toString('base64') },
  CacheService: { getScriptCache: () => ({ get: (k) => cache.get(k) ?? null, put: (k, v) => cache.set(k, v) }) },
  SpreadsheetApp: { getActive: () => ({
    getSheetByName: () => ({ getDataRange: () => ({ getValues: () => lignes.map((l) => [...l]) }),
      getRange: (r, c, nl, nc) => ({ setValues: (v) => { lignes[r - 1].splice(c - 1, nc, ...v[0]) } }) }),
    toast: (m) => { toast = m } }) },
}
vm.createContext(ctx)
vm.runInContext(source, ctx)

// 1. =RESUMER(A2) + cache : 2e appel identique sans requête
const r1 = ctx.RESUMER(lignes[1][1])
const r2 = ctx.RESUMER(lignes[1][1])
assert.ok(r1.length > 5 && r1 === r2 && appels === 1, 'cache')
assert.equal(ctx.RESUMER(''), '')
// 2. =RESUMER(A2:A3) : une plage renvoie une colonne
assert.equal(ctx.RESUMER([[lignes[1][1]], ['']]).length, 2)
// 3. Traitement par lot : lignes 1 et 2 remplies, ligne validée intacte
ctx.traiterEmails()
assert.equal(lignes[1][5], 'À valider')
assert.ok(vm.runInContext('CATEGORIES', ctx).includes(lignes[1][3]) && ['haute', 'normale', 'basse'].includes(lignes[1][4]))
assert.deepEqual(lignes[3], ['Déjà vu', 'Texte', 'ok', 'information', 'basse', 'Validé'])
console.log('RESUMER(A2) ->', r1)
lignes.slice(1).forEach((l) => console.log(' |', l.slice(2).join(' | ')))
console.log(toast, `(${appels} appels ${REEL ? 'réels' : 'factices'})`)
console.log('OK')
