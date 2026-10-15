// Génère le deck PowerPoint « Les agents dans Gemini Enterprise » (projet 09, PM et RH).
//
// À QUOI SERT CE SCRIPT
//   Il fabrique la présentation destinée aux chefs de projet (PM) et à l'équipe RH : même message que le PDF
//   produit par scripts/build_pdf.py (créer, réutiliser, connecter un agent ; pourquoi un cadre).
//   Fichier produit : Gemini-Enterprise-Agents-Guide-Equipes.pptx (15 diapositives, format 16:9),
//   avec notes de l'orateur sur les diapos. Si vous changez le message, modifiez aussi build_pdf.py.
//
// PRÉREQUIS
//   1. Node.js (testé avec v22).
//   2. Modules npm : pptxgenjs, react, react-dom, sharp, react-icons. Ils ne sont PAS installés dans ce
//      projet (pas de package.json ni de node_modules) ni en global. Installez-les dans un dossier à part :
//        npm install --prefix ~/pptx-deps pptxgenjs react react-dom sharp react-icons
//      puis indiquez ce dossier à Node avec NODE_PATH (voir la commande ci-dessous).
//   3. apply_theme.js (chemin en dur dans le require plus bas) : il vient du skill « pptx » de Claude Code,
//      sous /home/yarab/.claude/skills/synced/<id>/pptx/scripts/apply_theme.js. Il écrit le thème de
//      couleurs (THEME) dans le .pptx. Si ce dossier change ou disparaît (mise à jour du skill), corrigez le
//      chemin du require. Il charge lui-même pptxgenjs/jszip : NODE_PATH est donc indispensable pour lui aussi.
//
// COMMENT LE LANCER (depuis la racine du projet 09-agents-multi-projets-gemini-enterprise)
//   NODE_PATH=~/pptx-deps/node_modules node scripts/build_pptx.js Gemini-Enterprise-Agents-Guide-Equipes.pptx
//   -> affiche « written <chemin> ». Le 1er argument est le chemin de sortie (le fichier est écrasé) ;
//   sans argument, le script écrit « deck.pptx » dans le dossier courant.
//
// CE QU'IL LIT / ÉCRIT
//   Lit : apply_theme.js et les icônes react-icons (converties en PNG par sharp). Tout le texte est dans ce fichier.
//   Écrit : uniquement le .pptx de sortie.
//
// OÙ MODIFIER LE CONTENU
//   - Couleurs du thème : THEME. Titre / auteur du fichier : pres.title, pres.author...
//   - Gabarits (fond, position du titre, pied de page, numéro) : pres.defineSlideMaster « TITRE », « CONTENU », « SOMBRE ».
//   - Une diapo par bloc « // ===... N. Titre · diapo D » dans la fonction async en bas du fichier.
//     slide(master, section, kicker, titre) crée la diapo ; s.addNotes(...) = notes de l'orateur.
//   - Les positions (x, y, w, h) sont en pouces ; la diapo fait 13,333 x 7,5. Après un ajout de texte,
//     ouvrez le .pptx pour vérifier que rien ne déborde (aucun ajustement automatique).
//
// VÉRIFIER APRÈS RÉGÉNÉRATION
//   unzip -l Gemini-Enterprise-Agents-Guide-Equipes.pptx | grep -c "ppt/slides/slide[0-9]*.xml"   -> 15
//   Puis ouvrez-le (LibreOffice Impress ou PowerPoint).
//
// ERREURS FRÉQUENTES
//   - Error: Cannot find module 'pptxgenjs' (ou react, sharp, react-icons/fa6...) -> NODE_PATH absent ou
//     modules non installés (voir Prérequis 2).
//   - Error: Cannot find module '/home/yarab/.claude/skills/.../apply_theme.js'   -> skill déplacé : corriger le chemin.
//   - « pptxgenjs and the jszip that comes with it cannot be found » (venant d'apply_theme.js) -> NODE_PATH absent.
//   - Une icône inconnue (fa.FaXxx undefined) fait planter la conversion : vérifier le nom dans react-icons/fa6.
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
// Dépendance externe : apply_theme.js du skill « pptx » de Claude Code (voir Prérequis 3).
const { applyTheme } = require("/home/yarab/.claude/skills/synced/9d8ca538-7ca9-4bb9-a8f4-650e4b8459f4_8fd7f5c5-8ba9-4c34-8fdc-b76321a996d9/pptx/scripts/apply_theme.js");

// Chemin de sortie : 1er argument, sinon deck.pptx dans le dossier courant.
const OUT = process.argv[2] || "deck.pptx";

