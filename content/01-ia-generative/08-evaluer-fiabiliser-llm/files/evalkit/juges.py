"""Adaptateurs de juge : une fonction prompt -> texte. Fixez MODELE_JUGE sur une version précise."""
import os

def juge_claude(prompt):
    import anthropic  # pip install anthropic ; clé dans ANTHROPIC_API_KEY
    msg = anthropic.Anthropic().messages.create(
        model=os.environ.get("MODELE_JUGE", "claude-sonnet-4-5"),
        max_tokens=400, temperature=0,
        messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text

def juge_gemini(prompt):
    from google import genai  # pip install google-genai ; gcloud auth application-default login
    client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"],
                          location=os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1"))
    rep = client.models.generate_content(model=os.environ.get("MODELE_JUGE", "gemini-2.5-flash"),
                                         contents=prompt, config={"temperature": 0})
    return rep.text

# Importé par run_eval.py. JUGE=claude|gemini ; non défini = pas de juge (contrôles par code seuls).
# Choisissez un juge d'une autre famille que l'assistant évalué.
juge = {"claude": juge_claude, "gemini": juge_gemini}.get(os.environ.get("JUGE", ""))
