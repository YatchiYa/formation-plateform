"""Tests hors ligne (aucun appel Google) : outils, découverte par Agent Registry, appel inter-agents.

À quoi sert ce script
  Vérifie, sans rien déployer ni appeler Google, le code de l'agent stock (agents/specialist) et de
  l'orchestrateur (agents/orchestrator) : l'outil de stock, la conversion URN -> nom de ressource,
  la recherche
  de l'agent stock dans Agent Registry, l'appel de l'agent distant et l'échec propre en cas de refus (403).
  Le registre et Agent Runtime sont remplacés par de faux objets (FakeRegistry, FakeClient).

Quand l'utiliser
  - docs/06, partie 2.4 (prouver l'appel entre agents, avant query.py) ;
  - docs/10 (rejouer le flux complet) et README, avant `terraform apply` ou après une modification du code.

Prérequis
  - Dans le dossier du projet, venv activé (source .venv/bin/activate), dépendances des agents installées.
  - Aucune configuration, aucune connexion Google, aucun droit : LOCAL_DEV=1 est posé par le script lui-même.

Utilisation
    python scripts/test_agents.py
  Aucun argument, aucune option.

Ce qu'il lit / ce qu'il crée
  Importe agents/specialist/stock_agent et agents/orchestrator/orchestrator_agent. Ne crée, ne modifie et ne
  supprime rien (ni fichier, ni ressource Google). Relançable à volonté.

Résultat attendu
  tests agents OK (5 scénarios)
  (Un avertissement « UserWarning: [EXPERIMENTAL] … » de la bibliothèque ADK peut s'afficher : sans effet.)

Erreurs fréquentes et que faire
  - AssertionError avec une ligne du script : le comportement testé a changé -> lire le scénario (commentaire
    « # 1. » à « # 5. ») et corriger le code de l'agent (ou le test si le changement est voulu).
  - ModuleNotFoundError (google.adk, agentplatform…) : venv non activé ou dépendances non installées.
  - RuntimeError « PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants » : ne doit pas arriver (LOCAL_DEV=1 est posé
    avant les imports) ; vérifier que les imports n'ont pas été déplacés au-dessus.
"""
import asyncio
import os
import sys
import types
from pathlib import Path

# Avant tout import d'agent : autorise les agents à démarrer sans filtre Model Armor (essai local).
os.environ["LOCAL_DEV"] = "1"
ROOT = Path(__file__).resolve().parent.parent / "agents"
sys.path[:0] = [str(ROOT / "specialist"), str(ROOT / "orchestrator")]

from stock_agent import agent as stock  # noqa: E402
from orchestrator_agent import agent as orch  # noqa: E402

# 1. Outil du spécialiste
assert stock.get_store_stock("8771234", "lyon")["stock"] == {"lyon": 0}
assert stock.get_store_stock("nope")["status"] == "error"

# 2. URN Agent Registry -> ressource Agent Runtime
urn = "urn:agent:projects-123:projects:123:locations:europe-west1:reasoningEngines:456"
assert orch.urn_to_resource(urn) == "projects/123/locations/europe-west1/reasoningEngines/456"
reel = "urn:agent:projects-123:projects:123:locations:europe-west1:aiplatform:reasoningEngines:456"   # format constaté en 2026
assert orch.urn_to_resource(reel) == "projects/123/locations/europe-west1/reasoningEngines/456"
try:
    orch.urn_to_resource("urn:agent:projects-1:projects:1:locations:europe-west1:run:services:x")
    raise AssertionError("un service Cloud Run n'est pas appelable via Agent Runtime")
except ValueError:
    pass

# 3. Découverte dans Agent Registry (registre simulé)
class FakeRegistry:
    """Faux Agent Registry : vérifie projet et région demandés, renvoie deux agents dont « stock-agent »."""
    def __init__(self, project_id, location):
        assert (project_id, location) == ("projet-agents", "europe-west1")
    def list_agents(self):
        return {"agents": [{"displayName": "autre", "agentId": "x"}, {"displayName": "stock-agent", "agentId": urn}]}

# On remplace la classe dans son module d'origine : l'orchestrateur l'y cherche au moment de l'appel.
import google.adk.integrations.agent_registry as reg  # noqa: E402
reg.AgentRegistry = FakeRegistry
orch.AGENTS_PROJECT = "projet-agents"
# stock_agent_name() garde son résultat en cache : on le vide pour forcer une nouvelle recherche.
orch.stock_agent_name.cache_clear()
assert orch.stock_agent_name() == "projects/123/locations/europe-west1/reasoningEngines/456"

# 4. Appel de l'agent distant (Agent Runtime simulé)
calls = {}   # ce que l'orchestrateur a transmis, pour vérification

class FakeRemote:
    """Faux agent distant : note l'utilisateur et la question, renvoie un texte puis un appel d'outil."""
    async def async_create_session(self, user_id):
        calls["user"] = user_id
        return {"id": "s1"}
    async def async_stream_query(self, user_id, session_id, message):
        calls["message"] = message
        yield {"content": {"parts": [{"text": "Tente 2 places : 0 à Lyon."}]}}
        yield {"content": {"parts": [{"function_call": {"name": "get_store_stock"}}]}}

class FakeClient:
    """Faux client agentplatform : note le projet et la région, renvoie toujours FakeRemote."""
    def __init__(self, project, location):
        calls["where"] = (project, location)
        self.runtimes = types.SimpleNamespace(get=lambda name: FakeRemote())

orch.agentplatform.Client = FakeClient
ctx = types.SimpleNamespace(user_id="vendeur@acme.example")   # contexte d'outil minimal : l'utilisateur
out = asyncio.run(orch.ask_stock_agent("Stock 8771234 à Lyon ?", ctx))
assert out == {"status": "success", "answer": "Tente 2 places : 0 à Lyon."}, out
assert calls == {"where": ("123", "europe-west1"), "user": "vendeur@acme.example", "message": "Stock 8771234 à Lyon ?"}

# 5. Échec propre si l'agent distant est inaccessible (droit manquant, agent supprimé…)
def boom(project, location):
    """Client qui échoue comme un refus de droit (403)."""
    raise PermissionError("403 aiplatform.reasoningEngines.query denied")
orch.agentplatform.Client = boom
assert asyncio.run(orch.ask_stock_agent("x", ctx))["status"] == "error"

print("tests agents OK (5 scénarios)")
