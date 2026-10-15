"""Tests sans clé d'API : faux modèles scriptés.  pytest -q"""
import asyncio
import json

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import agent as a


class FauxModele(BaseLlm):
    model: str = "faux"
    script: list = []
    appels: int = 0

    async def generate_content_async(self, llm_request, stream=False):
        self.appels += 1
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=self.script.pop(0))]))


def note(n, remarques=("Ajoutez le prix.",)):
    return json.dumps({"clarte": n, "concret": n, "appel_action": n, "ton": n, "correction": n, "remarques": list(remarques)})


TEXTE_OK = "89 EUR HT nimbus.example/audit " + " ".join(["mot"] * 110)


def test_grille_valide_et_refuse():
    assert a.arbitrer(json.loads(note(5)), TEXTE_OK) == (True, [])
    ok, consignes = a.arbitrer(json.loads(note(3)), TEXTE_OK)
    assert not ok and len(consignes) == 5 + 1 + 1      # 5 critères + moyenne + la remarque du critique
    ok, consignes = a.arbitrer({"clarte": 4, "concret": 4, "appel_action": 5, "ton": 4, "correction": 5}, TEXTE_OK)
    assert not ok and consignes[0].startswith("moyenne")   # chaque note >= 4 mais moyenne 4.4 < 4.8
    ok, consignes = a.arbitrer(json.loads(note(5)), "Offre révolutionnaire " + TEXTE_OK)
    assert not ok and any("révolutionnaire" in c for c in consignes)
    ok, consignes = a.arbitrer(json.loads(note(5)), "trop court")
    assert not ok and consignes[0].startswith("longueur") and any("mention obligatoire" in c for c in consignes)


def faux(critiques, revisions):
    modeles = {"redacteur": FauxModele(script=["v0 " + TEXTE_OK]),
               "critique": FauxModele(script=critiques),
               "reviseur": FauxModele(script=revisions)}
    return modeles, (lambda nom: modeles[nom])


def test_boucle_s_arrete_des_que_la_grille_est_satisfaite():
    modeles, f = faux([note(3), note(5)], ["v1 " + TEXTE_OK, "jamais utilisé"])
    etat = asyncio.run(a.rediger("brief", agent=a.construire(f)))
    assert etat["valide"] and etat["tours"] == 2
    assert etat["brouillon"].startswith("v1")
    assert modeles["reviseur"].appels == 1             # pas de réécriture après validation
    assert [h["valide"] for h in etat["historique"]] == [False, True]


def test_boucle_bornee_par_max_iterations():
    n = a.MAX_TOURS
    modeles, f = faux([note(2)] * n, [f"v{i} " + TEXTE_OK for i in range(1, n + 1)])
    etat = asyncio.run(a.rediger("brief", agent=a.construire(f)))
    assert not etat["valide"] and etat["tours"] == n and modeles["critique"].appels == n
