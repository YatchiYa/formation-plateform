"""Ce que les agents partagent : le modèle Gemini, la protection Model Armor et le jeton OAuth de l'utilisateur.

Le même code tourne à trois endroits, sans modification :
  - en local (`adk web`, avec LOCAL_DEV=1) ;
  - sur Cloud Run, en A2A (01-bis-cloud-run-a2a/main.py lit `app`) ;
  - sur Agent Runtime (02-bis-agent-runtime, point d'entrée `agent_runtime_app`).
"""
import json
import os
import urllib.error
import urllib.request

from google.adk.apps import App
from google.adk.integrations.model_armor import ModelArmorConfig, ModelArmorPlugin
from google.adk.models import Gemini

# Réponse quand Model Armor bloque (ou ne peut pas filtrer) : visible dans le chat, à chercher dans les journaux.
BLOQUE = "Désolé, je ne peux pas traiter cette demande : elle a été filtrée par Model Armor."


def acces_modele() -> dict:
    """Comment l'agent joint Gemini, selon les variables d'environnement (la première présente l'emporte) :

      GEMINI_API_KEY   clé de l'API Gemini (Google AI Studio)
      VERTEX_API_KEY   clé d'API Vertex AI (mode express)
      (aucune)         Vertex AI avec l'identité de l'agent, point d'accès « global » : recommandé, aucun secret à gérer

    Déployé, la clé vient de Secret Manager (Terraform : model_api_key_secret), jamais en clair.
    """
    if os.getenv("GEMINI_API_KEY"):
        return {"enterprise": False, "api_key": os.environ["GEMINI_API_KEY"]}  # enterprise=False : force l'API Gemini
    if os.getenv("VERTEX_API_KEY"):
        return {"enterprise": True, "api_key": os.environ["VERTEX_API_KEY"]}   # clé et projet s'excluent : pas de location
    return {"enterprise": True, "location": "global"}


def modele() -> Gemini:
    """Le modèle Gemini, joint selon acces_modele()."""
    acces = acces_modele()
    # ADK lit le mode dans l'environnement (pas dans client_kwargs) pour nettoyer les messages reçus. Sans cela, les
    # métadonnées que Gemini Enterprise met sur chaque morceau de message (A2A) sont gardées et Vertex AI les refuse :
    # « part_metadata parameter is only supported in Gemini Developer API mode » (vu dans le chat, reproduit, corrigé).
    os.environ.setdefault("GOOGLE_GENAI_USE_ENTERPRISE", "true" if acces["enterprise"] else "false")
    return Gemini(model=os.getenv("MODEL", "gemini-3.5-flash"), client_kwargs=acces)


def app_securisee(root_agent) -> App:
    """L'agent + le plugin Model Armor.

    Gemini Enterprise ne filtre PAS les agents ajoutés (Agent Runtime, A2A) : l'agent se filtre lui-même.
    Sans template, il refuse de démarrer, sauf en local (LOCAL_DEV=1).
    """
    plugins = []
    if os.getenv("PROMPT_TEMPLATE"):
        plugins.append(ModelArmorPlugin(config=ModelArmorConfig(
            prompt_template_name=os.environ["PROMPT_TEMPLATE"],
            response_template_name=os.environ["RESPONSE_TEMPLATE"],
            block_on_screening_failure=True,  # Model Armor injoignable => on bloque (mode fermé)
            input_blocked_message=BLOQUE,
            output_blocked_message=BLOQUE,
        )))
    elif os.getenv("LOCAL_DEV") != "1":
        raise RuntimeError("PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants (LOCAL_DEV=1 pour un essai local).")
    return App(name=root_agent.name, root_agent=root_agent, plugins=plugins)


def jeton_utilisateur(tool_context, fournisseur: str = "") -> str | None:
    """Jeton OAuth de l'utilisateur Gemini Enterprise, ou None (autorisation non configurée, ou essai local).

    AUTH_ID = l'ID de l'autorisation créée dans Gemini Enterprise (docs/12-3, partie C). Gemini Enterprise demande le
    consentement à l'utilisateur, puis transmet son jeton à chaque appel :
      - Agent Runtime : AdkApp le range dans l'état de session « temp:AUTH_ID » ;
      - A2A (Cloud Run) : en-tête Authorization, que main.py range sous la même clé.
    « temp: » = jamais écrit dans la session : le jeton ne vit que le temps de la réponse.

    Plusieurs fournisseurs (Agent Runtime seulement, docs/12-1-8) : AUTH_ID="acces-google,acces-atlassian".
    Sans fournisseur : le jeton du 1er ID. jeton_utilisateur(ctx, "atlassian") : celui de l'ID qui contient ce mot.
    """
    ids = [i for i in os.getenv("AUTH_ID", "").split(",") if i]
    if fournisseur:
        ids = [i for i in ids if fournisseur in i]
    return tool_context.state.get(f"temp:{ids[0]}") if ids else None


def recherche_gemini_enterprise(question: str, tool_context) -> dict:
    """Cherche dans les sources connectées à l'app Gemini Enterprise (Drive, SharePoint, Confluence, sites…),
    avec les droits de l'utilisateur : il ne voit que les documents auxquels il a accès.

    Args:
        question: Ce qu'il faut chercher, en quelques mots.
    """
    jeton, engine = jeton_utilisateur(tool_context), os.getenv("GE_ENGINE")
    if not jeton or not engine:
        return {"status": "error", "error_message": "Recherche indisponible : autorisation OAuth (AUTH_ID) ou app (GE_ENGINE) non configurée."}
    loc = engine.split("/")[3]
    host = "discoveryengine.googleapis.com" if loc == "global" else f"{loc}-discoveryengine.googleapis.com"
    req = urllib.request.Request(
        f"https://{host}/v1/{engine}/servingConfigs/default_search:search",
        json.dumps({"query": question, "pageSize": 5}).encode(),
        {"Authorization": f"Bearer {jeton}", "Content-Type": "application/json", "X-Goog-User-Project": engine.split("/")[1]})
    try:
        resultats = json.load(urllib.request.urlopen(req, timeout=30)).get("results", [])
    except urllib.error.HTTPError as e:
        return {"status": "error", "error_message": f"Recherche refusée ({e.code}) : {e.read().decode()[:300]}"}
    docs = []
    for r in resultats:
        d = r.get("document", {}).get("derivedStructData", {})
        docs.append({"titre": d.get("title", ""), "lien": d.get("link", ""),
                     "extrait": " ".join(s.get("snippet", "") for s in d.get("snippets", []))[:400]})
    return {"status": "success", "documents": docs}
