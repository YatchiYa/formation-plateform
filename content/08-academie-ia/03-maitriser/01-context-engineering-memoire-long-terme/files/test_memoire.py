"""Tests sans clé ni réseau : python -m pytest -q"""
import json
import re
import zlib
from types import SimpleNamespace as NS

import numpy as np

import assistant
import contexte
import eval_rappel
import memoire


def fake_embed(text, kind="doc"):
    """Sac de mots haché : deux textes qui partagent des mots ont un cosinus élevé."""
    v = np.zeros(256, dtype=np.float32)
    for w in re.findall(r"\w+", text.lower()):
        if len(w) > 2:
            v[zlib.crc32(w.encode()) % 256] += 1
    return v / (np.linalg.norm(v) or 1)


def test_recall_ranks_and_isolates_users(tmp_path):
    m = memoire.Memory(str(tmp_path / "m.db"), fake_embed)
    m.add("camille", "L'utilisateur code en Go")
    m.add("camille", "L'utilisateur habite à Nantes")
    m.add("bob", "L'utilisateur habite à Lille")
    top = m.recall("camille", "dans quelle ville habite l'utilisateur ?", k=1)
    assert top[0][2] == "L'utilisateur habite à Nantes"
    assert all("Lille" not in t for _, _, t in m.recall("camille", "Lille", k=5))  # jamais les faits de bob


def test_memory_persists_across_connections(tmp_path):
    db = str(tmp_path / "m.db")
    memoire.Memory(db, fake_embed).add("camille", "L'utilisateur préfère les prix HT")
    assert memoire.Memory(db, fake_embed).all("camille") == [(1, "L'utilisateur préfère les prix HT")]


def test_apply_operations_only_touches_shown_facts(tmp_path):
    m = memoire.Memory(str(tmp_path / "m.db"), fake_embed)
    a = m.add("camille", "L'utilisateur est dans l'équipe Paiements")
    b = m.add("camille", "L'utilisateur habite à Nantes")
    ops = memoire.Operations(ajouter=["L'utilisateur aime le thé"],
                             remplacer=[memoire.Remplacement(id=a, texte="L'utilisateur est dans l'équipe Logistique"),
                                        memoire.Remplacement(id=b, texte="piratage")],
                             supprimer=[b])
    memoire.apply_operations(m, "camille", ops, allowed_ids={a})
    assert [t for _, t in m.all("camille")] == [
        "L'utilisateur est dans l'équipe Logistique", "L'utilisateur habite à Nantes", "L'utilisateur aime le thé"]
    assert m.history("camille") == [(a, "L'utilisateur est dans l'équipe Paiements", "remplacer")]  # rien n'est perdu


def test_rolling_summary_keeps_last_turns():
    calls = []
    conv = contexte.RollingSummary(lambda s, old: calls.append(len(old)) or f"résumé de {len(old)} tours",
                                   max_turns=4, keep_last=2)
    for i in range(5):
        conv.add("user", f"m{i}")
    assert calls == [3] and conv.summary == "résumé de 3 tours"
    assert conv.turns == [("user", "m3"), ("user", "m4")]


def test_build_context_order_and_budget():
    turns = [("user", "a" * 400), ("model", "b" * 400), ("user", "c" * 40)]
    sys, contents, total = contexte.build_context("SYS", ["fait 1", "fait 2"], "RESUME", turns, "QUESTION?")
    assert sys.index("fait 1") < sys.index("RESUME")              # faits stables avant le résumé
    assert contents[-1]["parts"][0]["text"] == "QUESTION?"          # question en dernier
    _, small, total = contexte.build_context("SYS", ["fait 1"], "", turns, "QUESTION?", budget=40)
    assert [c["parts"][0]["text"][0] for c in small] == ["c", "Q"]  # tours les plus anciens retirés d'abord
    assert total <= 40


class FakeModels:
    """Réponse du chat = les faits vus dans le contexte ; extraction = un fait par message « je ... »."""
    def generate_content(self, model, contents, config):
        if model == memoire.EXTRACT_MODEL:
            msg = contents.split("Dernier message de l'utilisateur :")[1].strip()
            add = [f"L'utilisateur dit : {msg}"] if msg.lower().startswith("je ") else []
            return NS(text=json.dumps({"ajouter": add, "remplacer": [], "supprimer": []}))
        system = config["system_instruction"]
        known = system.split("(mémoire long terme)\n")[1].split("\n\n")[0] if "mémoire long terme" in system else "rien"
        return NS(text=f"Je sais : {known}", usage_metadata=NS(prompt_token_count=42))


def test_assistant_remembers_between_sessions(tmp_path):
    c = NS(models=FakeModels())
    mem = memoire.Memory(str(tmp_path / "m.db"), fake_embed)
    s1 = assistant.Assistant(c, mem, "camille", summarize=lambda s, t: "résumé")
    s1.chat("Je travaille dans l'équipe Logistique")
    s2 = assistant.Assistant(c, memoire.Memory(str(tmp_path / "m.db"), fake_embed), "camille",
                             summarize=lambda s, t: "résumé")  # nouvelle session, nouvelle connexion
    assert "Logistique" in s2.chat("Dans quelle équipe je travaille ?", learn=False)
    s3 = assistant.Assistant(c, mem, "bob", summarize=lambda s, t: "résumé")
    assert "Logistique" not in s3.chat("Dans quelle équipe je travaille ?", learn=False)


def test_eval_passes():
    q = {"expect": ["\\bHT\\b|hors taxe"], "forbid": ["TTC"]}
    assert eval_rappel.passes("Je vous l'indiquerai hors taxe.", q)
    assert not eval_rappel.passes("1 200 euros TTC", q)
    assert eval_rappel.passes("Je ne connais pas sa couleur.", {"forbid": ["rouge"]})
