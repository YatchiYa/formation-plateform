"""La réponse : Claude lit les extraits trouvés et répond en les citant. Une recherche puis un appel (pas d'agent) :
le plus simple qui marche, et le moins cher."""

import html
import os

import anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.getenv("CLAUDE_EFFORT", "low")  # questions-réponses : « low » suffit (défaut de l'API : medium)
# Repli côté serveur si Claude décline une requête (modèles qui l'acceptent, API Claude directe).
FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}

SYSTEM = """Tu es l'assistant documentaire de l'équipe. Tu réponds en français, de façon précise et concise.

Règles :
1. Réponds UNIQUEMENT avec ce que disent les extraits fournis dans <documents>. Si la réponse n'y est pas, dis-le
   clairement (« Je ne trouve pas cette information dans les documents. ») et n'invente rien.
2. Cite chaque information avec un lien markdown vers sa source : [titre](lien), en reprenant exactement le titre et
   le lien de l'extrait. Termine par une ligne « Sources : » listant les documents utilisés.
3. Si des documents se contredisent, signale-le en citant les deux.
4. Pour une salutation ou une question sur ton fonctionnement, réponds simplement, sans citer."""

_client = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # ANTHROPIC_API_KEY, ou un profil `ant auth login`
    return _client


def documents_block(hits: list[dict]) -> str:
    q = lambda v: html.escape(v or "", quote=True)
    docs = "\n".join(f'<document index="{i}" titre="{q(h["titre"])}" lien="{q(h["lien"])}">\n{h["texte"]}\n</document>'
                     for i, h in enumerate(hits, 1))
    return f"<documents>\n{docs}\n</documents>" if hits else "<documents>\n(aucun extrait trouvé)\n</documents>"


def answer_stream(question: str, history: list[dict], hits: list[dict]):
    """Génère le texte de la réponse au fil de l'eau. `history` = [{"role": "user"|"assistant", "text": …}]."""
    messages = [{"role": h["role"], "content": h["text"]} for h in history if h.get("text")]
    messages.append({"role": "user", "content": f"{documents_block(hits)}\n\nQuestion : {question}"})
    kwargs = dict(model=MODEL, max_tokens=16000, system=SYSTEM, messages=messages,
                  output_config={"effort": EFFORT}, cache_control={"type": "ephemeral"})
    if MODEL in FALLBACK_MODELS:
        stream = client().beta.messages.stream(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
    else:
        stream = client().messages.stream(**kwargs)
    with stream as s:
        for text in s.text_stream:
            yield text
        final = s.get_final_message()
    if final.stop_reason == "refusal":
        yield "\n\n(La demande a été déclinée par Claude.)"
    elif final.stop_reason == "max_tokens":
        yield "\n\n(Réponse tronquée : limite de longueur atteinte.)"
