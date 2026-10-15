"""Tests sans clé d'API : règle d'adaptation + persistance SQLite avec un faux modèle.

    pytest -q
"""
import asyncio

from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from agent import APP_NAME, ajuster_niveau, definir_niveau, enregistrer_reponse


class FauxModele(BaseLlm):
    """Rejoue une liste de réponses : un appel d'outil puis un texte, etc."""
    script: list = []

    async def generate_content_async(self, llm_request, stream=False):
        yield LlmResponse(content=types.Content(role="model", parts=[self.script.pop(0)]))


def appel(nom, **args):
    return types.Part(function_call=types.FunctionCall(name=nom, args=args))


def test_ajuster_niveau():
    assert ajuster_niveau(2, [True, True]) == (3, [])
    assert ajuster_niveau(2, [False, False]) == (1, [])
    assert ajuster_niveau(2, [True, False]) == (2, [True, False])
    assert ajuster_niveau(5, [True, True]) == (5, [True, True])  # plafond
    assert ajuster_niveau(1, [False, False]) == (1, [False, False])  # plancher


async def _discuter(db, messages, script):
    service = SqliteSessionService(db)
    agent = Agent(name="tuteur", model=FauxModele(model="faux", script=script),
                  instruction="{user:progression?}", tools=[definir_niveau, enregistrer_reponse])
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=service)
    s = await service.create_session(app_name=APP_NAME, user_id="alice")
    for m in messages:
        async for _ in runner.run_async(user_id="alice", session_id=s.id,
                                        new_message=types.Content(role="user", parts=[types.Part(text=m)])):
            pass
    return (await service.get_session(app_name=APP_NAME, user_id="alice", session_id=s.id)).state


def test_progression_persiste_entre_sessions(tmp_path):
    db = str(tmp_path / "tuteur.db")
    script = [appel("definir_niveau", theme="Python", niveau=2), types.Part(text="Question 1"),
              appel("enregistrer_reponse", theme="python", notion="boucles", correcte=True), types.Part(text="Q2"),
              appel("enregistrer_reponse", theme="python", notion="listes", correcte=True), types.Part(text="Q3"),
              appel("enregistrer_reponse", theme="python", notion="dict", correcte=False), types.Part(text="Q4")]
    etat = asyncio.run(_discuter(db, ["python", "r1", "r2", "r3"], script))
    assert etat["user:progression"]["python"]["niveau"] == 3  # 2 bonnes d'affilée -> +1
    assert etat["user:progression"]["python"]["a_revoir"] == ["dict"]

    # Nouvelle session, nouveau service (= nouveau processus) : la progression « user: » est relue du disque.
    etat2 = asyncio.run(_discuter(db, ["re-bonjour"], [types.Part(text="Bon retour !")]))
    assert etat2["user:progression"]["python"]["bonnes"] == 2
    assert etat2["user:progression"]["python"]["total"] == 3
