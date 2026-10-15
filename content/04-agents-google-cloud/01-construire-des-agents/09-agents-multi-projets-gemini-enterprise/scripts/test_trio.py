"""Tests hors ligne des agents du trio (aucun appel Google ni Internet).

À quoi sert ce script
  Vérifie le code des 6 agents de agents/trio (meteo, redaction, traduction, taille, retour, identite) et de
  commun.py, sans rien déployer : outils, Model Armor obligatoire, accès au modèle, jeton OAuth de
  l'utilisateur, points d'entrée pour Agent Runtime et Cloud Run, cohérence du catalogue.
  Les appels réseau (service météo Open-Meteo) sont remplacés par de fausses réponses.

Quand l'utiliser
  - docs/12-1-1, partie 2 (préparer son poste : vérifier que le Python du projet fonctionne) ;
  - docs/12-3, partie 1.4 (après avoir créé un agent avec nouvel_agent.py) ;
  - docs/08 et docs/10, et après toute modification du code d'un agent, avant de déployer.

Prérequis
  - Dans le dossier du projet, venv activé, dépendances installées :
      uv venv -p '>=3.12' .venv && source .venv/bin/activate && uv pip install -r agents/trio/requirements.txt
  - Aucune configuration, aucune connexion Google, aucun droit. Le script règle lui-même LOCAL_DEV,
    PROMPT_TEMPLATE, RESPONSE_TEMPLATE, AUTH_ID, GEMINI_API_KEY et VERTEX_API_KEY pendant les tests.

Utilisation
    python scripts/test_trio.py
  Aucun argument, aucune option.

Ce qu'il lit / ce qu'il crée
  Importe les agents de agents/trio et lit agents/trio/catalogue.json. Ne crée, ne modifie et ne supprime
  rien (ni fichier, ni ressource Google). Relançable à volonté.

Résultat attendu
  tests trio OK (10 scénarios, 9 agents)
  (Un avertissement « UserWarning: [EXPERIMENTAL] … » de la bibliothèque ADK peut s'afficher : sans effet.)

Erreurs fréquentes et que faire
  - AssertionError suivie d'un nom de clé (ex. velo) : une entrée du catalogue n'a pas son dossier
    agents/trio/<dossier>/agent.py, ou sa clé dépasse 15 caractères -> corriger le catalogue ou le dossier.
  - AssertionError ailleurs : le comportement d'un outil a changé -> lire le scénario (commentaires « # 1. »
    à « # 6 quinquies. ») et corriger l'agent, ou le test si le changement est voulu.
  - « l'agent a démarré sans Model Armor » : commun.app_securisee() n'impose plus PROMPT_TEMPLATE.
  - ModuleNotFoundError : venv non activé ou dépendances non installées (voir Prérequis).
  - JSONDecodeError : catalogue.json cassé -> python3 -m json.tool agents/trio/catalogue.json
"""
import importlib
import io
import json
import os
import sys
from pathlib import Path

# Les agents s'importent comme en production : depuis agents/trio (meteo_agent.agent, commun…).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents" / "trio"))

# 1. Sans template Model Armor et hors LOCAL_DEV, un agent refuse de démarrer (mode fermé).
os.environ.pop("LOCAL_DEV", None)
os.environ.pop("PROMPT_TEMPLATE", None)
try:
    importlib.import_module("meteo_agent.agent")
    raise AssertionError("l'agent a démarré sans Model Armor")
except RuntimeError as e:
    assert "PROMPT_TEMPLATE" in str(e)
# L'import raté a laissé meteo_agent à moitié chargé dans sys.modules : on l'efface pour le réimporter.
for m in [m for m in sys.modules if m.startswith("meteo_agent")]:
    del sys.modules[m]

