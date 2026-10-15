"""Analyste BigQuery : toolset BigQuery d'ADK + contrôle de coût par dry-run.

    python agent.py "Quel est le chiffre d'affaires par catégorie en 2025 ?"

Identifiants : ADC (gcloud auth application-default login) ; modèle via Vertex AI.
"""
import asyncio
import os
import sys
from functools import cache

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.integrations.bigquery import BigQueryToolset
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv()
PROJET = os.environ.get("GOOGLE_CLOUD_PROJECT", "votre-projet")   # projet qui paie les requêtes
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
MAX_OCTETS = int(os.environ.get("MAX_OCTETS", 1_000_000_000))     # 1 Go par requête au maximum
DATASET = "bigquery-public-data.thelook_ecommerce"
TABLES_AUTORISEES = {f"{DATASET}.{t}" for t in
                     ("orders", "order_items", "products", "distribution_centers")}
LABELS = {"formation-lab": "analyste-bigquery"}


@cache
def client_bq():
    from google.cloud import bigquery
    return bigquery.Client(project=PROJET)


def estimer(requete: str) -> dict:
    """Dry-run BigQuery : type d'instruction, tables lues, octets traités. Rien n'est facturé."""
    from google.cloud import bigquery
    job = client_bq().query(requete, job_config=bigquery.QueryJobConfig(
        dry_run=True, use_query_cache=False, labels=LABELS))
    return {"type": job.statement_type, "octets": job.total_bytes_processed or 0,
            "tables": sorted(f"{t.project}.{t.dataset_id}.{t.table_id}"
                             for t in job.referenced_tables)}


def verifier(estimation: dict) -> str | None:
    """Renvoie la raison du refus, ou None si la requête peut partir."""
    if estimation["type"] != "SELECT":
        return f"Seules les requêtes SELECT sont permises (reçu : {estimation['type']})."
    interdites = [t for t in estimation["tables"] if t not in TABLES_AUTORISEES]
    if interdites:
        return (f"Tables non autorisées : {', '.join(interdites)}. Tables permises : "
                + ", ".join(sorted(TABLES_AUTORISEES)) + ".")
    if estimation["octets"] > MAX_OCTETS:
        return (f"Requête trop coûteuse : {estimation['octets'] / 1e6:.0f} Mo estimés, "
                f"plafond {MAX_OCTETS / 1e6:.0f} Mo. Sélectionne moins de colonnes ou filtre.")
    return None


def controle_cout(tool, args: dict, tool_context) -> dict | None:
    """before_tool_callback : dry-run et vérifications AVANT toute exécution réelle."""
    if tool.name == "get_table_info":
        cible = f"{args.get('project_id')}.{args.get('dataset_id')}.{args.get('table_id')}"
        if cible not in TABLES_AUTORISEES:
            return {"status": "ERROR", "error_details": f"Table non autorisée : {cible}."}
        return None
    if tool.name != "execute_sql":
        return None
    try:
        estimation = estimer(args.get("query", ""))
    except Exception as e:  # SQL invalide : le dry-run échoue, on renvoie l'erreur au modèle
        return {"status": "ERROR", "error_details": f"Dry-run refusé : {e}"}
    tool_context.state["estimations"] = tool_context.state.get("estimations", []) + [
        {"sql": args.get("query"), **estimation}]
    raison = verifier(estimation)
    return {"status": "ERROR", "error_details": raison} if raison else None


def modele_avec_reessais() -> Gemini:
    """Quota partagé : on réessaie les 429/503 avec un délai croissant (2 s, 4 s, 8 s...)."""
    return Gemini(model=MODEL, retry_options=types.HttpRetryOptions(initial_delay=2, attempts=6))


def creer_agent(model=None) -> Agent:
    boite_a_outils = BigQueryToolset(
        tool_filter=["get_table_info", "execute_sql"],
        bigquery_tool_config=BigQueryToolConfig(
            write_mode=WriteMode.BLOCKED,          # lecture seule (vérifiée aussi par dry-run)
            maximum_bytes_billed=MAX_OCTETS,       # plafond appliqué par BigQuery lui-même
            max_query_result_rows=50,
            compute_project_id=PROJET, default_project_id=PROJET,
            location="US",                          # thelook_ecommerce est en multirégion US
            application_name="lab-analyste-bigquery", job_labels=LABELS,
        ),
    )
    return Agent(
        name="analyste_bigquery",
        model=model or modele_avec_reessais(),
        description="Répond à des questions e-commerce en interrogeant BigQuery.",
        instruction=f"""Tu es un analyste de données. Tu réponds en français.
Données : jeu public fictif {DATASET} (boutique de vêtements en ligne).
Tables autorisées (et AUCUNE autre) : {', '.join(sorted(TABLES_AUTORISEES))}.
Écris toujours le nom complet des tables entre accents graves, par exemple
`{DATASET}.orders`. Les requêtes s'exécutent dans le projet {PROJET}.

Méthode :
1. Si tu doutes d'une colonne, appelle get_table_info (project_id='bigquery-public-data',
   dataset_id='thelook_ecommerce').
2. Écris UNE requête GoogleSQL SELECT qui calcule directement le résultat final, en ne
   sélectionnant que les colonnes utiles (BigQuery facture les colonnes lues), puis
   appelle execute_sql.
   Ne réponds jamais à partir des métadonnées de get_table_info (nombre de lignes...) :
   elles peuvent être périmées ; calcule toujours le résultat en SQL.
3. Si l'outil renvoie une erreur, corrige la requête (2 essais au maximum). Une fois le
   bon résultat obtenu, ne lance pas d'autre requête : la dernière requête exécutée doit
   être celle que tu cites dans ta réponse.
4. Réponds en trois parties : **Réponse** (chiffres arrondis), **Requête** (bloc sql),
   **Explication** (tables, filtres, limites).
Règles métier (sauf demande contraire) :
- chiffre d'affaires = SUM(order_items.sale_price) sur les articles au statut 'Complete' ;
- la date de référence d'une vente est order_items.created_at (TIMESTAMP, UTC) ;
- les montants n'ont pas de devise précise dans ce jeu fictif : n'écris pas de symbole €.""",
        tools=[boite_a_outils],
        before_tool_callback=controle_cout,
    )


root_agent = creer_agent()


async def demander(question: str, agent=root_agent) -> tuple[str, dict]:
    runner = InMemoryRunner(agent=agent, app_name="analyste_bq")
    s = await runner.session_service.create_session(app_name="analyste_bq", user_id="u")
    reponse, resultats, appels = "", [], []
    async for ev in runner.run_async(
            user_id="u", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=question)])):
        for p in ev.content.parts if ev.content and ev.content.parts else []:
            if p.function_call:
                appels.append(p.function_call.name)
            if p.function_response and p.function_response.name == "execute_sql":
                resultats.append(p.function_response.response)
        if ev.is_final_response() and ev.content and ev.content.parts:
            reponse = "".join(p.text or "" for p in ev.content.parts)
    if not reponse:
        raise RuntimeError("Aucune réponse finale du modèle (quota épuisé ? voir les journaux).")
    s = await runner.session_service.get_session(app_name="analyste_bq", user_id="u",
                                                 session_id=s.id)
    return reponse, {**s.state, "resultats": resultats, "appels": appels}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Combien de commandes ont été passées en 2025 ?"
    print(asyncio.run(demander(q))[0])
