/**
 * Google Apps Script : l'API Gemini dans Google Sheets.
 *
 * Installation : Extensions > Apps Script, collez ce fichier, enregistrez.
 * Clé : Paramètres du projet (roue dentée) > Propriétés du script >
 *       ajoutez GEMINI_API_KEY = votre clé (jamais dans le code).
 *
 *  - =RESUMER(A2)          fonction personnalisée : résumé en une phrase
 *  - menu « IA » > Traiter les e-mails : remplit résumé / catégorie / priorité
 *    sur la feuille « Emails » et met le statut « À valider » (un humain relit).
 */

const MODELE = 'gemini-3.5-flash';
const CATEGORIES = ['commande', 'facturation', 'reclamation', 'rendez-vous', 'information', 'autre'];
// Colonnes de la feuille « Emails » (1 = A) : A objet, B texte, puis ce que l'IA écrit
const COL = { OBJET: 1, TEXTE: 2, RESUME: 3, CATEGORIE: 4, PRIORITE: 5, STATUT: 6 };
const LIMITE_MS = 5 * 60 * 1000; // on s'arrête avant la limite de 6 min par exécution

function lireCle_() {
  const cle = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!cle) {
    throw new Error('Clé absente : Paramètres du projet > Propriétés du script > GEMINI_API_KEY');
  }
  return cle;
}

/** Appelle Gemini (API REST generateContent). Réessaie sur 429/503. */
function appelerGemini_(prompt, schema) {
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODELE + ':generateContent';
  const generationConfig = { temperature: 0.2 };
  if (schema) {
    generationConfig.responseMimeType = 'application/json';
    generationConfig.responseSchema = schema;
  }
  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: { 'x-goog-api-key': lireCle_() },
    payload: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: generationConfig }),
    muteHttpExceptions: true, // on lit nous-mêmes le code HTTP
  };
  for (let essai = 1; essai <= 3; essai++) {
    const rep = UrlFetchApp.fetch(url, options);
    const code = rep.getResponseCode();
    if (code === 200) {
      const parts = JSON.parse(rep.getContentText()).candidates[0].content.parts;
      return parts.map(function (p) { return p.text || ''; }).join('').trim();
    }
    if (code !== 429 && code !== 503) {
      throw new Error('Gemini a répondu ' + code + ' : ' + rep.getContentText().slice(0, 200));
    }
    Utilities.sleep(2000 * essai);
  }
  throw new Error('Gemini indisponible, réessayez dans quelques minutes');
}

/**
 * Résume un texte en une phrase de 20 mots maximum.
 *
 * @param {string} texte Le texte ou la cellule à résumer.
 * @return {string} Le résumé.
 * @customfunction
 */
function RESUMER(texte) {
  if (Array.isArray(texte)) { // =RESUMER(A2:A20) : une plage arrive en tableau 2D
    return texte.map(function (ligne) { return [RESUMER(ligne[0])]; });
  }
  if (!texte) return '';
  // Le tableur recalcule souvent : un cache de 6 h évite de repayer le même appel
  const cache = CacheService.getScriptCache();
  const cleCache = 'resume:' + Utilities.base64Encode(
    Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, String(texte)));
  const enCache = cache.get(cleCache);
  if (enCache) return enCache;
  const resume = appelerGemini_(
    'Résume ce texte en une phrase de 20 mots maximum, en français, sans inventer :\n\n' + texte);
  cache.put(cleCache, resume, 21600);
  return resume;
}

/** Ajoute le menu « IA » à l'ouverture du classeur. */
function onOpen() {
  SpreadsheetApp.getUi().createMenu('IA')
    .addItem('Traiter les e-mails', 'traiterEmails')
    .addToUi();
}

/** Analyse un e-mail : renvoie {resume, categorie, priorite}. */
function analyserEmail_(objet, texte) {
  const schema = {
    type: 'OBJECT',
    properties: {
      resume: { type: 'STRING' },
      categorie: { type: 'STRING', enum: CATEGORIES },
      priorite: { type: 'STRING', enum: ['haute', 'normale', 'basse'] },
    },
    required: ['resume', 'categorie', 'priorite'],
  };
  const prompt = 'Tu tries la boîte de réception d\'une petite entreprise. ' +
    'Résume l\'e-mail en une phrase, choisis une catégorie et une priorité ' +
    '(haute = client mécontent ou échéance sous 48 h).\n\nObjet : ' + objet + '\n\n' + texte;
  return JSON.parse(appelerGemini_(prompt, schema));
}

/** Menu IA > Traiter les e-mails : traite les lignes sans statut, puis s'arrête proprement. */
function traiterEmails() {
  const debut = Date.now();
  const feuille = SpreadsheetApp.getActive().getSheetByName('Emails');
  const valeurs = feuille.getDataRange().getValues(); // ligne 0 = en-têtes
  let traitees = 0;
  for (let i = 1; i < valeurs.length; i++) {
    if (valeurs[i][COL.STATUT - 1]) continue;        // déjà traité ou validé : on n'y touche pas
    if (Date.now() - debut > LIMITE_MS) break;       // relancez le menu pour continuer
    const r = analyserEmail_(valeurs[i][COL.OBJET - 1], valeurs[i][COL.TEXTE - 1]);
    feuille.getRange(i + 1, COL.RESUME, 1, 4).setValues([[r.resume, r.categorie, r.priorite, 'À valider']]);
    traitees++;
  }
  SpreadsheetApp.getActive().toast(traitees + ' e-mail(s) traité(s). Relisez la colonne Statut.');
}