# 2. Avec templates : le plugin Model Armor est bien branché.
os.environ.update(PROMPT_TEMPLATE="projects/p/locations/eu/templates/in", RESPONSE_TEMPLATE="projects/p/locations/eu/templates/out")
from redaction_agent import agent as redaction  # noqa: E402
assert [type(p).__name__ for p in redaction.app.plugins] == ["ModelArmorPlugin"]
assert redaction.app.plugins[0]._config.input_blocked_message.startswith("Désolé")
os.environ.pop("PROMPT_TEMPLATE"); os.environ.pop("RESPONSE_TEMPLATE")
os.environ["LOCAL_DEV"] = "1"

from meteo_agent import agent as meteo  # noqa: E402
from traduction_agent import agent as traduction  # noqa: E402

# 3. Météo : Open-Meteo simulé.
REPONSES = {
    "geocoding": {"results": [{"name": "Lille", "country_code": "FR", "latitude": 50.6, "longitude": 3.1}]},
    "forecast": {"current": {"temperature_2m": 13.6, "apparent_temperature": 10.7, "precipitation": 0.0,
                             "weather_code": 0, "wind_speed_10m": 16.2},
                 "daily": {"time": ["2026-10-08", "2026-10-09"], "weather_code": [63, 61],
                           "temperature_2m_max": [14.2, 17.5], "temperature_2m_min": [9.2, 9.4],
                           "precipitation_sum": [9.2, 6.2], "wind_speed_10m_max": [26.6, 26.3]}},
}
appels = []   # URL demandées, pour vérifier les paramètres envoyés au service météo

def faux_urlopen(url, timeout):
    """Remplace urllib.request.urlopen : renvoie la fausse réponse géocodage ou prévisions selon l'URL."""
    appels.append(url)
    return io.StringIO(json.dumps(REPONSES["geocoding" if "geocoding" in url else "forecast"]))

meteo.urllib.request.urlopen = faux_urlopen
r = meteo.meteo("Lille", jours=2)
assert r["status"] == "success" and r["lieu"] == "Lille (FR)", r
assert r["maintenant"]["ciel"] == "ciel dégagé" and len(r["previsions"]) == 2
assert r["previsions"][0]["ciel"] == "pluie" and "forecast_days=2" in appels[-1]
meteo.meteo("Lille", jours=30); assert "forecast_days=7" in appels[-1]   # borné à 7 jours
REPONSES["geocoding"] = {}
assert meteo.meteo("Xyzzy")["status"] == "error"
# Panne réseau simulée : l'outil doit répondre « indisponible » au lieu de planter.
def panne(url, timeout): raise OSError("réseau coupé")
meteo.urllib.request.urlopen = panne
assert "indisponible" in meteo.meteo("Lille")["error_message"]

froid = meteo.conseil_equipement(-5, 0, 10, "randonnée")
assert len(froid["couches"]) == 3 and "bonnet" in froid["accessoires"]
pluie = meteo.conseil_equipement(12, 4, 55)
assert pluie["couches"][-1] == "veste imperméable et respirante" and len(pluie["alertes"]) == 2
assert "crème solaire" in meteo.conseil_equipement(30, 0, 5)["accessoires"]

# 4. Rédaction.
assert redaction.charte_redactionnelle("E-mail client".replace("E-mail", "email"))["longueur_max_mots"] == 150
assert redaction.charte_redactionnelle("fiche produit")["status"] == "success"
assert redaction.charte_redactionnelle("fax")["status"] == "error"
a = redaction.analyser_texte("Bonjour. Votre commande est prête ! L'atelier l'a réparée.")
assert (a["mots"], a["phrases"], a["lisible"]) == (8, 3, True), a  # « L'atelier » = 1 mot
longue = "mot " * 30 + "."
assert redaction.analyser_texte(longue)["phrases_trop_longues"] and not redaction.analyser_texte(longue)["lisible"]
assert redaction.analyser_texte("")["mots"] == 0

