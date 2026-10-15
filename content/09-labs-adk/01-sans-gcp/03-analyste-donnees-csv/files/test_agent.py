"""Tests SANS clé d'API : message, contrôle des chiffres, et vrai Runner ADK avec un faux
modèle qui imite l'exécution de code de Gemini (code + résultat + image).

Lancer : pytest -q
"""
import asyncio

import pytest
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

import agent as analyste
from run import reference, verifier

PNG = bytes.fromhex("89504e470d0a1a0a")  # en-tête PNG : suffit pour le test


class FauxModele(BaseLlm):
    vus: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        yield LlmResponse(content=types.Content(role="model", parts=[
            types.Part(executable_code=types.ExecutableCode(language="PYTHON", code="print(df.chiffre_affaires.sum())")),
            types.Part(code_execution_result=types.CodeExecutionResult(outcome="OUTCOME_OK", output="414644")),
            types.Part(inline_data=types.Blob(mime_type="image/png", data=PNG)),
            types.Part(text="## Chiffres clés\nCA total : 414 644 €")]))


def test_reference_et_controle():
    ref = reference("ventes.csv")
    assert ref == {"ca_total": 414644, "meilleure_region": "Sud", "ca_meilleure_region": 123269}
    assert verifier("CA : 414 644 €. Sud en tête (123,269 €).", ref) == {"ca_total": True, "meilleure_region": True}
    assert verifier("CA : environ 415 000 €", ref)["ca_total"] is False


def test_message_contient_tout_le_csv():
    msg = analyste.construire_message("Analyse", "ventes.csv")
    assert "144 lignes" in msg.parts[0].text and "2025-12,Ouest,Accessoires" in msg.parts[0].text


def test_csv_trop_gros_refuse(tmp_path):
    gros = tmp_path / "gros.csv"
    gros.write_text("a\n" + "1\n" * (analyste.MAX_LIGNES + 1))
    with pytest.raises(ValueError):
        analyste.construire_message("Analyse", str(gros))


def test_runner_range_le_graphique_en_artefact():
    faux = FauxModele(model="gemini-faux")
    agent = analyste.root_agent.clone(update={"model": faux})

    async def run():
        runner = InMemoryRunner(agent=agent, app_name="t")
        s = await runner.session_service.create_session(app_name="t", user_id="u")
        async for _ in runner.run_async(user_id="u", session_id=s.id,
                                        new_message=analyste.construire_message("Analyse", "ventes.csv")):
            pass
        cles = await runner.artifact_service.list_artifact_keys(app_name="t", user_id="u", session_id=s.id)
        image = await runner.artifact_service.load_artifact(app_name="t", user_id="u", session_id=s.id, filename=cles[0])
        return cles, image

    cles, image = asyncio.run(run())
    assert isinstance(analyste.root_agent.code_executor, BuiltInCodeExecutor)
    assert any(t.code_execution for t in faux.vus[0].config.tools)  # l'outil natif est bien demandé au modèle
    assert len(cles) == 1 and image.inline_data.data == PNG
