// Génère le deck PowerPoint « Gemini Enterprise : note de sécurité Acme » (projet 08).
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
pres.title = "Gemini Enterprise - Note de sécurité Acme";
pres.subject = "Mise en conformité avec la note de sécurité";
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
    { text: { text: "Gemini Enterprise · Note de sécurité Acme · Diffusion restreinte", options: { x: MX, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
});
pres.defineSlideMaster({
  title: "SOMBRE",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: MX, y: 0.35, w: 9, h: 0.3, fontSize: 12, bold: true, color: C.accent6, charSpacing: 1.5, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.65, w: CW - 1.0, h: 0.75, fontSize: 30, bold: true, color: C.background1, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Gemini Enterprise · Note de sécurité Acme · Diffusion restreinte", options: { x: MX, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
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

  // ------------------------------------------------------------ helpers propres au deck 08
  const PH = [C.accent1, C.accent2, C.accent5, C.text2];
  function codeBox(s, x, y, w, h, text, fs) {
    card(s, x, y, w, h, "F4F6FA");
    s.addText(text, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: h - 0.24, isTextBox: true, margin: 0, fontFace: "Consolas", fontSize: fs || 12, color: C.text1, valign: "top" });
  }
  function phaseHeader(s, n, who, dur, doc) {
    badge(s, W - MX - 0.75, 0.45, 0.75, String(n), PH[n - 1], 22);
    [["Qui", who], ["Durée", dur], ["Guide", doc]].forEach(([k, v], i) => {
      const x = MX + i * (CW / 3);
      txt(s, [{ text: k + "  ", options: { bold: true, color: PH[n - 1] } }, { text: v, options: { color: C.text1 } }], { x, y: 1.5, w: CW / 3 - 0.1, h: 0.3, fontSize: 13 });
    });
  }
  function measureCard(s, x, y, w, h, num, title, natif, code, why) {
    card(s, x, y, w, h, C.background2);
    badge(s, x + 0.2, y + 0.2, 0.55, num, C.accent1, 16);
    txt(s, title, { x: x + 0.9, y: y + 0.2, w: w - 1.05, h: 0.55, fontSize: 15, bold: true, color: C.text2, valign: "middle" });
    txt(s, [
      { text: "Natif  ", options: { bold: true, color: C.accent1 } }, { text: natif, options: { breakLine: true } },
      { text: "Code  ", options: { bold: true, color: C.accent1 } }, { text: code, options: { breakLine: true } },
      { text: "Pourquoi  ", options: { bold: true, color: C.accent5 } }, { text: why },
    ], { x: x + 0.2, y: y + 0.9, w: w - 0.4, h: h - 1.0, fontSize: 12, paraSpaceAfter: 6 });
  }

  // =============================================================== 1. Titre
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "TITRE", sectionTitle: "Introduction" });
  s.addText("POUR L'ÉQUIPE PROJET ACME · DEV · DEVOPS · PM · SÉCURITÉ · DPO", { placeholder: "kicker" });
  s.addText("Note de sécurité Acme : de la note à la preuve", { placeholder: "title" });
  s.addText("Gemini Enterprise. Les 10 mesures, activées d'abord en natif dans Google Cloud, puis figées en Terraform, testées et suivies chaque jour.", { placeholder: "body" });
  txt(s, "Octobre 2026 · v1.0 · Diffusion restreinte à l'équipe projet", { x: MX, y: 6.6, w: 8, h: 0.3, fontSize: 12, color: C.accent6 });
  ["Console", "Terraform", "Tests", "Exploitation"].forEach((l, i) => {
    const x = 8.9 + i * 1.0, h = 0.9 + i * 0.8;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 6.3 - h, w: 0.92, h, fill: { color: i < 3 ? PH[i] : "3A4A6B" }, line: { type: "none" } });
    txt(s, `${i + 1}`, { x, y: 6.3 - h + 0.08, w: 0.92, h: 0.35, fontSize: 16, bold: true, color: C.background1, align: "center" });
    txt(s, l, { x: x - 0.05, y: 6.4, w: 1.02, h: 0.3, fontSize: 10, color: C.accent6, align: "center" });
  });
  s.addNotes("Ce deck s'adresse à toute l'équipe : développeurs, DevOps, chefs de projet, sécurité, DPO. Message principal : la note de sécurité n'est pas un document à ranger, c'est une liste de mesures que nous activons, codons, testons et suivons. Chaque mesure aura une preuve.");

  // =============================================================== 2. En une page
  s = slide("CONTENU", "Introduction", "Synthèse", "En une page");
  txt(s, "Le socle (projet 06) couvrait le cœur de la note. Le projet 08 comble les écarts et rend chaque mesure prouvable.", { x: MX, y: 1.45, w: CW, h: 0.4, fontSize: 16, color: C.accent3 });
  const phases = [
    ["Console", "Activer le natif Google, en observation quand c'est possible", "Protection immédiate, on mesure avant de bloquer", "Semaine 1"],
    ["Terraform", "Reprendre chaque réglage en code relu, paliers A → D", "Traçable, reproductible par domaine, sans dérive", "Semaines 2–3"],
    ["Tests", "22 tests, chacun avec son journal de preuve", "Une mesure non prouvée n'existe pas", "Semaines 3–4"],
    ["Exploitation", "Journal quotidien, revues, réponses aux alertes", "Détecter, réagir, prouver à l'audit", "En continu"],
  ];
  phases.forEach(([t, what, why, when], i) => {
    const x = MX + i * (CW / 4), w = CW / 4 - 0.2;
    card(s, x, 2.1, w, 3.3, C.background2);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 2.1, w, h: 0.12, fill: { color: PH[i] }, line: { type: "none" } });
    badge(s, x + 0.25, 2.45, 0.6, String(i + 1), PH[i], 18);
    txt(s, t, { x: x + 1.0, y: 2.45, w: w - 1.1, h: 0.6, fontSize: 19, bold: true, color: C.text2, valign: "middle" });
    txt(s, what, { x: x + 0.25, y: 3.25, w: w - 0.5, h: 0.9, fontSize: 14 });
    txt(s, why, { x: x + 0.25, y: 4.2, w: w - 0.5, h: 0.75, fontSize: 13, color: C.accent3, italic: true });
    txt(s, when, { x: x + 0.25, y: 4.95, w: w - 0.5, h: 0.3, fontSize: 13, bold: true, color: PH[i] });
  });
  callout(s, MX, 5.7, CW, 1.0, "Ajouts du projet 08 : agents protégés, Shadow AI, SIEM, Access Approval, analyse avant indexation, contrôle de sortie, VPC-SC élargi, Agent Registry, journal quotidien, contrôle de conformité.");
  s.addNotes("Quatre phases, dans cet ordre. La console d'abord, parce que la protection n'attend pas le code. Terraform ensuite, parce qu'un réglage manuel ne dure pas. Puis on prouve, puis on exploite au quotidien. Le socle 06 reste valable : on ne refait rien, on complète.");

  // =============================================================== 3. Qui fait quoi
  s = slide("CONTENU", "Introduction", "Organisation", "Qui fait quoi");
  table(s, ["Rôle", "Ce qu'il fait", "Ce qu'il ne peut pas faire"], [
    ["Chef de projet / PM", "Planifie les phases, obtient les décisions, suit le PV de recette et les indicateurs", "—"],
    ["Sécurité (RSSI, SOC)", "Possède Model Armor, clés, journaux ; valide chaque PR garde-fou ; traite les alertes", "Déployer seule : tout passe par la CI"],
    ["DevOps / plateforme", "Phase 1 en console, phase 2 en Terraform via la CI, import de la console", "Modifier un garde-fou sans la sécurité (CODEOWNERS)"],
    ["Développeurs d'agents", "Agent Runtime + Model Armor + confirmation humaine ; Agent Registry", "Exposer un service à Internet, déployer hors CI"],
    ["Admins Gemini Enterprise", "App, connecteurs, ouverture aux groupes", "Toucher aux filtres, aux clés, lire les journaux d'usage"],
    ["DPO", "Journalisation du contenu, durées de conservation", "—"],
  ], MX, 1.55, [2.7, 5.4, 4.03], { fontSize: 13 });
  callout(s, MX, 5.75, CW, 0.95, "Règle d'or : après la phase 2, plus aucune modification de sécurité en console. Toute exception déclenche une alerte et doit correspondre à une PR.");
  s.addNotes("Le point clé : personne ne peut désactiver sa propre sécurité. Les administrateurs de l'app ne touchent ni aux filtres ni aux clés. Les développeurs ne publient pas d'agent hors CI. La sécurité valide, mais ne déploie pas seule.");

  // =============================================================== 4. Les 10 mesures
  pres.addSection({ title: "Les mesures" });
  s = slide("CONTENU", "Les mesures", "Vue d'ensemble", "Les 10 mesures et notre réponse");
  table(s, ["#", "Mesure de la note", "Natif (phase 1)", "Terraform / script (phase 2)", "Statut"], [
    ["1", "Agents sur Agent Runtime", "Plancher Model Armor sur Agent Platform", "90_agents_registry.tf, 30_ai_guardrails.tf", "Couvert"],
    ["2", "Shadow AI", "Politiques d'org, Asset Inventory, SCC", "75_shadow_ai.tf · inventaire", "Couvert (Wiz : hors app)"],
    ["3", "Model Armor", "Templates, réglage de l'app, plancher", "30_ai_guardrails.tf (DLP France)", "Plus strict"],
    ["4", "Journaux, AxT, Access Approval, SIEM", "Audit Logs, AxT, Access Approval", "70, 80, 85_siem_access.tf", "Couvert"],
    ["5", "Filtrage de sortie", "Agent Gateway, IP fixes", "60_advanced.tf, 95_secure_web_proxy.tf", "Couvert (correction)"],
    ["6", "RAG : droits, documents", "Connecteurs fédérés", "scan_before_ingest.py", "Couvert"],
    ["7", "VPC Service Controls", "Dry-run, niveau d'accès", "60_advanced.tf (+ aiplatform)", "Dry-run → appliqué"],
    ["8", "Identité, domaines, rôles", "IdP, groupes", "10_identity_access.tf, tfvars par domaine", "Décision IdP"],
    ["9", "Validation humaine", "Confirmations GE", "require_confirmation, destructiveHint", "Couvert"],
    ["10", "Agent Registry, partage", "Registre, partage désactivé", "90_agents_registry.tf, 50_app.tf", "Couvert"],
  ], MX, 1.5, [0.5, 3.0, 3.3, 3.6, 1.73], { fontSize: 12 });
  s.addNotes("Une ligne par mesure de la note. Chaque mesure a d'abord une réponse native, activable en console, puis une réponse en code. Deux points demandent une décision : le fournisseur d'identité et la quarantaine réseau du Shadow AI, qui relève de l'organisation.");

  // =============================================================== 5. Pourquoi console puis Terraform
  pres.addSection({ title: "Méthode" });
  s = slide("CONTENU", "Méthode", "Méthode", "Pourquoi d'abord la console, puis Terraform ?");
  const args = [
    [I.bolt, "La protection n'attend pas le code", "Journaux d'audit et Model Armor : dix minutes en console. Attendre deux semaines de code, c'est deux semaines sans protection."],
    [I.eye, "Observer avant de bloquer", "Plancher des agents en inspection, VPC-SC en dry-run : on voit ce qui serait bloqué, on règle, sans casser un service."],
    [I.code, "Le code ensuite, pour durer", "Relu (PR), traçable (Git), reproductible pour chaque domaine, vérifiable : le plan montre toute dérive."],
    [I.route, "Rien n'est perdu entre les deux", "Les ressources créées en console sont importées : Terraform les adopte sans les recréer."],
  ];
  args.forEach(([ic, t, d], i) => {
    const x = MX + (i % 2) * (CW / 2), y = 1.6 + Math.floor(i / 2) * 2.55, w = CW / 2 - 0.2;
    card(s, x, y, w, 2.3, C.background2);
    s.addImage({ data: ic, x: x + 0.3, y: y + 0.3, w: 0.5, h: 0.5 });
    txt(s, t, { x: x + 1.0, y: y + 0.25, w: w - 1.2, h: 0.6, fontSize: 18, bold: true, color: C.text2, valign: "middle" });
    txt(s, d, { x: x + 0.3, y: y + 1.0, w: w - 0.6, h: 1.15, fontSize: 14 });
  });
  s.addNotes("C'est la question qu'on nous posera : pourquoi ne pas tout faire en Terraform tout de suite ? Parce que la protection n'attend pas, et parce qu'un contrôle trop strict activé à l'aveugle pousse les équipes vers des IA non maîtrisées, c'est-à-dire le Shadow AI que la note veut éviter. Et rien n'est perdu : on importe.");

  // =============================================================== 6. Calendrier
  s = slide("CONTENU", "Méthode", "Méthode", "Le calendrier");
  table(s, ["Semaine", "Phase", "Livrable", "Critère de sortie"], [
    ["S1", "1 · Console", "Journal de bord des activations", "Audit actif ; Model Armor sur l'app ; plancher agents en inspection"],
    ["S2", "2 · Terraform A", "PR socle + palier A, import de la console", "Plan sans écart ; verify_controls.sh au vert"],
    ["S3", "2 · Terraform B, C", "SIEM ; politiques d'org ; VPC-SC dry-run", "Flux reçu par le SOC ; aucune violation VPC-SC légitime"],
    ["S3–S4", "3 · Tests", "PV de recette des 22 tests", "Tests bloquants OK ; risques résiduels signés"],
    ["S5", "Bascule", "Plancher agents en blocage ; VPC-SC appliqué", "Deux semaines sans faux positif"],
    ["Ensuite", "4 · Exploitation", "Rapports quotidiens et mensuels", "Indicateurs au comité"],
  ], MX, 1.55, [1.3, 2.2, 4.0, 4.63], { fontSize: 14 });
  s.addNotes("Cinq semaines pour passer de la note à une conformité prouvée. La bascule en blocage n'a lieu qu'après deux semaines d'observation : c'est ce qui évite les coupures.");

  // =============================================================== 7–8. Phase 1
  pres.addSection({ title: "Phase 1 · Console" });
  s = slide("CONTENU", "Phase 1 · Console", "Phase 1", "Activer le natif dans la console (1/2)");
  phaseHeader(s, 1, "DevOps + sécurité", "semaine 1", "docs/01-phase1-console.md");
  table(s, ["#", "Action", "Rechercher dans la console", "Réglage clé", "§"], [
    ["1", "Journaux d'audit", "Audit Logs", "Data Read + Write : Discovery Engine, Agent Platform, Model Armor, Secret Manager, Agent Registry", "4"],
    ["2", "Templates Model Armor", "Model Armor", "Région eu ; injection, URL, IA responsable ; données sensibles avancées (DLP France) ; Inspect & Block", "3"],
    ["3", "Model Armor dans l'app", "Gemini Enterprise", "App → Configurations : deux templates ; mode fermé ; rôle Model Armor User", "3"],
    ["4", "Plancher + Agent Platform", "Model Armor", "Paramètres de plancher → Services → Agent Platform : Inspecter uniquement ; Cloud Logging", "1"],
    ["5", "Agent Registry, partage", "Agent Registry", "Agents et MCP enregistrés ; partage d'agents désactivé ; skills sur approbation", "10"],
  ], MX, 2.0, [0.4, 2.4, 2.4, 6.4, 0.53], { fontSize: 12 });
  callout(s, MX, 5.9, CW, 0.85, "Les journaux d'audit en premier : par défaut, qui interroge quoi n'est pas journalisé. Sans eux, aucune enquête n'est possible.");
  s.addNotes("Astuce pratique : la barre de recherche de la console est le moyen le plus fiable de trouver une page, les menus changent souvent. Les cinq premières actions se font dans la journée.");

  s = slide("CONTENU", "Phase 1 · Console", "Phase 1", "Activer le natif dans la console (2/2)");
  phaseHeader(s, 1, "DevOps + sécurité + équipe Cloud centrale", "semaine 1", "docs/01-phase1-console.md");
  table(s, ["#", "Action", "Rechercher dans la console", "Réglage clé", "§"], [
    ["6", "Inventaire Shadow AI", "Asset Inventory", "Ou scripts/shadow_ai_inventory.sh sur l'organisation", "2"],
    ["7", "Politiques d'organisation", "Règles d'administration", "run.allowedIngress, iam.allowedPolicyMemberDomains, gcp.resourceLocations", "2"],
    ["8", "Accès de Google", "Access Transparency / Approval", "AxT sur l'organisation (support Enhanced/Premium) ; Access Approval : tous les services", "4"],
    ["9", "Journaux et SIEM", "Routeur de journaux", "Buckets eu ge-security et ge-usage ; sink Pub/Sub (peut être laissé à Terraform)", "4"],
    ["10", "VPC Service Controls", "VPC Service Controls", "Périmètre dry-run, avec aiplatform ; niveau d'accès IP Acme", "7"],
    ["11", "AI Protection", "Security Command Center", "Si SCC Enterprise/Premium ; sinon Wiz si c'est le standard", "2"],
  ], MX, 2.0, [0.4, 2.4, 2.6, 6.2, 0.53], { fontSize: 12 });
  callout(s, MX, 5.9, CW, 0.85, "Chaque activation est notée dans un journal de bord : il sert à l'import Terraform et de preuve pour l'audit.");
  s.addNotes("Les étapes 7, 8 et 10 demandent des droits d'organisation : à faire avec l'équipe Cloud centrale, qui possède peut-être déjà certains de ces réglages.");

  s = slide("CONTENU", "Phase 1 · Console", "Phase 1 · Zoom", "Les deux réglages qui font la différence");
  card(s, MX, 1.55, CW / 2 - 0.15, 5.1, C.background2);
  txt(s, "Plancher Model Armor sur Agent Platform", { x: MX + 0.3, y: 1.75, w: CW / 2 - 0.6, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
  txt(s, "Dans Gemini Enterprise, Model Armor ne filtre pas les agents personnalisés. Le plancher, avec Agent Platform, filtre chaque appel Gemini du projet : agents, notebooks, scripts. Même si un développeur oublie le plugin.",
    { x: MX + 0.3, y: 2.3, w: CW / 2 - 0.6, h: 1.6, fontSize: 14 });
  txt(s, [{ text: "2 semaines  ", options: { bold: true, color: C.accent1 } }, { text: "Inspecter uniquement → journaux", options: { breakLine: true } },
    { text: "Puis  ", options: { bold: true, color: C.accent5 } }, { text: "Inspecter et bloquer (une ligne Terraform)" }],
  { x: MX + 0.3, y: 4.0, w: CW / 2 - 0.6, h: 0.8, fontSize: 14 });
  codeBox(s, MX + 0.3, 5.0, CW / 2 - 0.6, 1.4, 'armor_agent_platform_mode = "inspect"\n# après 2 semaines sans faux positif :\narmor_agent_platform_mode = "block"', 12);
  const x2 = MX + CW / 2 + 0.15;
  card(s, x2, 1.55, CW / 2 - 0.15, 5.1, C.background2);
  txt(s, "VPC Service Controls en dry-run", { x: x2 + 0.3, y: 1.75, w: CW / 2 - 0.6, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
  txt(s, [
    { text: "Anti-exfiltration : même avec des identifiants volés, rien ne sort du projet.", options: { breakLine: true } },
    { text: "Piège 1  ", options: { bold: true, color: C.accent4 } }, { text: "l'interface GE passe par discoveryengine : sans niveau d'accès, on bloque les utilisateurs.", options: { breakLine: true } },
    { text: "Piège 2  ", options: { bold: true, color: C.accent4 } }, { text: "créer les connecteurs avant d'appliquer.", options: { breakLine: true } },
    { text: "Ajout  ", options: { bold: true, color: C.accent5 } }, { text: "aiplatform et agentregistry dans le périmètre, comme l'exige la note." },
  ], { x: x2 + 0.3, y: 2.3, w: CW / 2 - 0.6, h: 3.0, fontSize: 14, paraSpaceAfter: 8 });
  codeBox(s, x2 + 0.3, 5.4, CW / 2 - 0.6, 1.0, "protoPayload.metadata.@type=\n \"...VpcServiceControlAuditMetadata\"\nprotoPayload.metadata.dryRun=true", 11);
  s.addNotes("Ces deux réglages illustrent la méthode : observer avant de bloquer. Le plancher sur Agent Platform est le filet de sécurité des agents. VPC-SC en dry-run évite la coupure classique où l'on bloque ses propres utilisateurs.");

  // =============================================================== Phase 2
  pres.addSection({ title: "Phase 2 · Terraform" });
  s = slide("CONTENU", "Phase 2 · Terraform", "Phase 2", "Figer en Terraform : quatre paliers");
  phaseHeader(s, 2, "DevOps (exécution), sécurité (revue)", "semaines 2–3", "docs/phase2-terraform/");
  table(s, ["Palier", "Contenu", "Prérequis"], [
    ["A · Projet", "Socle 06 ; audit aiplatform + agentregistry ; plancher Agent Platform ; droits Agent Registry ; alerte Shadow AI", "Droits sur le projet"],
    ["B · SOC", "Export Pub/Sub vers le SIEM, même filtre que le bucket sécurité", "Identité du connecteur SIEM"],
    ["C · Organisation", "Politiques d'org ; VPC-SC + niveau d'accès ; Access Approval", "Rôles org ; AxT ; ID client Workspace"],
    ["D · Réseau", "Secure Web Proxy, liste blanche de domaines", "VPC, sous-réseaux, liste validée"],
  ], MX, 2.0, [2.0, 6.9, 3.23], { fontSize: 14 });
  txt(s, "Reprendre la console sans rien recréer", { x: MX, y: 4.75, w: CW, h: 0.35, fontSize: 16, bold: true, color: C.text2 });
  codeBox(s, MX, 5.15, CW, 1.55, 'import {\n  to = google_model_armor_template.shield["ge-prompt-shield"]        # adresse dans le code\n  id = "projects/PROJECT_ID/locations/eu/templates/ge-prompt-shield"  # ressource existante\n}   # terraform plan -> "1 to import" ; tout "~ update" = un écart à trancher en revue', 12);
  s.addNotes("Un palier, une PR, un test. Le palier A ne demande rien à personne et apporte déjà l'essentiel. B, C et D dépendent d'autres équipes : SOC, équipe Cloud centrale, réseau. Les blocs import permettent de reprendre ce qui a été fait en console.");

  s = slide("CONTENU", "Phase 2 · Terraform", "Phase 2", "Ce qui change par rapport au socle 06");
  table(s, ["Fichier", "Ajout", "§"], [
    ["30_ai_guardrails.tf", "Plancher étendu : integrated_services = AI_PLATFORM, inspect ou block", "1, 3"],
    ["60_advanced.tf", "aiplatform et agentregistry dans le périmètre ; niveau d'accès IP Acme", "7"],
    ["70_detection.tf", "Journaux d'accès aux données pour aiplatform et agentregistry", "4"],
    ["75_shadow_ai.tf (nouveau)", "3 politiques d'organisation ; alerte service public / agent créé", "2"],
    ["85_siem_access.tf (nouveau)", "Pub/Sub, sink, droit du writer ; Access Approval", "4"],
    ["90_agents_registry.tf (nouveau)", "Droits du registre ; agent sur Agent Runtime, identité dédiée, Agent Gateway", "1, 9, 10"],
    ["95_secure_web_proxy.tf (nouveau)", "Proxy, politique, liste blanche, sous-réseau dédié", "5"],
  ], MX, 1.55, [3.8, 7.1, 1.23], { fontSize: 14 });
  callout(s, MX, 5.65, CW, 1.05, "Circuit : PR → plan publié → validation sécurité obligatoire (CODEOWNERS) → apply par la CI → alerte « garde-fou modifié » → verify_controls.sh. Un KO fait échouer le déploiement.");
  s.addNotes("Quatre fichiers nouveaux, trois modifiés. Chaque fichier a sa fiche explicative pour les débutants dans terraform/docs. Le circuit CI est celui que nous avons simulé dans le projet 07.");

  // =============================================================== Mesures détaillées
  pres.addSection({ title: "Mesure par mesure" });
  const mw = CW / 3 - 0.15;
  s = slide("CONTENU", "Mesure par mesure", "Mesure par mesure", "Agents, Shadow AI, Model Armor");
  measureCard(s, MX, 1.55, mw, 5.15, "1", "Agents sur Agent Runtime", "Plancher Model Armor sur Agent Platform.",
    "Identité dédiée, ModelArmorPlugin en mode fermé, refus de démarrer sans Model Armor, sortie Agent Gateway.",
    "Héberger ne filtre rien. Plugin + plancher : deux protections indépendantes. Exception encadrée : MCP sur Cloud Run.");
  measureCard(s, MX + mw + 0.22, 1.55, mw, 5.15, "2", "Shadow AI", "Asset Inventory, politiques d'org, SCC AI Protection.",
    "Cloud Run non public, partage au domaine, UE ; alerte « service public / agent créé » ; inventaire mensuel.",
    "Empêcher coûte moins cher que détecter ; l'inventaire prouve l'état. Quarantaine réseau et Wiz : organisation.");
  measureCard(s, MX + 2 * (mw + 0.22), 1.55, mw, 5.15, "3", "Model Armor", "Templates, réglage de l'app, plancher.",
    "Inspect & Block en entrée et en sortie ; DLP France (NIR, CNI, passeport, IBAN) ; mode fermé.",
    "Plus strict que la note. Le filtre « de base » ne voit ni IBAN ni NIR.");
  s.addNotes("Mesure 1 : le point à retenir est qu'héberger sur Agent Runtime ne protège pas en soi. Mesure 2 : on empêche d'abord, on détecte ensuite, on inventorie chaque mois. Mesure 3 : nous allons plus loin que la note, avec des détecteurs français.");

  s = slide("CONTENU", "Mesure par mesure", "Mesure par mesure", "Journaux, sortie, documents");
  measureCard(s, MX, 1.55, mw, 5.15, "4", "Journaux, AxT, Access Approval, SIEM", "Audit Logs, Access Transparency, Access Approval.",
    "Audit étendu à aiplatform et agentregistry ; buckets UE ; Pub/Sub vers le SIEM ; Access Approval sur tous les services.",
    "Access Approval couvre Gemini Enterprise, Agent Runtime, Model Armor et KMS : pas d'accès Google sans accord.");
  measureCard(s, MX + mw + 0.22, 1.55, mw, 5.15, "5", "Filtrage de sortie", "Agent Gateway, IP fixes des connecteurs.",
    "Agent Gateway ; agent relié à la passerelle ; Secure Web Proxy optionnel, liste blanche.",
    "GE est un SaaS : il ne sort pas par notre VPC. Agent Gateway pour GE et les agents, SWP pour nos charges.");
  measureCard(s, MX + 2 * (mw + 0.22), 1.55, mw, 5.15, "6", "RAG : droits et documents", "Connecteurs fédérés : droits de la source à chaque requête.",
    "scan_before_ingest.py : Model Armor analyse PDF, Office, CSV ; quarantaine ; fail closed.",
    "Model Armor ne voit pas les documents récupérés : on les analyse avant de les publier.");
  s.addNotes("Mesure 5 : c'est la correction la plus importante de la note. Le Secure Web Proxy ne voit pas le trafic de Gemini Enterprise. Mesure 6 : le scanner ferme la porte de l'empoisonnement pour les dépôts que nous alimentons.");

  s = slide("CONTENU", "Mesure par mesure", "Mesure par mesure", "Périmètre, identité, humain, registre");
  const mw4 = CW / 4 - 0.15;
  [["7", "VPC Service Controls", "Dry-run, niveau d'accès.", "aiplatform, agentregistry ajoutés ; IP Acme.", "Le dry-run évite la coupure."],
    ["8", "Identité et domaines", "IdP de l'app, groupes.", "Rôles séparés ; un tfvars et un état par domaine.", "Un domaine compromis n'expose pas les autres."],
    ["9", "Validation humaine", "Confirmations GE, outils destructifs.", "require_confirmation ; destructiveHint.", "Dernier rempart contre l'injection indirecte."],
    ["10", "Agent Registry", "Registre ; partage désactivé.", "Lecture utilisateurs, publication développeurs.", "Hors registre = non gouverné, non joignable."],
  ].forEach(([n, t, a, b, c], i) => measureCard(s, MX + i * (mw4 + 0.2), 1.55, mw4, 5.15, n, t, a, b, c));
  s.addNotes("Mesure 8 : une décision doit être prise avant la production, le fournisseur d'identité. Mesure 9 : la confirmation humaine est la protection qui fonctionne même quand toutes les autres ont été contournées.");

  // =============================================================== Agent modèle
  s = slide("CONTENU", "Mesure par mesure", "Développeurs", "Le modèle d'agent sécurisé");
  codeBox(s, MX, 1.55, 6.6, 4.1, '# §9 : toute écriture passe par un humain\ntools=[get_order,\n  FunctionTool(refund_order,\n    require_confirmation=needs_human)]\n\n# §3 : Model Armor, mode fermé\nModelArmorPlugin(config=ModelArmorConfig(\n  prompt_template_name=os.environ["PROMPT_TEMPLATE"],\n  response_template_name=os.environ["RESPONSE_TEMPLATE"],\n  block_on_screening_failure=True))\n\n# Jamais d\'agent déployé sans Model Armor\nraise RuntimeError("PROMPT_TEMPLATE manquant")', 12);
  const rules = ["Déployé sur Agent Runtime, par la CI", "Identité dédiée par agent", "ModelArmorPlugin, mode fermé", "Refus de démarrer sans Model Armor",
    "require_confirmation sur les écritures", "MCP : readOnlyHint / destructiveHint", "Sortie via Agent Gateway"];
  rules.forEach((r, i) => {
    s.addImage({ data: I.check, x: 7.6, y: 1.65 + i * 0.58, w: 0.3, h: 0.3 });
    txt(s, r, { x: 8.05, y: 1.6 + i * 0.58, w: 4.7, h: 0.4, fontSize: 15, valign: "middle" });
  });
  callout(s, MX, 5.9, CW, 0.8, "Essai local : LOCAL_DEV=1 adk web .  →  « Rembourse 10 € sur CMD-1002 »  →  l'interface demande une confirmation.");
  s.addNotes("Chaque agent personnalisé suit ce modèle. Trois mesures de la note sont dans le code : Model Armor, confirmation humaine, et le refus de démarrer sans protection. Les développeurs peuvent l'essayer en local en deux minutes.");

  // =============================================================== Phase 3
  pres.addSection({ title: "Phase 3 · Tests" });
  s = slide("CONTENU", "Phase 3 · Tests", "Phase 3", "Prouver : 22 tests, un journal par test");
  phaseHeader(s, 3, "sécurité (exécution), PM (suivi)", "semaines 3–4", "docs/03-plan-de-tests.md");
  table(s, ["#", "Test", "Attendu", "Preuve"], [
    ["T01–T07", "Jailbreak, IBAN, carte, NIR, URL ; affaiblir un template", "Bloqués ; plancher refuse", "Script ; audit"],
    ["T08–T10", "Jailbreak vers l'agent ; appel Gemini direct", "Bloqué ; journalisé puis bloqué", "SanitizeOperationLogEntry"],
    ["T11–T12", "Remboursement ; outil MCP destructif", "Confirmation demandée", "Interface, traces"],
    ["T13–T15", "Lien externe inconnu ; fichier de B ; PDF piégé", "Non chargé ; invisible ; quarantaine", "Navigateur ; CSV"],
    ["T16–T19", "Hors groupe ; admin GE ; allUsers ; agent hors CI", "Refusés ou alerte", "PERMISSION_DENIED ; e-mail"],
    ["T20–T22", "verify_controls ; PR template ; hors réseau", "Tout OK ; alerte + SIEM ; violation", "Sortie ; SIEM ; VPC-SC"],
  ], MX, 2.0, [1.4, 4.5, 3.3, 2.93], { fontSize: 13 });
  callout(s, MX, 5.75, CW, 0.95, "Passage en production : T01–T12, T14, T16, T17, T20, T21 OK. Les autres OK, ou risque accepté par écrit par le RSSI.", "E8F3EC", C.accent5);
  s.addNotes("Une mesure non prouvée n'existe pas. Chaque test a un résultat attendu et un journal qui le prouve. verify_controls.sh donne en une commande une ligne OK ou KO par mesure : c'est la preuve d'audit la plus simple.");

  // =============================================================== Phase 4
  pres.addSection({ title: "Phase 4 · Exploitation" });
  s = slide("CONTENU", "Phase 4 · Exploitation", "Phase 4", "Exploiter : le journal quotidien");
  phaseHeader(s, 4, "sécurité / SOC", "10 min par jour", "docs/04-exploitation-journaliere.md");
  table(s, ["Fréquence", "Quoi", "Outil"], [
    ["Chaque jour", "Changements, blocages, Shadow AI, accès refusés, VPC-SC ; alertes", "daily_report.sh, Alerting"],
    ["Chaque semaine", "Faux positifs Model Armor ; nouveaux agents au registre", "Log Analytics, Agent Registry"],
    ["Chaque mois", "Conformité et inventaire Shadow AI archivés", "verify_controls.sh, shadow_ai_inventory.sh"],
    ["Chaque trimestre", "Groupes, liste blanche, conservation, exceptions", "IAM, terraform.tfvars"],
  ], MX, 2.0, [2.2, 5.6, 4.33], { fontSize: 14 });
  table(s, ["Journal", "Où", "Durée"], [
    ["Audit admin et accès aux données, verdicts Model Armor, VPC-SC", "Bucket ge-security", "365 j"],
    ["Usage Gemini Enterprise (contient des questions)", "ge-usage, sécurité seule", "90 j"],
    ["Copie temps réel pour le SOC", "Pub/Sub → SIEM", "Selon SOC"],
  ], MX, 4.55, [6.6, 3.8, 1.73], { fontSize: 13 });
  s.addNotes("Dix minutes par jour suffisent. Le script produit un tableau avec des seuils d'action clairs. Les journaux sont dans deux buckets européens, l'un lisible seulement par la sécurité. Dans la console : Logs Explorer, Affiner la portée, Stockage.");

  s = slide("CONTENU", "Phase 4 · Exploitation", "Phase 4", "Quand une alerte sonne");
  table(s, ["Alerte", "Première question", "Si la réponse est non"], [
    ["Garde-fou modifié", "Une PR Terraform correspond ?", "Incident : terraform apply remet la configuration validée ; retirer les droits ; RSSI"],
    ["Pic de blocages", "Un seul utilisateur, ou beaucoup ?", "Un seul : abus (charte). Beaucoup : faux positif, ajuster par PR"],
    ["Service public / agent créé", "PR et inscription au registre ?", "Contacter l'auteur ; retirer allUsers, arrêter ou régulariser"],
    ["Demande Access Approval", "Le ticket support est-il connu ?", "Refuser ; sinon approuver pour la durée minimale"],
    ["Fuite suspectée", "—", "Retirer l'accès ; désactiver la clé KMS si besoin ; exporter les journaux ; DPO (72 h)"],
  ], MX, 1.55, [2.8, 3.4, 5.93], { fontSize: 14 });
  s.addNotes("Une seule question à se poser pour chaque alerte, et une conduite à tenir si la réponse est non. Le cas le plus fréquent sera la modification légitime par une PR : on vérifie, on clôt.");

  // =============================================================== Corrections
  pres.addSection({ title: "Corrections et suite" });
  s = slide("CONTENU", "Corrections et suite", "Transparence", "Sept points de la note à corriger");
  table(s, ["#", "La note dit", "La réalité", "Ce que nous faisons"], [
    ["1", "Exemple JSON Model Armor", "Champs invalides : refusé par l'API", "Syntaxe correcte dans le code"],
    ["2", "Config de base = données Acme", "Orientée US : ni IBAN, ni NIR, ni CNI", "Config avancée, DLP France"],
    ["3", "« Detect and redact »", "Dans GE, une détection bloque", "« Détecter et bloquer »"],
    ["4", "Filtre d'URL = Echo Leak couvert", "Seulement les URL connues", "Test T13, sortie, humain"],
    ["5", "Model Armor protège tous les modèles", "Pas les agents personnalisés dans GE", "Plugin + plancher Agent Platform"],
    ["6", "Le SWP filtre la sortie de l'IA", "GE ne sort pas par notre VPC", "Agent Gateway ; SWP pour nos charges"],
    ["7", "WIF Entra / Okta", "Pas de connecteurs Workspace ; changer efface l'historique", "Décision avant la production"],
  ], MX, 1.55, [0.5, 3.6, 4.3, 3.73], { fontSize: 13 });
  s.addNotes("Corriger la note n'est pas la critiquer : c'est éviter qu'un auditeur ou une équipe s'appuie sur une protection qui n'existe pas. Chaque correction a sa source dans la documentation Google, listée dans docs/05.");

  s = slide("SOMBRE", "Corrections et suite", "Conclusion", "Pourquoi cette approche est la bonne");
  const why = [["Protéger dès la semaine 1", "avec le natif Google, sans attendre le code"], ["Ne rien casser", "ce qui peut bloquer passe d'abord par l'observation"],
    ["Durer", "tout finit en code relu, reproductible par domaine"], ["Se prouver", "22 tests, une commande de conformité, un journal quotidien"],
    ["Corriger la note", "là où elle promettait ce qui n'existe pas"]];
  why.forEach(([t, d], i) => {
    const y = 1.75 + i * 0.78;
    badge(s, MX, y, 0.55, String(i + 1), C.accent1, 16);
    txt(s, [{ text: t + "  ", options: { bold: true, color: C.background1 } }, { text: d, options: { color: C.accent6 } }], { x: MX + 0.8, y, w: 7.2, h: 0.55, fontSize: 17, valign: "middle" });
  });
  card(s, 8.6, 1.75, W - MX - 8.6, 3.6, C.accent1, "prochaine");
  txt(s, "Prochaine étape", { x: 8.9, y: 2.0, w: 3.8, h: 0.45, fontSize: 20, bold: true, color: C.background1 });
  txt(s, "Atelier de deux heures (sécurité, plateforme, PM, DPO) pour acter les quatre décisions : IdP, SIEM, Access Transparency, exception MCP. Puis phase 1 dans le projet de recette.",
    { x: 8.9, y: 2.55, w: W - MX - 9.2, h: 2.6, fontSize: 15, color: C.background1 });
  s.addNotes("Conclure sur l'action : un atelier court pour les quatre décisions, puis la phase 1 démarre immédiatement. Tout le reste est prêt : code, scripts, guides, plan de tests.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