# 5. Traduction.
g = traduction.glossaire("EN")
assert g["termes_imposes"]["retrait en magasin"] == "in-store pickup" and "Quechua" in g["marques_a_ne_pas_traduire"]
assert traduction.glossaire("ja")["status"] == "error"
ok = traduction.verifier_traduction("Tente Quechua en retrait en magasin.", "Quechua tent with in-store pickup.")
assert ok["conforme"], ok
ko = traduction.verifier_traduction("Tente Quechua et chaussures Kiprun.", "Tienda de campaña y zapatillas Kiprun.")
assert ko["problemes"] == ["marque absente de la traduction : Quechua"], ko
assert not traduction.verifier_traduction("Un long texte source à traduire entièrement.", "Hi")["conforme"]

# 6 bis. Accès au modèle : identité Vertex AI par défaut, ou clé d'API (Gemini ou Vertex express).
import commun  # noqa: E402
for k in ("GEMINI_API_KEY", "VERTEX_API_KEY"):
    os.environ.pop(k, None)
assert commun.acces_modele() == {"enterprise": True, "location": "global"}
os.environ["VERTEX_API_KEY"] = "cle-vertex"
assert commun.acces_modele() == {"enterprise": True, "api_key": "cle-vertex"}
os.environ["GEMINI_API_KEY"] = "cle-gemini"   # prioritaire
assert commun.acces_modele() == {"enterprise": False, "api_key": "cle-gemini"}
assert commun.modele().client_kwargs["api_key"] == "cle-gemini"
os.environ.pop("GEMINI_API_KEY"); os.environ.pop("VERTEX_API_KEY")

# 6 ter. Les agents ajoutés avec scripts/nouvel_agent.py (12-3).
from taille_agent import agent as taille  # noqa: E402
from retour_agent import agent as retour  # noqa: E402
assert taille.taille_vetement("haut", 98)["taille"] == "M" and "L" in taille.taille_vetement("haut", 99)["conseil"]
assert taille.taille_vetement("bas", 80)["taille"] == "M"
assert taille.taille_vetement("chapeau", 50)["status"] == "error" and taille.taille_vetement("haut", 9)["status"] == "error"
assert taille.pointure(27, "course")["pointure_eu"] == 42 and taille.pointure(27)["pointure_eu"] == 41
assert taille.pointure(26)["pointure_eu"] == 40
assert retour.regles_retour("chaussures", 40)["retour_possible"] is True
assert retour.regles_retour("montre GPS", 40)["retour_possible"] is False
assert retour.regles_retour("maillot de bain", 2)["retour_possible"] is False
assert retour.regles_retour("maillot de bain", 2, "défectueux")["retour_possible"] is True

# 6 quater. Agent Identité : sans AUTH_ID, sans jeton (le cas avec jeton est testé en vrai, docs/12-3 partie C).
from types import SimpleNamespace  # noqa: E402
from identite_agent import agent as identite  # noqa: E402
assert "AUTH_ID absent" in identite.qui_suis_je(SimpleNamespace(state={}))["raison"]
os.environ["AUTH_ID"] = "acces-test"
assert identite.qui_suis_je(SimpleNamespace(state={}))["authentifie"] is False
# Le jeton de l'utilisateur est rangé dans l'état de session sous « temp:<AUTH_ID> » (par AdkApp sur Agent
# Runtime, par 01-bis-cloud-run-a2a/main.py sur Cloud Run). « temp: » = jamais enregistré dans la session.
assert commun.jeton_utilisateur(SimpleNamespace(state={"temp:acces-test": "ya29.x"})) == "ya29.x"
from courriels_agent import agent as courriels  # noqa: E402  (Gmail : sans jeton -> « Autoriser », sans appel réseau)
assert "Autoriser" in courriels.lire_emails(tool_context=SimpleNamespace(state={}))["error_message"]
# Agent Espace de travail (docs/12-1-8) : plusieurs autorisations, et aucune requête Sheets qui supprime (sans réseau).
from workspace_agent import agent as workspace  # noqa: E402
os.environ["AUTH_ID"] = "acces-google,acces-atlassian"
_ctx = SimpleNamespace(state={"temp:acces-google": "G", "temp:acces-atlassian": "A"})
assert commun.jeton_utilisateur(_ctx) == "G" and commun.jeton_utilisateur(_ctx, "atlassian") == "A"
for _req in ({"deleteSheet": {"sheetId": 0}}, {"updateCells": {}}, {"repeatCell": {"fields": "userEnteredValue"}}):
    assert workspace.sheets_modifier("ID", [_req], tool_context=_ctx)["status"] == "error", _req