const THEME = {
  name: "Securite Gemini Enterprise",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1C2333", lt1: "FFFFFF", dk2: "14213D", lt2: "EEF2F9",
    accent1: "2F6FDE", accent2: "1F4FA8", accent3: "5B6B8C", accent4: "C75B12", accent5: "1E7A4C", accent6: "8FB3F5",
    hlink: "2F6FDE", folHlink: "1F4FA8",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Les agents dans Gemini Enterprise";
pres.subject = "Créer, réutiliser et connecter des agents";
pres.author = "Équipe projet Gemini Enterprise";
pres.company = "Projet Gemini Enterprise";
const C = pres.SchemeColor;

const W = 13.333, MX = 0.6, CW = W - 2 * MX;
const LV = [C.accent3, C.accent1, C.accent2, C.text2]; // couleurs des niveaux N0..N3
const LVHEX = [HEX.accent3, HEX.accent1, HEX.accent2, HEX.dk2];

// ------------------------------------------------------------------ layouts
// TITRE = couverture sombre ; CONTENU = diapo standard (kicker, titre, pied de page, numéro) ; SOMBRE = diapo de conclusion.
pres.defineSlideMaster({
  title: "TITRE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: MX, y: 1.3, w: 11, h: 0.4, fontSize: 13, bold: true, color: C.accent6, charSpacing: 1.5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 1.85, w: 8.0, h: 1.9, fontSize: 44, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: MX, y: 4.1, w: 7.6, h: 1.2, fontSize: 18, color: C.accent6, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENU",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: MX, y: 0.35, w: 9, h: 0.3, fontSize: 12, bold: true, color: C.accent1, charSpacing: 1.5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.65, w: CW - 1.0, h: 0.75, fontSize: 30, bold: true, color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Gemini Enterprise · Les agents · Diffusion interne", options: { x: MX, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
});
pres.defineSlideMaster({
  title: "SOMBRE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: MX, y: 0.35, w: 9, h: 0.3, fontSize: 12, bold: true, color: C.accent6, charSpacing: 1.5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.65, w: CW - 1.0, h: 0.75, fontSize: 30, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Gemini Enterprise · Les agents · Diffusion interne", options: { x: MX, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

// ------------------------------------------------------------------ helpers
// Convertit une icône react-icons en image PNG (base64) de couleur hex, utilisable dans s.addImage({ data }).
async function icon(Comp, hex) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
// Nouvelle diapo sur le gabarit master, rangée dans la section section, avec un petit kicker et un titre.
function slide(master, section, kicker, title) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  if (kicker) s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}
// Zone de texte : o = options pptxgenjs (x, y, w, h en pouces, fontSize, color...) qui remplacent les valeurs par défaut.
function txt(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, margin: 0, fontSize: 15, color: C.text1, valign: "top" }, o)); }
// Rectangle arrondi de fond (couleur fill, gris-bleu clair par défaut).
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || C.background2 }, line: { type: "none" }, objectName: name });
}
// Pastille ronde de diamètre d avec un court label (numéro, « N1 »...).
function badge(s, x, y, d, label, fill, size) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  s.addText(label, { x, y, w: d, h: d, isTextBox: true, margin: 0, align: "center", valign: "middle", bold: true, fontSize: size || 18, color: C.background1 });
}
// Tableau : header = titres, rows = lignes, colW = largeur de chaque colonne ; o.fontSize, o.firstBold.
function table(s, header, rows, x, y, colW, o = {}) {
  const fs = o.fontSize || 13;
  const data = [header.map((h) => ({ text: h, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: fs } }))];
  rows.forEach((r, i) => data.push(r.map((c, j) => ({
    text: c,
    options: { bold: j === 0 && o.firstBold !== false, color: C.text1, fontSize: fs, fill: { color: i % 2 ? C.background2 : C.background1 } },
  }))));
  s.addTable(data, { x, y, w: colW.reduce((a, b) => a + b, 0), colW, border: { type: "solid", pt: 0.5, color: "D9DEE6" }, margin: [4, 6, 4, 6], valign: "middle", autoPage: false });
}
// Encadré : carte de fond + texte centré verticalement.
function callout(s, x, y, w, h, text, fill, color) {
  card(s, x, y, w, h, fill || C.background2);
  txt(s, text, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: h - 0.3, fontSize: 15, color: color || C.text2, valign: "middle" });
}
// Encadré vert « Critères de passage au niveau suivant » avec une case à cocher par item ; renvoie sa hauteur.
function gate(s, x, y, w, items) {
  const h = 0.42 + items.length * 0.34;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: "E8F3EC" }, line: { color: C.accent5, width: 1 } });
  txt(s, "Critères de passage au niveau suivant", { x: x + 0.2, y: y + 0.1, w: w - 0.4, h: 0.3, fontSize: 13, bold: true, color: C.accent5 });
  items.forEach((it, i) => {
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.22, y: y + 0.5 + i * 0.34, w: 0.16, h: 0.16, fill: { color: C.background1 }, line: { color: C.accent5, width: 1 } });
    txt(s, it, { x: x + 0.5, y: y + 0.44 + i * 0.34, w: w - 0.7, h: 0.3, fontSize: 13, valign: "middle" });
  });
  return h;
}
// Pastille « Nn » en haut à droite + ligne Où / Qui / Données / Durée sous le titre.
function levelHeader(s, n, where, who, data, duration) {
  badge(s, W - MX - 0.75, 0.45, 0.75, "N" + n, LV[n], 20);
  const meta = [["Où", where], ["Qui", who], ["Données", data], ["Durée", duration]];
  meta.forEach(([k, v], i) => {
    const x = MX + i * (CW / 4);
    txt(s, [{ text: k + "  ", options: { bold: true, color: LV[n] } }, { text: v, options: { color: C.text1 } }], { x, y: 1.5, w: CW / 4 - 0.1, h: 0.3, fontSize: 13 });
  });
}

