"""Assistant avec mémoire long terme persistante (SQLite + embeddings) et résumé glissant.

Usage interactif : python assistant.py <utilisateur> [memoire.db]
Chaque lancement est une NOUVELLE session : seule la mémoire long terme survit."""
import os
import sys

from dotenv import load_dotenv

import contexte
import memoire

load_dotenv()

MODEL = os.getenv("MODEL", "gemini-3.5-flash")
K = int(os.getenv("RECALL_K", "4"))

SYSTEM = """Tu es l'assistant interne de l'entreprise Atelier. Réponds en français, brièvement.
Utilise ce que tu sais de l'utilisateur quand c'est pertinent, sans le réciter.
Si une information sur l'utilisateur ne figure ni dans ta mémoire ni dans la conversation,
dis que tu ne la connais pas : n'invente jamais."""


class Assistant:
    def __init__(self, c, mem: memoire.Memory | None, user: str, model: str = MODEL,
                 summarize=None, max_turns: int = 12):
        self.c, self.mem, self.user, self.model = c, mem, user, model
        self.conv = contexte.RollingSummary(summarize or contexte.llm_summarizer(c, model), max_turns=max_turns)
        self.last = {}

    def chat(self, message: str, learn: bool = True) -> str:
        recalled = self.mem.recall(self.user, message, K) if self.mem else []
        system, contents, est = contexte.build_context(
            SYSTEM, [t for _, _, t in recalled], self.conv.summary, self.conv.turns, message)
        r = memoire.with_retry(lambda: self.c.models.generate_content(
            model=self.model, contents=contents, config={"system_instruction": system}))
        answer = (r.text or "").strip()
        self.conv.add("user", message)
        self.conv.add("model", answer)
        u = r.usage_metadata
        self.last = {"recalled": recalled, "prompt_tokens": u.prompt_token_count if u else est,
                     "estimated_tokens": est, "memory_ops": None}
        if learn and self.mem:
            # On montre au LLM les faits proches du message : il peut les mettre à jour au lieu de dupliquer.
            known = [(i, t) for _, i, t in recalled]
            ops = memoire.extract_operations(self.c, message, known)
            self.last["memory_ops"] = memoire.apply_operations(self.mem, self.user, ops, {i for i, _ in known})
        return answer


def main(user: str, db: str = "memoire.db"):
    from google import genai
    c = genai.Client()
    mem = memoire.Memory(db, memoire.gemini_embedder(c))
    a = Assistant(c, mem, user)
    print(f"Session de {user} ({len(mem.all(user))} faits en mémoire). Ligne vide pour quitter.")
    while (msg := input("> ").strip()):
        print(a.chat(msg))
        ops = a.last["memory_ops"]
        if ops and any(ops.values()):
            print("   [mémoire]", ops)


if __name__ == "__main__":
    main(*sys.argv[1:])
