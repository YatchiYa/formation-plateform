// Génère le deck PowerPoint « Gemini Enterprise : feuille de route sécurité » (projet 06).
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");
const { applyTheme } = require("/home/yarab/.claude/skills/synced/9d8ca538-7ca9-4bb9-a8f4-650e4b8459f4_8fd7f5c5-8ba9-4c34-8fdc-b76321a996d9/pptx/scripts/apply_theme.js");

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
pres.title = "Gemini Enterprise - Feuille de route sécurité";
pres.subject = "Sécurité Gemini Enterprise par niveaux";
pres.author = "Équipe projet Gemini Enterprise";
pres.company = "Projet Gemini Enterprise";
const C = pres.SchemeColor;

const W = 13.333, MX = 0.6, CW = W - 2 * MX;
const LV = [C.accent3, C.accent1, C.accent2, C.text2]; // couleurs des niveaux N0..N3
const LVHEX = [HEX.accent3, HEX.accent1, HEX.accent2, HEX.dk2];

// ------------------------------------------------------------------ layouts
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
    { text: { text: "Gemini Enterprise · Feuille de route sécurité · Acme · Diffusion interne", options: { x: MX, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
});
pres.defineSlideMaster({
  title: "SOMBRE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: MX, y: 0.35, w: 9, h: 0.3, fontSize: 12, bold: true, color: C.accent6, charSpacing: 1.5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.65, w: CW - 1.0, h: 0.75, fontSize: 30, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Gemini Enterprise · Feuille de route sécurité · Acme · Diffusion interne", options: { x: MX, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

// ------------------------------------------------------------------ helpers
async function icon(Comp, hex) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
function slide(master, section, kicker, title) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  if (kicker) s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}
function txt(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, margin: 0, fontSize: 15, color: C.text1, valign: "top" }, o)); }
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || C.background2 }, line: { type: "none" }, objectName: name });
}
function badge(s, x, y, d, label, fill, size) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" } });
  s.addText(label, { x, y, w: d, h: d, isTextBox: true, margin: 0, align: "center", valign: "middle", bold: true, fontSize: size || 18, color: C.background1 });
}
function table(s, header, rows, x, y, colW, o = {}) {
  const fs = o.fontSize || 13;
  const data = [header.map((h) => ({ text: h, options: { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: fs } }))];
  rows.forEach((r, i) => data.push(r.map((c, j) => ({
    text: c,
    options: { bold: j === 0 && o.firstBold !== false, color: C.text1, fontSize: fs, fill: { color: i % 2 ? C.background2 : C.background1 } },
  }))));
  s.addTable(data, { x, y, w: colW.reduce((a, b) => a + b, 0), colW, border: { type: "solid", pt: 0.5, color: "D9DEE6" }, margin: [4, 6, 4, 6], valign: "middle", autoPage: false });
}
function callout(s, x, y, w, h, text, fill, color) {
  card(s, x, y, w, h, fill || C.background2);
  txt(s, text, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: h - 0.3, fontSize: 15, color: color || C.text2, valign: "middle" });
}
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
function levelHeader(s, n, where, who, data, duration) {
  badge(s, W - MX - 0.75, 0.45, 0.75, "N" + n, LV[n], 20);
  const meta = [["Où", where], ["Qui", who], ["Données", data], ["Durée", duration]];
  meta.forEach(([k, v], i) => {
    const x = MX + i * (CW / 4);
    txt(s, [{ text: k + "  ", options: { bold: true, color: LV[n] } }, { text: v, options: { color: C.text1 } }], { x, y: 1.5, w: CW / 4 - 0.1, h: 0.3, fontSize: 13 });
  });
}

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

  // =============================================================== 1. Titre
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "TITRE", sectionTitle: "Introduction" });
  s.addText("PRÉPARÉ POUR LES ÉQUIPES ACME · SÉCURITÉ · ARCHITECTURE · DATA", { placeholder: "kicker" });
  s.addText("Gemini Enterprise\nFeuille de route sécurité", { placeholder: "title" });
  s.addText("De la découverte dans la console Google Cloud à une production industrialisée en Terraform, niveau par niveau.", { placeholder: "body" });
  txt(s, "Octobre 2026 · v1.0 · Document de travail, diffusion interne", { x: MX, y: 6.6, w: 8, h: 0.3, fontSize: 12, color: C.accent6 });
  [0, 1, 2, 3].forEach((n) => {
    const h = 1.0 + n * 0.9, x = 8.9 + n * 1.0;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 6.4 - h, w: 0.95, h, fill: { color: n === 0 ? "3A4A6B" : LV[n] }, line: { color: HEX.dk2, width: 1 } });
    txt(s, "N" + n, { x: x + 0.12, y: 6.4 - h + 0.12, w: 0.7, h: 0.35, fontSize: 16, bold: true, color: C.accent6 });
  });
  s.addNotes("Objectif de la séance : montrer comment on donne un assistant IA à grande échelle sans ouvrir de brèche. Message clé dès l'ouverture : on ne choisit pas entre aller vite et être sûr. On démarre en quelques jours dans la console Google Cloud, sur des données sans enjeu, pendant qu'on construit en code le socle de production. Le document s'appuie sur un socle Terraform déjà écrit (projet 06), commenté fichier par fichier.");

  // =============================================================== 2. En une page
  s = slide("CONTENU", "Introduction", "Synthèse", "Sécuriser par niveaux, comme on monte un escalier");
  const lv = [
    ["Découverte", "Console Google Cloud", "10 à 20 testeurs", "Données non sensibles", "1 à 2 semaines"],
    ["Socle", "Terraform", "Pilote de 50 à 200", "Données internes", "3 à 4 semaines"],
    ["Production", "Terraform + CI/CD", "Ouverture par groupes", "Données internes", "4 à 6 semaines"],
    ["Avancé", "Terraform + organisation", "Tous", "Sources étendues", "Selon besoins"],
  ];
  const cw4 = (CW - 3 * 0.3) / 4;
  lv.forEach((l, n) => {
    const x = MX + n * (cw4 + 0.3), y = 1.75;
    card(s, x, y, cw4, 3.5, C.background2, "niveau" + n);
    badge(s, x + 0.25, y + 0.25, 0.75, "N" + n, LV[n], 20);
    txt(s, l[0], { x: x + 1.15, y: y + 0.4, w: cw4 - 1.3, h: 0.5, fontSize: 20, bold: true, color: C.text2 });
    txt(s, [
      { text: "Où", options: { bold: true, color: LV[n], breakLine: true } }, { text: l[1], options: { breakLine: true } },
      { text: "Qui", options: { bold: true, color: LV[n], breakLine: true } }, { text: l[2], options: { breakLine: true } },
      { text: "Données", options: { bold: true, color: LV[n], breakLine: true } }, { text: l[3], options: { breakLine: true } },
      { text: "Durée indicative", options: { bold: true, color: LV[n], breakLine: true } }, { text: l[4] },
    ], { x: x + 0.25, y: y + 1.2, w: cw4 - 0.5, h: 2.2, fontSize: 14, paraSpaceAfter: 2 });
  });
  callout(s, MX, 5.55, CW, 1.2, "Chaque marche apporte une protection mesurable, élargit le périmètre d'usage, et ne commence que lorsque la précédente est validée. Les mesures sont cumulatives : le niveau 2 contient tout le niveau 1.");
  s.addNotes("Lire de gauche à droite. Niveau 0 : on apprend dans la console, sans données sensibles. Niveau 1 : on rejoue en code ce qui a été validé et on ajoute ce que la console ne fait pas bien, sur un pilote. Niveau 2 : on obtient des garanties opposables (chiffrement par nos clés, preuves verrouillées, CI/CD). Niveau 3 : on étend vers les agents qui agissent. Les durées sont indicatives et dépendent surtout des délais d'autorisation des sources (Microsoft, GitHub, Atlassian).");

  // =============================================================== 3. Bénéfices
  s = slide("CONTENU", "Introduction", "Ce que l'approche apporte", "Aller vite, sans prendre de risque");
  const ben = [
    [I.bolt, "Démarrer demain", "Test en console en quelques jours, sur des données sans enjeu, pendant que le socle de production se construit."],
    [I.clip, "Une sécurité démontrable", "Chaque mesure répond à un risque nommé, se teste en recette et laisse une trace d'audit."],
    [I.lock, "Impossible à affaiblir par erreur", "Plancher Model Armor, séparation des rôles, alerte dès qu'un garde-fou change."],
    [I.building, "RGPD dès la conception", "Données en UE, sources interrogées sans copie, conservation minimisée, journaux réservés."],
    [I.code, "Industrialisé", "La même configuration Terraform, relue et versionnée, en recette et en production."],
  ];
  ben.forEach(([ic, t, d], i) => {
    const y = 1.7 + i * 1.0;
    s.addShape(pres.shapes.OVAL, { x: MX, y, w: 0.7, h: 0.7, fill: { color: C.background2 }, line: { type: "none" } });
    s.addImage({ data: ic, x: MX + 0.17, y: y + 0.17, w: 0.36, h: 0.36 });
    txt(s, t, { x: MX + 1.0, y: y + 0.02, w: 6.6, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
    txt(s, d, { x: MX + 1.0, y: y + 0.4, w: 6.6, h: 0.5, fontSize: 14, color: C.text1 });
  });
  card(s, 8.6, 1.7, W - MX - 8.6, 4.7, C.text2, "citation");
  txt(s, "« La bonne question n'est pas : l'IA est-elle sûre ? C'est : que peut-elle voir, que lui envoie-t-on, et comment le sait-on ? »",
    { x: 8.9, y: 2.0, w: W - MX - 9.2, h: 3.0, fontSize: 22, italic: true, color: C.background1, valign: "middle" });
  txt(s, "Le reste de la présentation répond à ces trois questions, niveau par niveau.", { x: 8.9, y: 5.3, w: W - MX - 9.2, h: 0.8, fontSize: 14, color: C.accent6 });
  s.addNotes("Les deux échecs classiques des projets d'IA en entreprise : le projet bloqué par une sécurité tout ou rien, et le pilote ouvert trop vite qu'on ne sait plus refermer. L'approche par niveaux évite les deux. Insister sur la citation : elle recentre le débat sur l'accès aux données, ce qu'on envoie au modèle, et la capacité de détection, plutôt que sur une confiance abstraite dans le modèle.");

  // =============================================================== 4. Décisions
  s = slide("CONTENU", "Introduction", "Décisions attendues de Acme", "Quatre décisions à prendre à froid");
  const dec = [
    ["Fournisseur d'identité", "Google ou Entra ID", "En changer plus tard efface l'historique des conversations", "Avant le niveau 1"],
    ["Localisation", "UE recommandée", "Immuable après création ; conditionne le chiffrement CMEK", "Avant le niveau 1"],
    ["Sources du pilote", "Drive, SharePoint…", "Définit connecteurs, secrets et autorisations à préparer", "Pendant le niveau 0"],
    ["Conservation et journaux", "DPO, CSE si besoin", "Données personnelles de salariés", "Avant le niveau 2"],
  ];
  const cw2 = (CW - 0.3) / 2;
  dec.forEach((d, i) => {
    const x = MX + (i % 2) * (cw2 + 0.3), y = 1.7 + Math.floor(i / 2) * 2.45;
    card(s, x, y, cw2, 2.2, C.background2, "decision" + i);
    badge(s, x + 0.3, y + 0.3, 0.7, String(i + 1), C.accent1, 22);
    txt(s, d[0], { x: x + 1.25, y: y + 0.3, w: cw2 - 1.5, h: 0.45, fontSize: 22, bold: true, color: C.text2 });
    txt(s, d[1], { x: x + 1.25, y: y + 0.78, w: cw2 - 1.5, h: 0.35, fontSize: 15, color: C.accent1, bold: true });
    txt(s, d[2], { x: x + 1.25, y: y + 1.18, w: cw2 - 1.5, h: 0.5, fontSize: 14 });
    txt(s, "Quand : " + d[3], { x: x + 1.25, y: y + 1.7, w: cw2 - 1.5, h: 0.3, fontSize: 13, color: C.accent3, bold: true });
  });
  s.addNotes("Ces quatre décisions conditionnent tout le reste. Les deux premières sont irréversibles : la localisation d'une app Gemini Enterprise ne se change pas, et changer de fournisseur d'identité efface l'historique des conversations et oblige à recréer les sources. C'est la raison d'être du niveau 0 : apprendre avant de décider. Sur la localisation, la recommandation est l'UE : résidence des données et condition pour activer CMEK (impossible en global).");

  // =============================================================== 5. Principes
  pres.addSection({ title: "Principes et vue d'ensemble" });
  s = slide("CONTENU", "Principes et vue d'ensemble", "Principes", "Six principes qui guident tous les choix");
  const pr = [
    [I.flask, "Tester en console, industrialiser en code", "La console pour comprendre ; Terraform pour garantir, relire et reproduire."],
    [I.gauge, "Mesurer avant de bloquer", "Observer les faux positifs, régler, puis appliquer. Identité et données : bloquants dès le jour 1."],
    [I.route, "Les droits de la source font foi", "Mode fédéré par défaut : chacun ne voit que ce qu'il voit déjà, sans copie."],
    [I.layers, "Défense en profondeur", "Identité, connecteurs, filtrage et détection se complètent ; aucune mesure ne suffit seule."],
    [I.users, "Personne ne désactive sa propre sécurité", "Admins de l'app ≠ sécurité. Plancher technique et alerte sur toute modification."],
    [I.scale, "Décisions tracées et réversibles", "Variables documentées, revue de code, validation par la bonne personne."],
  ];
  const cw3 = (CW - 2 * 0.3) / 3;
  pr.forEach(([ic, t, d], i) => {
    const x = MX + (i % 3) * (cw3 + 0.3), y = 1.7 + Math.floor(i / 3) * 2.6;
    card(s, x, y, cw3, 2.35, C.background2, "principe" + i);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.3, w: 0.65, h: 0.65, fill: { color: C.background1 }, line: { type: "none" } });
    s.addImage({ data: ic, x: x + 0.46, y: y + 0.46, w: 0.33, h: 0.33 });
    txt(s, t, { x: x + 0.3, y: y + 1.05, w: cw3 - 0.6, h: 0.6, fontSize: 17, bold: true, color: C.text2 });
    txt(s, d, { x: x + 0.3, y: y + 1.62, w: cw3 - 0.6, h: 0.65, fontSize: 13 });
  });
  s.addNotes("Ces principes viennent de la pratique des déploiements cloud en entreprise. Le deuxième est le plus contre-intuitif pour une équipe sécurité : un filtre trop strict est contourné, et les collaborateurs partent vers des IA grand public non maîtrisées, ce qui est le pire scénario. On mesure donc avant de bloquer, sauf pour l'identité et l'accès aux données, bloquants dès le premier jour. Le cinquième est le plus structurant : celui qui exploite l'outil ne peut pas couper sa sécurité.");

  // =============================================================== 6. Escalier
  s = slide("CONTENU", "Principes et vue d'ensemble", "Vue d'ensemble", "L'escalier de sécurité");
  const stairs = [
    ["Découverte", "Console", ["App de test en UE", "SSO Workspace", "Model Armor natif", "Recherche web coupée"]],
    ["Socle", "Terraform", ["Groupes, séparation des rôles", "Model Armor + DLP France", "Connecteurs fédérés", "Secrets en coffre", "Journaux, alertes"]],
    ["Production", "Terraform + CI/CD", ["Clés Acme (CMEK)", "Preuves verrouillées", "Politiques d'organisation UE", "Revue de code obligatoire"]],
    ["Avancé", "Terraform + organisation", ["VPC Service Controls", "Agent Gateway", "Agents maison filtrés", "Databricks via MCP"]],
  ];
  stairs.forEach(([name, where, items], n) => {
    const x = MX + n * (cw4 + 0.3), top = 4.4 - n * 0.85, h = 6.75 - top;
    card(s, x, top, cw4, h, LV[n], "marche" + n);
    txt(s, "N" + n + " · " + name, { x: x + 0.25, y: top + 0.2, w: cw4 - 0.5, h: 0.45, fontSize: 20, bold: true, color: C.background1 });
    txt(s, where, { x: x + 0.25, y: top + 0.65, w: cw4 - 0.5, h: 0.3, fontSize: 13, color: C.accent6 });
    txt(s, items.map((it, i) => ({ text: it, options: { bullet: true, breakLine: i < items.length - 1 } })),
      { x: x + 0.25, y: top + 1.05, w: cw4 - 0.4, h: h - 1.2, fontSize: 13, color: C.background1, paraSpaceAfter: 3 });
  });
  callout(s, MX, 1.6, 6.2, 1.45, "Pourquoi des niveaux plutôt qu'un « big bang » ? Trois décisions sont irréversibles : localisation, identité, CMEK. On les prend après avoir appris.", "FBF1EA", C.accent4);
  s.addNotes("L'escalier se lit de gauche à droite : chaque marche contient la précédente. Le message à faire passer : on ne prend pas les décisions irréversibles dans l'urgence d'un lancement. Le niveau 0 sert précisément à apprendre la plateforme pour décider en connaissance de cause.");

  // =============================================================== 7. Couches
  s = slide("CONTENU", "Principes et vue d'ensemble", "Les six couches", "Six couches de protection, qui montent en puissance");
  table(s, ["Couche", "Question à laquelle elle répond", "N0", "N1", "N2", "N3"], [
    ["1 · Identité et accès", "Qui peut entrer, et qui peut changer les règles ?", "SSO", "Complet", "Revues d'accès", "Entra ID si besoin"],
    ["2 · Protection des données", "Qui contrôle le chiffrement et les secrets ?", "Google", "Secrets", "CMEK", "Politiques d'org."],
    ["3 · Connecteurs", "Que peut voir l'assistant, avec quels droits ?", "1 source test", "Fédéré", "IP fixes", "MCP, Databricks"],
    ["4 · Filtrage IA", "Qu'est-ce qui entre et sort du modèle ?", "Natif", "DLP France", "Red team", "Agents maison"],
    ["5 · Exposition", "Où vont les données, que partage-t-on ?", "UE, web coupé", "Partages fermés", "Ouverture gouvernée", "VPC-SC"],
    ["6 · Audit et détection", "Comment le sait-on ?", "Audit", "Alertes", "Logs verrouillés", "SIEM"],
  ], MX, 1.7, [2.6, 3.9, 1.35, 1.35, 1.5, 1.43], { fontSize: 14 });
  s.addNotes("Chaque couche répond à une question simple. Le tableau montre comment chacune monte en puissance d'un niveau à l'autre. À souligner : dès le niveau 0, trois couches sont déjà actives nativement (SSO, Model Armor, UE et web coupé), sans écrire une ligne de code.");

  // =============================================================== 8. N0 activations
  pres.addSection({ title: "Les niveaux" });
  s = slide("CONTENU", "Les niveaux", "Niveau 0 · Découverte", "Tester directement dans la console Google Cloud");
  levelHeader(s, 0, "console Google Cloud", "10 à 20 testeurs", "non sensibles", "1 à 2 semaines");
  table(s, ["Ce que l'on active", "Pourquoi", "Où dans la console"], [
    ["Projet de découverte dédié", "Isoler les essais ; supprimé ensuite", "Resource Manager → Nouveau projet"],
    ["App Gemini Enterprise en UE", "Résidence européenne dès le départ", "Gemini Enterprise → Créer une app → EU"],
    ["Identité Google Workspace (SSO)", "Aucun compte local, 2FA de l'annuaire", "Gemini Enterprise → Paramètres → Identité"],
    ["Licences d'essai, groupe testeurs", "Périmètre maîtrisé et nominatif", "Abonnements ; IAM → groupe"],
    ["Google Drive fédéré (dossier test)", "Vérifier que les droits Drive sont respectés", "App → Data stores → Google Drive"],
    ["Model Armor sur l'assistant", "Voir les blocages : injection, données sensibles", "Security → Model Armor ; App → Configurations"],
    ["Recherche web publique coupée", "Aucune question vers un moteur public", "App → Configurations → Assistant"],
    ["Journaux d'accès aux données", "Premières traces d'audit", "IAM → Journaux d'audit"],
  ], MX, 2.05, [3.6, 4.2, 4.33], { fontSize: 13 });
  s.addNotes("Gemini Enterprise est un service managé : l'essentiel des garde-fous s'active en quelques clics. Commencer par la console permet aux équipes de voir concrètement l'effet de chaque réglage avant de le figer en code. Chaque réglage fait ici est noté dans un inventaire : il sera repris en Terraform au niveau 1.");

  // =============================================================== 9. N0 tests + gate
  s = slide("CONTENU", "Les niveaux", "Niveau 0 · Découverte", "Ce que l'on teste ensemble, et la règle d'or");
  const tests = ["Un testeur ne retrouve pas un document Drive qui ne lui est pas partagé",
    "« Ignore tes instructions… », une carte de test ou un lien malveillant sont bloqués",
    "Les réponses citent leurs sources ; qualité jugée sur des cas d'usage réels",
    "Faux positifs de Model Armor observés sur le vocabulaire Acme"];
  tests.forEach((t, i) => {
    const y = 1.75 + i * 0.85;
    s.addImage({ data: I.check, x: MX, y: y + 0.05, w: 0.4, h: 0.4 });
    txt(s, t, { x: MX + 0.6, y, w: 6.3, h: 0.7, fontSize: 16, valign: "middle" });
  });
  card(s, 7.8, 1.75, W - MX - 7.8, 3.0, "FBF1EA", "regle");
  s.addImage({ data: I.warn, x: 8.1, y: 2.0, w: 0.5, h: 0.5 });
  txt(s, "Règle d'or du niveau 0", { x: 8.75, y: 2.02, w: 4, h: 0.45, fontSize: 20, bold: true, color: C.accent4 });
  txt(s, "Aucune donnée personnelle ou confidentielle. L'app de découverte est jetable : elle n'a pas le chiffrement CMEK, qui doit être activé avant la création de l'app de production.",
    { x: 8.1, y: 2.65, w: W - MX - 8.4, h: 1.9, fontSize: 15, color: C.text1 });
  gate(s, MX, 5.15, CW, ["Les 4 décisions structurantes sont prises", "Tests passés et faux positifs documentés", "Inventaire des réglages console établi, pour reprise en Terraform"]);
  s.addNotes("Les tests du niveau 0 se font avec les équipes, en direct. Le plus parlant pour le métier : un document Drive non partagé reste invisible. Le plus parlant pour la sécurité : une tentative d'injection de prompt bloquée. La règle d'or est non négociable : l'app de découverte n'a pas CMEK, et CMEK ne peut pas être ajouté après coup.");

  // =============================================================== 10. N1
  s = slide("CONTENU", "Les niveaux", "Niveau 1 · Socle", "Les six couches en code, sur un pilote métier");
  levelHeader(s, 1, "Terraform (projet 06)", "pilote de 50 à 200", "internes", "3 à 4 semaines");
  const n1 = [
    [I.id, "1 · Identité et accès", "4 groupes ; séparation des rôles : les admins de l'app ne touchent ni filtres, ni clés, ni journaux"],
    [I.key, "2 · Données", "Secrets des connecteurs en coffre ; conversations conservées 30 jours au lieu de 60"],
    [I.plug, "3 · Connecteurs", "Modèle générique fédéré : droits natifs, aucune copie ; IP sortantes fixes"],
    [I.shield, "4 · Filtrage IA", "Model Armor entrée et sortie, FAIL_CLOSED, détecteurs France (NIR, IBAN…), plancher"],
    [I.globe, "5 · Exposition", "UE, recherche web coupée, partages d'agents et de conversations fermés"],
    [I.radar, "6 · Détection", "Journaux dédiés en UE lisibles par la sécurité seule ; alertes garde-fou et pic de blocages"],
  ];
  n1.forEach(([ic, t, d], i) => {
    const x = MX + (i % 3) * (cw3 + 0.3), y = 2.05 + Math.floor(i / 3) * 1.6;
    card(s, x, y, cw3, 1.42, C.background2, "couche" + i);
    badge(s, x + 0.2, y + 0.22, 0.55, "", C.accent1);
    s.addImage({ data: ic, x: x + 0.33, y: y + 0.35, w: 0.29, h: 0.29 });
    txt(s, t, { x: x + 0.9, y: y + 0.2, w: cw3 - 1.05, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
    txt(s, d, { x: x + 0.9, y: y + 0.58, w: cw3 - 1.05, h: 0.8, fontSize: 13 });
  });
  gate(s, MX, 5.35, CW, ["Recette de sécurité passée (13 tests) et points « à valider » levés", "DPO : conservation et journalisation validées ; pilote informé", "Valeur métier confirmée par le pilote"]);
  s.addNotes("Dès que de vraies données entrent en jeu, la configuration doit être relue, reproductible et traçable. Terraform décrit l'état attendu, toute modification passe par une revue de code, et l'historique Git devient la preuve d'audit. Le socle livré couvre les six couches. Point fort à souligner : les détecteurs France. Le filtre de base de Google est orienté États-Unis et ne détecte ni le NIR ni l'IBAN.");

  // =============================================================== 11. N2
  s = slide("CONTENU", "Les niveaux", "Niveau 2 · Production", "Maîtrise du chiffrement, preuves et exploitation");
  levelHeader(s, 2, "Terraform + CI/CD", "ouverture par groupes", "internes", "4 à 6 semaines");
  table(s, ["Mesure", "Pourquoi"], [
    ["CMEK : clé Acme (KMS, Europe)", "Clé désactivée = données illisibles en 15 min"],
    ["Journaux de sécurité verrouillés", "Rétention et preuves non modifiables"],
    ["Politiques d'organisation", "UE et CMEK imposés à tout nouveau projet"],
    ["Chaîne CI/CD Terraform", "Plus aucune modification manuelle en production"],
    ["Access Transparency", "Accès éventuels du personnel Google journalisés"],
    ["Exploitation", "Revues d'accès, rotation des secrets, red team"],
  ], MX, 2.05, [3.9, 4.8], { fontSize: 13 });
  callout(s, 9.6, 2.05, W - MX - 9.6, 3.0, "Pourquoi CMEK maintenant ? La clé doit être enregistrée avant la création de l'app qu'elle protège, et elle engage l'exploitation : rotation, révocation, astreinte.");
  gate(s, MX, 5.35, CW, ["Test de révocation de clé réalisé en recette", "CI/CD en place : plus de droit d'écriture humain en production", "Tableaux de bord d'usage et de sécurité suivis"]);
  s.addNotes("À grande échelle, la question devient : pouvons-nous le prouver, le maîtriser et le maintenir ? CMEK donne à Acme le contrôle du chiffrement : désactiver la clé rend les données illisibles en quinze minutes, ce qui sert d'interrupteur d'urgence. Ce qui est créé avant l'enregistrement de la clé reste chiffré par Google : on active donc CMEK sur l'app de production, de façon préparée, avec une procédure de révocation testée.");

  // =============================================================== 12. N3
  s = slide("CONTENU", "Les niveaux", "Niveau 3 · Avancé", "Étendre la valeur sans étendre la surface d'attaque");
  levelHeader(s, 3, "Terraform + organisation", "tous", "sources étendues", "selon besoins");
  table(s, ["Mesure", "Pourquoi", "Quand"], [
    ["Agent Gateway", "Pare-feu des agents : refus par défaut, règles par outil", "Premier agent maison ou MCP"],
    ["Model Armor par agent", "L'app ne filtre pas les agents maison", "Pour chaque agent"],
    ["Agent Identity", "Une identité par agent, sans clé, révocable", "Avec Agent Gateway"],
    ["Databricks via MCP", "Pas de connecteur natif ; droits Unity Catalog", "Selon les cas d'usage"],
    ["VPC Service Controls", "Bloque l'exfiltration, même avec des identifiants volés", "Observation, puis actif"],
    ["SIEM / SOC", "Intégrer l'IA à la supervision existante", "Selon l'outillage"],
  ], MX, 2.05, [2.4, 4.0, 2.3], { fontSize: 13 });
  card(s, 9.6, 2.05, W - MX - 9.6, 4.4, C.text2, "agentgw");
  s.addImage({ data: I.robot, x: 9.85, y: 2.3, w: 0.5, h: 0.5 });
  txt(s, "Point clé : le filtrage Model Armor de Gemini Enterprise ne s'applique pas aux agents maison.", { x: 9.85, y: 3.0, w: W - MX - 10.1, h: 1.5, fontSize: 16, bold: true, color: C.background1 });
  txt(s, "Agent Gateway est prêt dans le socle : une variable suffit, le jour où le premier agent qui agit arrive.", { x: 9.85, y: 4.65, w: W - MX - 10.1, h: 1.5, fontSize: 14, color: C.accent6 });
  s.addNotes("Les agents personnalisés et les serveurs MCP font passer l'assistant de répondre à agir : interroger Databricks, appeler une API métier, créer un ticket. C'est précisément l'angle mort du filtrage Model Armor de Gemini Enterprise, qui ne couvre pas les agents ADK ou A2A. Agent Gateway n'apporte presque rien sans agent maison : on ne l'impose pas trop tôt, mais il est prêt dans le socle.");

  // =============================================================== 13. Console vs Terraform
  pres.addSection({ title: "Méthode et zooms" });
  s = slide("CONTENU", "Méthode et zooms", "Méthode", "Console pour apprendre, Terraform pour garantir");
  table(s, ["Élément", "Console (N0)", "Terraform (N1 à N3)", "Reste manuel"], [
    ["App, assistant, recherche web, langue", "Oui", "Oui", "—"],
    ["Identité, rôles, groupes", "Oui", "Oui", "Appartenance aux groupes"],
    ["Model Armor, plancher, DLP France", "Oui", "Oui", "—"],
    ["Connecteurs (Workspace, Microsoft, GitHub, Jira…)", "Oui", "Oui, modèle générique", "OAuth initial, IP côté SaaS"],
    ["Secrets des connecteurs", "—", "Référencés, jamais leur valeur", "Création par la sécurité"],
    ["CMEK", "Possible", "Oui, protégé contre la suppression", "Révocation d'urgence"],
    ["Conservation, observabilité", "Oui", "Par l'API, depuis Terraform", "—"],
    ["Journaux dédiés, exclusions, alertes", "Oui", "Oui", "—"],
    ["Licences", "Oui", "Possible (facturé)", "Attribution en console"],
    ["Agent Gateway, VPC-SC", "Possible", "Oui (options)", "Règles d'entrée VPC-SC"],
  ], MX, 1.7, [4.4, 1.7, 3.3, 2.73], { fontSize: 13 });
  s.addNotes("La console sert à apprendre et vérifier ; Terraform sert à garantir. Le passage se fait sans perte : chaque réglage du niveau 0 est inventorié, puis devient une variable ou une ressource Terraform relue en revue de code. L'app de découverte est supprimée, et la production repart d'un état décrit à 100 % par le code. Une alerte signale ensuite toute modification manuelle des garde-fous.");

  // =============================================================== 14. Model Armor
  s = slide("CONTENU", "Méthode et zooms", "Zoom", "Model Armor : le pare-feu des échanges avec l'IA");
  const flow = [["Question", C.background2, C.text2], ["prompt-shield", C.accent1, C.background1], ["Gemini", C.text2, C.background1], ["response-shield", C.accent1, C.background1], ["Réponse", C.background2, C.text2]];
  const fw = 2.05, gap = (CW - 5 * fw) / 4;
  flow.forEach(([t, f, c], i) => {
    const x = MX + i * (fw + gap);
    card(s, x, 1.75, fw, 0.75, f, "flux" + i);
    txt(s, t, { x, y: 1.75, w: fw, h: 0.75, fontSize: 17, bold: true, color: c, align: "center", valign: "middle" });
    if (i < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + fw + gap * 0.2, y: 1.97, w: gap * 0.6, h: 0.32, fill: { color: C.accent6 }, line: { type: "none" } });
  });
  table(s, ["Filtre", "Ce qu'il détecte", "Réglage"], [
    ["Injection et jailbreak", "« Ignore tes instructions… », consignes cachées", "Seuil moyen"],
    ["Liens malveillants", "Phishing et malware connus", "Activé"],
    ["IA responsable", "Haine, harcèlement, sexuel, dangereux", "Seuil moyen"],
    ["Données sensibles", "NIR, CNI, passeport, IBAN, carte, secrets", "DLP France"],
  ], MX, 2.85, [2.4, 4.1, 1.5], { fontSize: 13 });
  const gar = [["FAIL_CLOSED", "Model Armor indisponible : l'assistant refuse"], ["Plancher", "Aucun filtre moins strict que le minimum"], ["Séparation + alerte", "Seule la sécurité modifie ; tout est signalé"]];
  gar.forEach(([t, d], i) => {
    const y = 2.85 + i * 1.12;
    card(s, 8.85, y, W - MX - 8.85, 0.98, C.background2, "garantie" + i);
    txt(s, t, { x: 9.1, y: y + 0.1, w: 3.5, h: 0.35, fontSize: 16, bold: true, color: C.accent1 });
    txt(s, d, { x: 9.1, y: y + 0.48, w: W - MX - 9.35, h: 0.42, fontSize: 13 });
  });
  txt(s, "Choix assumé : seuil moyen. Un outil qui bloque à tort est contourné ; plancher et détection couvrent le reste.", { x: MX, y: 6.3, w: CW, h: 0.4, fontSize: 14, italic: true, color: C.accent3 });
  s.addNotes("Model Armor analyse chaque question avant le modèle et chaque réponse avant l'utilisateur. C'est un classifieur indépendant du modèle : on ne peut pas le convaincre comme on contourne une consigne. Deux filtres, parce qu'une réponse peut recopier un IBAN trouvé dans un document. Trois garanties : refus si le service est indisponible, plancher qui interdit d'affaiblir les filtres, séparation des rôles avec alerte. E-mails et téléphones ne sont volontairement pas bloqués : ils sont omniprésents dans le travail normal.");

  // =============================================================== 15. Journalisation
  s = slide("CONTENU", "Méthode et zooms", "Zoom", "Journalisation : tout tracer, sans tout exposer");
  table(s, ["Journal", "Contenu", "Stockage UE"], [
    ["Audit d'administration", "Qui a modifié filtres, clés, droits, connecteurs", "Sécurité · 365 j"],
    ["Audit d'accès aux données", "Appels aux API, lectures de secrets", "Sécurité · 365 j"],
    ["Usage Gemini Enterprise", "Qui a demandé quoi, sources, blocages", "Usage · 90 j"],
    ["Texte intégral des échanges", "Questions et réponses complètes", "Désactivé (DPO)"],
    ["Contenu filtré Model Armor", "Texte bloqué, filtre déclenché", "Désactivé (Google)"],
    ["Statistiques d'usage", "Actifs, requêtes, retours", "Console Analytics"],
  ], MX, 1.7, [2.9, 3.8, 1.9], { fontSize: 13 });
  card(s, 9.55, 1.7, W - MX - 9.55, 4.95, C.text2, "rgpd");
  s.addImage({ data: I.eye, x: 9.8, y: 1.95, w: 0.45, h: 0.45 });
  txt(s, "Détecter sans surveiller", { x: 10.4, y: 1.98, w: 2.6, h: 0.4, fontSize: 17, bold: true, color: C.background1 });
  txt(s, "Questions exclues du journal par défaut, lisibles par la sécurité seule. Les blocages sont comptés et alertés sans exposer le contenu.\n\nRGPD : finalité écrite, information des salariés, registre, CSE si contrôle d'activité.",
    { x: 9.8, y: 2.6, w: W - MX - 10.05, h: 3.9, fontSize: 13, color: C.accent6 });
  s.addNotes("Journaliser l'usage d'un outil par les salariés est un traitement de données personnelles. Le dispositif sépare les finalités : la preuve d'audit (un an) et le suivi d'usage (90 jours) n'ont ni la même durée ni les mêmes lecteurs. Les questions sont sorties du journal par défaut, lisible par de nombreux rôles techniques. On enquête en SQL sans copier les journaux. Le socle démarre au plus sobre : toute extension, comme le texte intégral des échanges, se décide avec le DPO.");

  // =============================================================== 16. Risques
  s = slide("CONTENU", "Méthode et zooms", "Couverture", "Onze risques, et le niveau qui les traite");
  table(s, ["#", "Risque", "Exemple", "Mesures", "Niveau"], [
    ["R1", "Accès non autorisé", "Ex-collaborateur, compte partagé", "SSO, groupes", "0 → 1"],
    ["R2", "Divulgation de données", "Un stagiaire retrouve des salaires", "Connecteurs fédérés, DLP", "1"],
    ["R3", "Injection de prompt", "Consigne cachée dans un document", "Model Armor", "0 → 1"],
    ["R4", "Données personnelles", "Un IBAN client collé dans une question", "DLP France", "1"],
    ["R5", "Contenus malveillants", "Lien de phishing relayé", "Model Armor", "0 → 1"],
    ["R6", "Sécurité affaiblie", "Un filtre coupé « pour une démo »", "Rôles, plancher, alerte", "1"],
    ["R7", "Perte de maîtrise", "Données hors UE, non révocables", "UE, CMEK", "0 → 2"],
    ["R8", "Secrets exposés", "Mot de passe dans un dépôt Git", "Secret Manager", "1"],
    ["R9", "Exfiltration", "Export massif, identifiants volés", "IP fixes, VPC-SC", "1 → 3"],
    ["R10", "Abus non détecté", "200 jailbreaks ignorés", "Journaux, alertes", "1 → 2"],
    ["R11", "Agent incontrôlé", "Un agent appelle une API sensible", "Agent Gateway", "3"],
  ], MX, 1.65, [0.7, 2.7, 4.2, 3.33, 1.2], { fontSize: 12 });
  s.addNotes("Chaque risque est nommé, illustré par un exemple concret et rattaché à une mesure et à un niveau. Risques résiduels assumés : une attaque très subtile peut passer le seuil moyen de Model Armor ; en mode fédéré, la question est transmise à l'éditeur de la source ; en cas de panne de Model Armor, l'assistant est indisponible, par choix.");

  // =============================================================== 17. RACI
  pres.addSection({ title: "Organisation et suite" });
  s = slide("CONTENU", "Organisation et suite", "Organisation", "Qui fait quoi");
  table(s, ["Activité", "Sécurité", "Admin Gemini", "DevOps", "DPO", "Métier"], [
    ["Filtres Model Armor, plancher, clés", "R / A", "I", "C", "I", "—"],
    ["Connecteurs et sources", "C", "R", "C", "C", "A"],
    ["Code Terraform, CI/CD", "C (revue)", "C", "R / A", "—", "—"],
    ["Conservation, journalisation du contenu", "C", "I", "I", "A", "C"],
    ["Ouverture à de nouveaux groupes", "C", "R", "I", "I", "A"],
    ["Enquête après alerte", "R / A", "C", "C", "I", "—"],
  ], MX, 1.7, [4.6, 1.5, 1.6, 1.5, 1.4, 1.53], { fontSize: 14 });
  txt(s, "R = réalise · A = approuve · C = consulté · I = informé", { x: MX, y: 5.0, w: CW, h: 0.3, fontSize: 12, color: C.accent3 });
  callout(s, MX, 5.5, CW, 1.15, "Le point clé : la sécurité approuve les garde-fous, le métier approuve l'ouverture, le DPO approuve la conservation. Personne n'est juge et partie.");
  s.addNotes("La gouvernance traduit le principe : personne ne désactive sa propre sécurité. La sécurité possède les garde-fous, l'administrateur Gemini Enterprise exploite l'outil, l'équipe plateforme possède le code et la CI/CD, le DPO arbitre la conservation, le métier décide de l'ouverture.");

  // =============================================================== 18. Planning
  s = slide("CONTENU", "Organisation et suite", "Planning indicatif", "Douze semaines jusqu'à la production");
  const plan = [["S1 – S2", "Niveau 0", "Découverte console, 4 décisions actées"], ["S3 – S6", "Niveau 1", "Socle Terraform, recette, pilote"],
    ["S7 – S12", "Niveau 2", "Production : CMEK, CI/CD, ouverture"], ["Ensuite", "Niveau 3", "Agents, Databricks, VPC-SC"]];
  plan.forEach(([w, l, d], n) => {
    const x = MX + n * (cw4 + 0.3);
    s.addShape(pres.shapes.CHEVRON, { x, y: 1.9, w: cw4, h: 1.0, fill: { color: LV[n] }, line: { type: "none" } });
    txt(s, w, { x: x + 0.35, y: 1.9, w: cw4 - 0.7, h: 1.0, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle" });
    txt(s, l, { x, y: 3.15, w: cw4, h: 0.4, fontSize: 18, bold: true, color: C.text2 });
    txt(s, d, { x, y: 3.6, w: cw4 - 0.2, h: 0.9, fontSize: 14 });
  });
  callout(s, MX, 5.0, CW, 1.4, "Durées indicatives : le chemin critique est rarement technique. Ce sont les décisions (identité, DPO) et les autorisations des sources (Microsoft, GitHub, Atlassian) qu'il faut lancer dès le niveau 0.", "FBF1EA", C.accent4);
  s.addNotes("Le planning est indicatif. Le chemin critique n'est presque jamais le code : ce sont les décisions de gouvernance et les délais d'autorisation côté éditeurs (consentement administrateur Entra ID, GitHub App, Atlassian). D'où l'intérêt de les lancer pendant le niveau 0.");

  // =============================================================== 19. Transparence
  s = slide("CONTENU", "Organisation et suite", "Transparence", "Ce qui reste à valider sur le projet réel");
  table(s, ["Point à confirmer en recette", "Repli si besoin"], [
    ["Localisation du modèle DLP associé à Model Armor en UE", "Autre localisation DLP, ou filtre de base temporaire"],
    ["Paramètres exacts de certains connecteurs (Teams, GitHub)", "Création une fois en console, puis reprise en code"],
    ["Motif de blocage visible dans les journaux d'usage", "Journalisation Model Armor temporaire en recette"],
    ["Opérations surveillées par l'alerte « garde-fou modifié »", "Ajustement du filtre après le premier changement"],
    ["Exclusion effective des questions du journal par défaut", "Vérification dans l'explorateur de journaux"],
  ], MX, 1.7, [6.4, 5.73], { fontSize: 14 });
  callout(s, MX, 5.2, CW, 1.3, "Le socle Terraform est validé syntaxiquement et construit sur la documentation Google d'octobre 2026. Il sera confirmé lors de la recette du niveau 1 : chaque point a sa solution de repli.");
  s.addNotes("Être transparent sur ce qui reste à valider renforce la crédibilité auprès d'une équipe sécurité. Rien de bloquant : chacun de ces points a une solution de repli documentée, et ils seront levés lors de la recette du niveau 1.");

  // =============================================================== 20. Conclusion
  s = slide("SOMBRE", "Organisation et suite", "Conclusion", "Pourquoi cette approche est la bonne");
  const why = [["Démarrer demain", "en console, sans exposer une seule donnée sensible"], ["Décider au bon moment", "les choix irréversibles après avoir appris"],
    ["Sécurité vérifiable", "un risque, une mesure, un test, une trace"], ["Protéger l'adoption", "des réglages mesurés, que personne ne contourne"],
    ["Préparer la suite", "agents, Databricks et périmètre sans refaire le socle"]];
  why.forEach(([t, d], i) => {
    const y = 1.75 + i * 0.78;
    badge(s, MX, y, 0.55, String(i + 1), C.accent1, 16);
    txt(s, [{ text: t + "  ", options: { bold: true, color: C.background1 } }, { text: d, options: { color: C.accent6 } }], { x: MX + 0.8, y, w: 7.2, h: 0.55, fontSize: 17, valign: "middle" });
  });
  card(s, 8.6, 1.75, W - MX - 8.6, 3.6, C.accent1, "prochaine");
  txt(s, "Prochaine étape", { x: 8.9, y: 2.0, w: 3.8, h: 0.45, fontSize: 20, bold: true, color: C.background1 });
  txt(s, "Atelier de deux heures avec sécurité, architecture et DPO pour acter les quatre décisions, puis lancement du niveau 0 dans un projet de découverte dédié.",
    { x: 8.9, y: 2.55, w: W - MX - 9.2, h: 2.6, fontSize: 15, color: C.background1 });
  s.addNotes("Conclure sur l'action. On ne demande pas de valider une architecture abstraite : on propose un atelier court pour prendre les quatre décisions, puis un niveau 0 qui démarre immédiatement, sans risque. Le reste suit, niveau par niveau, avec à chaque marche une validation explicite.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