// Construction des diapos (async car les icônes sont converties en PNG avant usage : I.flask, I.lock...).
(async () => {
  const I = {};
  const iconDefs = {
    flask: [fa.FaFlask, HEX.accent1], code: [fa.FaCode, HEX.accent1], gauge: [fa.FaGaugeHigh, HEX.accent1],
    lock: [fa.FaLock, HEX.accent1], layers: [fa.FaLayerGroup, HEX.accent1], users: [fa.FaUserShield, HEX.accent1],
    scale: [fa.FaScaleBalanced, HEX.accent1], route: [fa.FaRoute, HEX.accent1], eye: [fa.FaEye, HEX.accent1],
    id: [fa.FaIdBadge, HEX.lt1], key: [fa.FaKey, HEX.lt1], plug: [fa.FaPlug, HEX.lt1], shield: [fa.FaShieldHalved, HEX.lt1],
    globe: [fa.FaGlobe, HEX.lt1], radar: [fa.FaMagnifyingGlassChart, HEX.lt1], robot: [fa.FaRobot, HEX.accent1],
    check: [fa.FaCircleCheck, HEX.accent5], warn: [fa.FaTriangleExclamation, HEX.accent4], bolt: [fa.FaBolt, HEX.accent1],
    clip: [fa.FaClipboardCheck, HEX.accent1], building: [fa.FaBuildingShield, HEX.accent1],
  };
  for (const [k, [Comp, hex]] of Object.entries(iconDefs)) I[k] = await icon(Comp, hex);

  // ------------------------------------------------------------ helpers propres au deck 09
  const LVC = [C.accent1, C.accent2, C.accent5];
  // Carte d'un niveau d'autonomie (1 à 3) : bandeau de couleur, pastille, titre, texte, ligne meta en bas.
  function levelCard(s, x, y, w, h, n, title, lines, meta) {
    card(s, x, y, w, h, C.background2);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.12, fill: { color: LVC[n - 1] }, line: { type: "none" } });
    badge(s, x + 0.25, y + 0.35, 0.6, String(n), LVC[n - 1], 18);
    txt(s, title, { x: x + 1.0, y: y + 0.35, w: w - 1.15, h: 0.6, fontSize: 18, bold: true, color: C.text2, valign: "middle" });
    txt(s, lines, { x: x + 0.25, y: y + 1.15, w: w - 0.5, h: h - 2.0, fontSize: 14 });
    txt(s, meta, { x: x + 0.25, y: y + h - 0.75, w: w - 0.5, h: 0.6, fontSize: 13, bold: true, color: LVC[n - 1] });
  }
  // Rangée de boîtes sombres [(titre, description), ...] reliées par des flèches, sur toute la largeur.
  function flowRow(s, y, boxes, h) {
    const n = boxes.length, gap = 0.45, w = (CW - gap * (n - 1)) / n;
    boxes.forEach(([t, d], i) => {
      const x = MX + i * (w + gap);
      card(s, x, y, w, h, C.text2);
      txt(s, t, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.45, fontSize: 15, bold: true, color: C.background1 });
      txt(s, d, { x: x + 0.2, y: y + 0.65, w: w - 0.4, h: h - 0.8, fontSize: 12.5, color: C.accent6 });
      if (i) txt(s, "→", { x: x - gap, y: y + h / 2 - 0.25, w: gap, h: 0.5, fontSize: 22, bold: true, color: C.accent1, align: "center", valign: "middle" });
    });
  }
  // Liste numérotée (pastilles 1, 2, 3...) ; step = espacement vertical entre deux items.
  function numbered(s, x, y, w, items, fs, step) {
    items.forEach((t, i) => {
      badge(s, x, y + i * step, 0.42, String(i + 1), C.accent1, 13);
      txt(s, t, { x: x + 0.6, y: y + i * step - 0.04, w: w - 0.6, h: step - 0.05, fontSize: fs, valign: "middle" });
    });
  }

  // =============================================================== 1. Titre · diapo 1
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "TITRE", sectionTitle: "Introduction" });
  s.addText("POUR LES CHEFS DE PROJET ET L'ÉQUIPE RH · ACME", { placeholder: "kicker" });
  s.addText("Les agents dans Gemini Enterprise", { placeholder: "title" });
  s.addText("Ce que vous pouvez faire vous-même, ce que vous pouvez demander, comment ça marche, et pourquoi il y a un cadre.", { placeholder: "body" });
  txt(s, "Octobre 2026 · v1.0 · Diffusion interne", { x: MX, y: 6.6, w: 8, h: 0.3, fontSize: 12, color: C.accent6 });
  ["Vous créez", "Vous réutilisez", "On connecte"].forEach((l, i) => {
    const x = 9.0 + i * 1.3, h = 1.1 + i * 0.9;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 6.3 - h, w: 1.2, h, fill: { color: LVC[i] }, line: { type: "none" } });
    txt(s, `${i + 1}`, { x, y: 6.3 - h + 0.1, w: 1.2, h: 0.4, fontSize: 18, bold: true, color: C.background1, align: "center" });
    txt(s, l, { x: x - 0.1, y: 6.4, w: 1.4, h: 0.3, fontSize: 11, color: C.accent6, align: "center" });
  });
  s.addNotes("Objectif de cette présentation : que chacun sache ce qu'est un agent, ce qu'il peut faire seul dans l'app, comment demander l'intégration d'un agent développé par une équipe technique, et pourquoi ces étapes existent. Aucun prérequis technique.");

  // =============================================================== 2. En une page · diapo 2
  s = slide("CONTENU", "Introduction", "Synthèse", "Trois façons d'avoir un agent");
  const W3 = (CW - 0.4) / 3;
  levelCard(s, MX, 1.55, W3, 4.2, 1, "Vous le créez", "Dans l'app, sans code : vous décrivez ce que vous voulez, choisissez les sources, testez, partagez.", "Quelques minutes · vous");
  levelCard(s, MX + W3 + 0.2, 1.55, W3, 4.2, 2, "Vous en réutilisez un", "Un agent déjà publié par une autre équipe devient une étape de votre propre agent.", "Immédiat · vous");
  levelCard(s, MX + 2 * (W3 + 0.2), 1.55, W3, 4.2, 3, "On connecte le vôtre", "Un agent développé par une équipe technique, hébergé ailleurs, est branché dans l'app.", "Quelques jours · équipe habilitée");
  callout(s, MX, 6.0, CW, 0.75, "La règle simple : composer, c'est libre ; connecter, c'est encadré.");
  s.addNotes("C'est le message principal. Les deux premières façons sont en libre-service dans l'app web. La troisième demande une intervention, parce qu'on fait entrer dans l'app quelque chose de nouveau : c'est là qu'on vérifie la sécurité et les données.");

  // =============================================================== 3. C'est quoi un agent · diapo 3
  s = slide("CONTENU", "Introduction", "Comprendre", "Qu'est-ce qu'un agent ?");
  table(s, ["", "L'assistant", "Un agent"], [
    ["Mission", "Tout sujet", "Une tâche précise (ex. politique de télétravail)"],
    ["Sources", "Tout ce à quoi vous avez accès", "Seulement les sources choisies"],
    ["Consignes", "Générales", "Ton, format, étapes, limites définies une fois"],
    ["Régularité", "À la demande", "À la demande, ou planifié (chaque lundi)"],
    ["Partage", "—", "Partagé à une équipe : mêmes réponses pour tous"],
  ], MX, 1.55, [2.2, 4.3, 5.63], { fontSize: 15 });
  callout(s, MX, 5.3, CW, 1.2, "Un agent cherche avec les droits de la personne qui l'utilise. Un collègue sans accès à un dossier RH n'y aura pas accès en passant par un agent.", "E8F3EC", C.accent5);
  s.addNotes("Point de confiance essentiel pour l'équipe RH : un agent n'a pas de super-pouvoirs. Il voit ce que l'utilisateur voit, pas plus.");

  // =============================================================== 4. Trois niveaux · diapo 4
  s = slide("CONTENU", "Introduction", "Qui peut faire quoi", "Trois niveaux d'autonomie");
  table(s, ["", "1 · Utilisateur", "2 · Équipe habilitée", "3 · Administrateur"], [
    ["Qui", "Tout collaborateur de l'app", "2-3 équipes techniques certifiées", "Équipe plateforme"],
    ["Où", "App web", "App web + console Google Cloud", "Console Google Cloud"],
    ["Peut", "Créer sans code, réutiliser, partager (validé)", "Connecter SES agents développés", "Tout : sources, outils, sécurité"],
    ["Ne peut pas", "Brancher un agent ou outil externe", "Toucher à la sécurité de l'app", "—"],
    ["Délai", "Minutes", "Heures", "Jours"],
  ], MX, 1.55, [1.8, 3.5, 3.6, 3.23], { fontSize: 14 });
  callout(s, MX, 5.45, CW, 1.1, "Pourquoi un niveau « équipe habilitée » ? Les équipes qui livrent souvent publient leurs agents sans ticket, avec un rôle limité aux agents : aucune possibilité de modifier la sécurité.");
  s.addNotes("La très grande majorité des utilisateurs n'a besoin que du niveau 1. Le niveau 2 se décide équipe par équipe, après une charte et une courte formation. C'est un levier pour réduire les délais, sans ouvrir la sécurité.");

  // =============================================================== 5. Niveau 1 pas à pas · diapo 5
  pres.addSection({ title: "Créer et partager" });
  s = slide("CONTENU", "Créer et partager", "Niveau 1", "Créer votre agent, vous-même");
  numbered(s, MX, 1.6, 7.3, [
    "App → Agents → Créer un agent",
    "Décrivez en français ce que vous voulez",
    "Choisissez les sources déjà connectées",
    "Ajoutez si besoin un agent existant",
    "Testez, ajustez les consignes",
    "Publiez, partagez à un groupe (validation)",
  ], 16, 0.72);
  card(s, 8.3, 1.55, W - MX - 8.3, 4.5, C.background2);
  txt(s, "Exemple RH", { x: 8.55, y: 1.75, w: 3.9, h: 0.4, fontSize: 16, bold: true, color: C.accent1 });
  txt(s, "« Un agent qui répond aux questions des managers sur la politique de télétravail, à partir du guide RH 2026, en citant le paragraphe. Il refuse les questions sur des cas individuels et renvoie vers le RRH. »",
    { x: 8.55, y: 2.25, w: W - MX - 8.8, h: 3.6, fontSize: 14, italic: true });
  callout(s, MX, 6.15, CW, 0.65, "Bon réflexe : écrire dans les consignes ce que l'agent doit refuser.");
  s.addNotes("Démonstration possible en direct : 10 minutes suffisent pour créer l'agent FAQ télétravail. Insister sur les consignes de refus : c'est ce qui fait un agent fiable.");

  // =============================================================== 6. Ce qu'on peut utiliser · diapo 6
  s = slide("CONTENU", "Créer et partager", "Niveau 1", "Ce que vous pouvez utiliser dans votre agent");
  table(s, ["Disponible", "Exemples", "Si ce n'est pas là"], [
    ["Sources déjà connectées", "Drive, SharePoint, Gmail, Agenda, Jira…", "Demande à l'admin"],
    ["Outils déjà connectés", "Tableau Google Sheets, création de ticket", "Demande à l'admin"],
    ["Agents déjà publiés", "« Stock magasin (Supply) », « Prix et promotions »", "Demande de connexion"],
    ["Planification", "Tous les lundis à 8 h, résumé envoyé", "Si la fonction est activée"],
  ], MX, 1.55, [3.1, 5.6, 3.43], { fontSize: 15 });
  callout(s, MX, 4.6, CW, 1.1, "Il n'existe pas de bouton « connecter un agent externe » pour les utilisateurs : faire entrer un nouvel agent, outil ou source passe toujours par une demande.");
  s.addNotes("C'est la limite à expliquer clairement : l'utilisateur compose avec ce qui est en place. Pour ajouter du neuf, on passe par le circuit de demande, présenté plus loin.");

  // =============================================================== 7. Exemples RH · diapo 7
  s = slide("CONTENU", "Créer et partager", "Pour l'équipe RH", "Idées d'agents, et limites à respecter");
  table(s, ["Agent", "Mission", "Niveau", "Avis DPO"], [
    ["FAQ politiques RH", "Télétravail, congés, mobilité, avec citation du texte", "1", "Non"],
    ["Accueil nouvel arrivant", "Guider la première semaine", "1", "Non"],
    ["Préparation d'entretien annuel", "Trame et questions selon le poste", "1", "Non"],
    ["Synthèse des offres internes", "Résumé chaque lundi", "1 (planifié)", "Non"],
    ["Questions paie individuelles", "Sur SA fiche de paie", "3 (développé)", "Oui"],
    ["Analyse de dossiers salariés", "Résumer des dossiers individuels", "3 (développé)", "Oui, préalable"],
  ], MX, 1.5, [3.4, 5.0, 1.9, 1.83], { fontSize: 13 });
  callout(s, MX, 5.55, CW, 1.1, "Protection automatique : un numéro de sécurité sociale, un IBAN ou un numéro de CNI dans une question ou une réponse est bloqué par le filtre de sécurité.", "E8F3EC", C.accent5);
  s.addNotes("Les quatre premiers agents peuvent démarrer dès le pilote. Dès qu'il s'agit de données personnelles individuelles (paie, dossiers), c'est un agent développé et l'avis du DPO est un préalable. Ne jamais copier des données personnelles dans un dossier partagé pour que l'agent les trouve.");

  // =============================================================== 8. Partager · diapo 8
  s = slide("CONTENU", "Créer et partager", "Partager", "Partager un agent avec vos collègues");
  flowRow(s, 1.6, [["Vous", "publiez et partagez avec un groupe"], ["Demande", "envoyée à l'administrateur"],
    ["Validation", "sources, consignes, destinataires"], ["Équipe", "l'agent apparaît dans la galerie"]], 1.7);
  table(s, ["Réglage de l'app", "Recommandé"], [
    ["Création d'agents par les utilisateurs", "Activée, d'abord pour un groupe pilote"],
    ["Partage sans validation de l'admin", "Désactivé"],
    ["Partage à des groupes entiers", "Avec validation"],
    ["Galerie d'agents", "Activée"],
  ], MX, 3.65, [6.2, 5.93], { fontSize: 14 });
  s.addNotes("Le partage est simple, mais validé. C'est ce qui garantit qu'un agent diffusé à des centaines de personnes a été relu : bonnes sources, bonnes consignes, bons destinataires. Délai habituel : un à deux jours ouvrés.");

  // =============================================================== 9. Connecter · diapo 9
  pres.addSection({ title: "Connecter et demander" });
  s = slide("CONTENU", "Connecter et demander", "Niveaux 2 et 3", "Connecter un agent développé par une équipe");
  flowRow(s, 1.6, [["Projet Supply", "l'agent « Stock magasin » y est développé"], ["Autorisation", "Supply autorise notre app"],
    ["App Gemini Enterprise", "l'agent est ajouté et décrit"], ["Utilisateurs", "le groupe autorisé le trouve"]], 1.7);
  const pts = ["Les utilisateurs n'ont besoin d'aucun accès au projet de l'équipe Supply : c'est l'app qui appelle l'agent.",
    "L'équipe propriétaire garde la main : elle autorise, et peut retirer l'autorisation.",
    "Un agent peut en appeler un autre : l'Assistant magasin demande le stock à l'agent Supply.",
    "Même projet que l'app : aucune autorisation à donner, ajouté en quelques minutes."];
  pts.forEach((t, i) => {
    s.addImage({ data: I.check, x: MX, y: 3.75 + i * 0.68, w: 0.32, h: 0.32 });
    txt(s, t, { x: MX + 0.5, y: 3.7 + i * 0.68, w: CW - 0.5, h: 0.45, fontSize: 15, valign: "middle" });
  });
  s.addNotes("Exemple réel, déjà réalisé dans le projet de référence : l'agent de stock de l'équipe Supply vit dans son propre projet Google Cloud, et il est utilisé dans notre app et par un autre agent. Chaque équipe reste responsable de son agent.");

  // =============================================================== 10. Demander · diapo 10
  s = slide("CONTENU", "Connecter et demander", "Demander", "Comment demander la connexion d'un agent");
  numbered(s, MX, 1.6, 6.0, ["Le PM décrit le besoin (mission, utilisateurs, données)", "L'équipe technique développe ou fournit l'agent, en Europe",
    "La sécurité vérifie la checklist (+ DPO si données perso.)", "L'équipe habilitée ou l'admin connecte l'agent", "Les utilisateurs le trouvent ; le PM suit l'adoption"], 15, 0.8);
  card(s, 7.1, 1.5, W - MX - 7.1, 4.6, C.background2);
  txt(s, "Checklist avant connexion", { x: 7.35, y: 1.65, w: 5.0, h: 0.4, fontSize: 15, bold: true, color: C.text2 });
  ["Hébergé en Europe", "Filtre de sécurité intégré à l'agent", "Identité technique propre, droits minimum", "Confirmation humaine avant toute action",
    "Description claire", "Groupe d'utilisateurs précis", "Propriétaire identifié", "Avis DPO si données personnelles"].forEach((t, i) => {
    s.addImage({ data: I.check, x: 7.35, y: 2.2 + i * 0.47, w: 0.26, h: 0.26 });
    txt(s, t, { x: 7.75, y: 2.15 + i * 0.47, w: 4.7, h: 0.38, fontSize: 13, valign: "middle" });
  });
  callout(s, MX, 6.25, CW, 0.6, "Délai indicatif : 2 à 5 jours ouvrés ; avec données personnelles, selon l'avis du DPO.");
  s.addNotes("Le PM est le point d'entrée : il décrit le besoin. La checklist est courte et connue d'avance, ce qui rend le délai prévisible.");

  // =============================================================== 10 bis. Agent déjà dans un catalogue · diapo 11
  s = slide("CONTENU", "Connecter et demander", "Cas fréquent", "Une équipe a déjà un agent dans son catalogue ?");
  txt(s, "Pas besoin de le refaire : le catalogue (Agent Registry) de l'équipe sert à le retrouver et à savoir comment le brancher.",
    { x: MX, y: 1.45, w: CW, h: 0.45, fontSize: 15, color: C.accent3 });
  levelCard(s, MX, 2.05, W3, 3.55, 1, "Hébergé chez Google", "L'équipe donne une autorisation dans son projet ; nous l'ajoutons dans l'app.", "Le jour même");
  levelCard(s, MX + W3 + 0.2, 2.05, W3, 3.55, 2, "Hébergé ailleurs (A2A)", "Autorisation sur son service ; l'agent doit se protéger lui-même.", "Le jour même");
  levelCard(s, MX + 2 * (W3 + 0.2), 2.05, W3, 3.55, 3, "Par notre catalogue", "Inscrit dans notre catalogue ; tout passe par un point de contrôle.", "Quelques jours · cible");
  callout(s, MX, 5.8, CW, 0.95, "L'équipe nous envoie : projet et nom de l'agent, type, nom et description, groupe visé, données utilisées, protection intégrée, propriétaire.");
  s.addNotes("Réponse à une question fréquente : les équipes qui ont déjà des agents dans leur Agent Registry n'ont rien à refaire. Voies 1 et 2 : disponible le jour même. Voie 3 : la cible de gouvernance, avec Agent Gateway. Détail technique : docs/04 du projet 09.");

  // =============================================================== 11. Pourquoi · diapo 12
  pres.addSection({ title: "Cadre et suite" });
  s = slide("CONTENU", "Cadre et suite", "Pourquoi", "Pourquoi ce cadre, et pas « tout ouvert » ?");
  table(s, ["Risque", "Ce qui l'empêche"], [
    ["Fuite de données", "L'agent respecte les droits de chaque utilisateur ; partage validé"],
    ["Agent non maîtrisé (« Shadow AI »)", "Seuls l'admin et les équipes habilitées connectent ; chaque ajout est tracé"],
    ["Manipulation de l'IA", "Filtre Model Armor ; confirmation humaine avant toute action"],
    ["Données personnelles", "Avis DPO, partage restreint, journalisation encadrée"],
    ["Agent sans propriétaire", "Propriétaire identifié, revue trimestrielle"],
  ], MX, 1.55, [4.2, 7.93], { fontSize: 15 });
  callout(s, MX, 5.4, CW, 1.15, "Le cadre ne freine pas : il permet d'ouvrir largement la création d'agents parce que les points sensibles sont maîtrisés.");
  s.addNotes("Bénéfices à souligner : autonomie des métiers, réutilisation d'un bon agent par toutes les équipes, confiance de la sécurité et du DPO, rapidité pour les équipes habilitées.");

  // =============================================================== 12. Qui fait quoi + feuille de route · diapo 13
  s = slide("CONTENU", "Cadre et suite", "Organisation", "Qui fait quoi, et dans quel ordre");
  table(s, ["Activité", "RH / utilisateur", "PM", "Tech", "Admin", "Sécurité", "DPO"], [
    ["Créer un agent sans code", "R", "I", "—", "—", "—", "—"],
    ["Valider un partage", "C", "I", "—", "R / A", "I", "C"],
    ["Exprimer un besoin d'agent développé", "C", "R", "C", "I", "I", "C"],
    ["Vérifier la checklist", "—", "I", "C", "C", "R / A", "A"],
    ["Connecter l'agent", "—", "I", "R", "R / A", "I", "—"],
  ], MX, 1.5, [4.0, 1.8, 1.0, 1.1, 1.3, 1.5, 1.43], { fontSize: 12 });
  table(s, ["Phase", "Création (niveau 1)", "Connexion d'agents développés", "Pour l'équipe RH"], [
    ["Pilote", "Groupe pilote, partage validé", "Admin uniquement", "FAQ politiques RH, accueil"],
    ["Généralisation", "Tous, partage validé", "Admin + 2-3 équipes habilitées", "Agents planifiés"],
    ["Cible", "Tous", "Équipes habilitées + catalogue central", "Agents sur données RH (DPO)"],
  ], MX, 4.25, [2.0, 3.2, 3.8, 3.13], { fontSize: 13 });
  s.addNotes("R = réalise, A = approuve, C = consulté, I = informé. La feuille de route démarre petit avec l'équipe RH et deux agents pilotes.");

  // =============================================================== 13. FAQ · diapo 14
  s = slide("CONTENU", "Cadre et suite", "Questions fréquentes", "FAQ");
  table(s, ["Question", "Réponse"], [
    ["Puis-je connecter moi-même un agent trouvé ailleurs ?", "Non : faites une demande."],
    ["Puis-je utiliser l'agent d'une autre équipe dans le mien ?", "Oui, s'il est publié dans l'app et partagé avec vous."],
    ["Mon agent verra-t-il des documents que je ne vois pas ?", "Non : il cherche avec vos droits."],
    ["Mes collègues verront-ils mes conversations ?", "Non : partager un agent ne partage pas les conversations."],
    ["Pourquoi mon partage est « en attente » ?", "L'admin valide : un à deux jours ouvrés."],
    ["Faut-il un accès Google Cloud ?", "Non, sauf pour les équipes techniques."],
    ["Une équipe a déjà un agent dans son catalogue ?", "Pas à refaire : branché souvent le jour même."],
    ["L'agent est dans le même projet que l'app ?", "Plus simple : aucune autorisation à donner."],
    ["Un agent sur des données de paie ?", "Agent développé, après avis du DPO."],
  ], MX, 1.5, [6.2, 5.93], { fontSize: 14 });
  s.addNotes("Garder cette diapositive affichée pendant les questions.");

  // =============================================================== 14. Prochaine étape · diapo 15
  s = slide("SOMBRE", "Cadre et suite", "Prochaine étape", "Démarrer avec l'équipe RH");
  [["Atelier d'une heure", "choisir deux agents pilotes avec l'équipe RH"], ["Créer ensemble", "FAQ politiques RH et accueil nouvel arrivant"],
    ["Définir le partage", "le groupe pilote et la validation"], ["Mesurer", "usages et retours après un mois"]].forEach(([t, d], i) => {
    const y = 1.8 + i * 0.95;
    badge(s, MX, y, 0.6, String(i + 1), C.accent1, 16);
    txt(s, [{ text: t + "  ", options: { bold: true, color: C.background1 } }, { text: d, options: { color: C.accent6 } }], { x: MX + 0.85, y, w: 7.4, h: 0.6, fontSize: 18, valign: "middle" });
  });
  card(s, 8.8, 1.8, W - MX - 8.8, 3.4, C.accent1, "doc");
  txt(s, "Pour aller plus loin", { x: 9.1, y: 2.0, w: 3.6, h: 0.45, fontSize: 18, bold: true, color: C.background1 });
  txt(s, "Guide PDF « Les agents dans Gemini Enterprise ». Équipes techniques : dossier 09-…/docs, en commençant par le tutoriel 02 (même projet).",
    { x: 9.1, y: 2.55, w: W - MX - 9.4, h: 2.4, fontSize: 14, color: C.background1 });
  s.addNotes("Conclure sur l'action : un atelier d'une heure et deux agents pilotes. Tout le reste est prêt : le cadre, le circuit de demande, la documentation.");

  // Écrit le .pptx, puis y applique le thème de couleurs THEME.
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