os.environ["AUTH_ID"] = "acces-google"
assert "Atlassian" in workspace.jira_chercher(tool_context=_ctx)["error_message"]
os.environ.pop("AUTH_ID")
assert "AUTH_ID absent" in courriels.qui_suis_je(SimpleNamespace(state={}))["error_message"]

# 6 quinquies. Agent Sheets expert : calculs A1 et profil, garde-fous anti-perte, API Google simulée (sans réseau).
from sheets_agent import agent as sheets, grille  # noqa: E402
assert (grille.lettre(0), grille.lettre(27), grille.colonne("AB")) == ("A", "AB", 27)
assert grille.a1_vers_grille("'L''été'!B2:D", {"L'été": 7}) == {"sheetId": 7, "startColumnIndex": 1, "startRowIndex": 1, "endColumnIndex": 4}
assert grille.a1_vers_grille("Ventes!C5", {"Ventes": 0}) == {"sheetId": 0, "startColumnIndex": 2, "startRowIndex": 4, "endColumnIndex": 3, "endRowIndex": 5}
assert grille.grille_vers_a1({"sheetId": 7, "startColumnIndex": 1, "startRowIndex": 1, "endColumnIndex": 4, "endRowIndex": 3}, {7: "L'été"}) == "'L''été'!B2:D3"
_p = grille.profil([["Ville", "CA"], ["Lille", "120"], ["Lille", "120"], ["Lyon", "80,5"]])
assert _p["lignes_en_double"] == 1 and _p["colonnes"][1]["type"] == "nombre" and _p["colonnes"][1]["somme"] == 320.5, _p
assert sheets.root_agent.name == "sheets_agent" and not any("jira" in getattr(t, "__name__", "") for t in sheets.root_agent.tools)
os.environ["AUTH_ID"] = "acces-google"
_ctx = SimpleNamespace(state={"temp:acces-google": "G"})
assert "Autoriser" in sheets.outils_sheets.sheets_infos("ID", tool_context=SimpleNamespace(state={}))["error_message"]
envoyes = []   # (méthode, URL, corps) de chaque appel simulé

def faux_google(req, timeout):
    """Simule l'API Sheets : un onglet « Ventes » contenant Ville/CA, Lille/120."""
    url, corps = req.full_url, json.loads(req.data) if req.data else None
    envoyes.append((req.get_method(), url, corps))
    if "values:batchGet" in url:
        rep = {"valueRanges": [{"values": [["Ville", "CA"], ["Lille", "120"]]}] * url.count("ranges=")}
    elif "values:batchUpdate" in url:
        rep = {"totalUpdatedCells": 4, "responses": [{"updatedRange": "Ventes!A1:B2"}]}
    elif ":batchUpdate" in url:
        rep = {"replies": [{} for _ in corps["requests"]]}
    else:
        rep = {"sheets": [{"properties": {"title": "Ventes", "sheetId": 0}}]}
    return io.BytesIO(json.dumps(rep).encode())

import urllib.request  # noqa: E402
urllib.request.urlopen = faux_google
_s = sheets.outils_sheets
for _req in ({"deleteSheet": {"sheetId": 0}}, {"updateCells": {}}, {"clearBasicFilter": {}}, {"deleteDuplicates": {}},
             {"repeatCell": {"fields": "userEnteredValue"}}, {"repeatCell": {"fields": "*"}}, {"setDataValidation": {"range": {}}},
             {"updateSheetProperties": {"fields": "gridProperties.rowCount"}}, {"updateSheetProperties": {"fields": "*"}}):
    assert _s.sheets_modifier("ID", [_req], tool_context=_ctx)["status"] == "error", _req
