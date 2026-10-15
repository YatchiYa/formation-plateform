"""Construire le contexte envoyé au modèle : ordre, budget de tokens, résumé glissant."""


def approx_tokens(text: str) -> int:
    """Estimation grossière (environ 4 caractères par token). Pour un chiffre exact :
    client.models.count_tokens(...)."""
    return len(text) // 4 + 1


class RollingSummary:
    """Garde les derniers échanges mot pour mot et résume les plus anciens.

    summarize(ancien_resume, tours) -> nouveau_resume est injecté (LLM en vrai, fonction en test)."""

    def __init__(self, summarize, max_turns: int = 12, keep_last: int = 6):
        self.summarize, self.max_turns, self.keep_last = summarize, max_turns, keep_last
        self.summary, self.turns = "", []   # turns : [(role, texte)], role = "user" | "model"

    def add(self, role: str, text: str):
        self.turns.append((role, text))
        if len(self.turns) > self.max_turns:
            old, self.turns = self.turns[:-self.keep_last], self.turns[-self.keep_last:]
            self.summary = self.summarize(self.summary, old)


def build_context(system: str, facts: list[str], summary: str, turns: list[tuple[str, str]],
                  question: str, budget: int = 6000, count=approx_tokens):
    """Ordre : consignes et faits stables en tête (préfixe stable = cache implicite possible),
    puis le résumé, puis les tours récents, et la question en DERNIER (là où le modèle la voit le mieux).
    Si le budget est dépassé, on retire d'abord les tours les plus anciens, puis les faits les moins pertinents
    (facts est trié du plus au moins pertinent). Renvoie (system_instruction, contents, tokens_estimés)."""
    facts, turns = list(facts), list(turns)

    def render():
        sys = system
        if facts:
            sys += "\n\n## Ce que tu sais de l'utilisateur (mémoire long terme)\n" + "\n".join(f"- {f}" for f in facts)
        if summary:
            sys += "\n\n## Résumé de la conversation jusqu'ici\n" + summary
        contents = [{"role": r, "parts": [{"text": t}]} for r, t in turns]
        contents.append({"role": "user", "parts": [{"text": question}]})
        total = count(sys) + sum(count(t) for _, t in turns) + count(question)
        return sys, contents, total

    sys, contents, total = render()
    while total > budget and (turns or facts):
        if turns:
            turns.pop(0)
        else:
            facts.pop()
        sys, contents, total = render()
    return sys, contents, total


SUMMARY_PROMPT = """Mets à jour le résumé d'une conversation entre un utilisateur et un assistant.
Garde : les décisions, les demandes en cours, les informations données par l'utilisateur.
Supprime : les politesses, les répétitions. Si une information a changé, ne garde que la nouvelle.
120 mots maximum, en français. Réponds uniquement par le texte du résumé, sans titre.

Résumé actuel :
{summary}

Nouveaux échanges à intégrer :
{turns}"""


def llm_summarizer(c, model: str):
    from memoire import with_retry

    def summarize(summary: str, turns: list[tuple[str, str]]) -> str:
        txt = "\n".join(f"{'Utilisateur' if r == 'user' else 'Assistant'} : {t}" for r, t in turns)
        r = with_retry(lambda: c.models.generate_content(
            model=model, contents=SUMMARY_PROMPT.format(summary=summary or "(vide)", turns=txt)))
        return r.text.strip()
    return summarize