assert not envoyes   # refusé AVANT tout appel à Google
_fusion = {"mergeCells": {"range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 2}}}
assert "effacerait" in _s.sheets_modifier("ID", [_fusion], tool_context=_ctx)["error_message"]   # 4 cellules remplies
assert envoyes[-1][0] == "GET"   # la fusion n'a pas été envoyée
_fig = {"updateSheetProperties": {"properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}}
assert _s.sheets_modifier("ID", [_fig], tool_context=_ctx)["requetes_appliquees"] == 1
# Écriture : jamais vider, confirmation avant d'écraser, rien écrit sans elle.
assert "effacer" in _s.sheets_ecrire("ID", [{"plage": "Ventes!A2", "valeurs": [["", "1"]]}], tool_context=_ctx)["error_message"]
_n = len(envoyes)
_r = _s.sheets_ecrire("ID", [{"plage": "Ventes!A1", "valeurs": [["Ville", "CA"], ["Lille", "150"]]}], tool_context=_ctx)
assert _r["status"] == "confirmation_requise" and _r["apercu"][0]["avant"] == "120" and len(envoyes) == _n + 1, _r
_r = _s.sheets_ecrire("ID", [{"plage": "Ventes!A1", "valeurs": [["Ville", "CA"], ["Lille", "150"]]}], confirme=True, tool_context=_ctx)
assert _r["status"] == "success" and envoyes[-1][2]["valueInputOption"] == "USER_ENTERED", _r
assert _s.sheets_ecrire("ID", [{"plage": "Ventes!A1", "valeurs": [["Ville", "CA", "=B2*2"]]}], tool_context=_ctx)["status"] == "success"  # rien d'écrasé
# Tableau croisé : nouvel onglet + pivot dans le même appel, colonnes retrouvées par leur nom.
_r = _s.sheets_tableau_croise("ID", "Ventes!A1:B", ["Ville"], [{"colonne": "CA", "fonction": "sum"}], tool_context=_ctx)
_reqs = envoyes[-1][2]["requests"]
_pivot = _reqs[1]["updateCells"]["rows"][0]["values"][0]["pivotTable"]
assert _r["status"] == "success" and "addSheet" in _reqs[0] and _reqs[0]["addSheet"]["properties"]["sheetId"] == _r["sheetId"]
assert _pivot["rows"][0]["sourceColumnOffset"] == 0 and _pivot["values"][0] == {"summarizeFunction": "SUM", "sourceColumnOffset": 1, "name": "SUM de CA"}
assert "absente" in _s.sheets_tableau_croise("ID", "Ventes!A1:B", ["Pays"], [{"colonne": "CA"}], tool_context=_ctx)["error_message"]
assert "existe déjà" in _s.sheets_tableau_croise("ID", "Ventes!A1:B", ["Ville"], [{"colonne": "CA"}], nouvel_onglet="Ventes", tool_context=_ctx)["error_message"]
assert _s.sheets_chercher("ID", "lil", tool_context=_ctx)["resultats"] == [{"onglet": "Ventes", "cellule": "A2", "valeur": "Lille"}]
assert _s.sheets_graphique("ID", "Ventes!A1:A", tool_context=_ctx)["status"] == "error"   # il faut au moins 1 série
os.environ.pop("AUTH_ID")
import json as _json  # noqa: E402
_cat = _json.load(open(Path(__file__).resolve().parent.parent / "agents" / "trio" / "catalogue.json"))
for _cle, _a in _cat.items():   # chaque entrée du catalogue a son dossier, et la clé respecte la limite de longueur
    assert (Path(__file__).resolve().parent.parent / "agents" / "trio" / _a["dossier"] / "agent.py").exists(), _cle
    assert len(_cle) <= 15, _cle

# 6. Les 9 agents sont prêts pour Agent Runtime (point d'entrée) et décrits pour Gemini Enterprise.
for mod in (meteo, redaction, traduction, taille, retour, identite, courriels, workspace, sheets):
    assert mod.agent_runtime_app is not None and len(mod.root_agent.description) > 40
    assert mod.app.name == mod.root_agent.name

print("tests trio OK (10 scénarios, 9 agents)")
