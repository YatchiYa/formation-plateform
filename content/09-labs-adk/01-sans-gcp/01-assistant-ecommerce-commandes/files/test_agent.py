"""Tests SANS clé d'API : fonctions pures + vrai Runner ADK piloté par un faux modèle.

Lancer : pytest -q
"""
import asyncio

from google.adk.agents import Agent
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

import agent as boutique


class FauxModele(BaseLlm):
    """Rejoue une liste de réponses écrites d'avance, une par appel au modèle."""
    reponses: list

    async def generate_content_async(self, llm_request, stream=False):
        yield self.reponses.pop(0)


def appel(nom, **args):
    return LlmResponse(content=types.Content(role="model", parts=[
        types.Part(function_call=types.FunctionCall(name=nom, args=args))]))


def texte(t):
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=t)]))


def discuter(reponses_du_modele, messages, etat=None):
    """Joue des messages utilisateur dans une même session ; renvoie (réponses d'outils, état final)."""
    agent = Agent(name="test", model=FauxModele(model="faux", reponses=reponses_du_modele),
                  instruction=boutique.INSTRUCTION, tools=boutique.root_agent.tools,
                  before_model_callback=boutique.garde_fou_entree,
                  before_tool_callback=boutique.garde_fou_outils)

    async def run():
        runner = InMemoryRunner(agent=agent, app_name="t")
        s = await runner.session_service.create_session(app_name="t", user_id="u", state=etat or {})
        sorties = []
        for m in messages:
            async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
                    role="user", parts=[types.Part(text=m)])):
                for p in ev.content.parts if ev.content else []:
                    if p.function_response:
                        sorties.append((p.function_response.name, p.function_response.response))
                    if p.text and ev.is_final_response():
                        sorties.append(("texte", p.text))
        s = await runner.session_service.get_session(app_name="t", user_id="u", session_id=s.id)
        return sorties, s.state
    return asyncio.run(run())


def test_fonctions_pures():
    assert boutique.chercher_produits("casque")["resultats"][0]["sku"] == "CASQ-01"
    assert boutique.verifier_stock("casq-02")["disponible"] is False
    assert boutique.calculer_panier({"CASQ-01": 2, "CAB-01": 1})["total"] == 190.0
    assert "erreur" in boutique.statut_livraison("CMD-9999")


def test_panier_dans_etat_de_session():
    sorties, etat = discuter([appel("ajouter_au_panier", sku="CASQ-01", quantite=2), texte("Ajouté.")],
                             ["Ajoute 2 casques Nova"])
    assert etat["panier"] == {"CASQ-01": 2}


def test_quantite_plafonnee():
    sorties, etat = discuter([appel("ajouter_au_panier", sku="CAB-01", quantite=9), texte("Refusé.")],
                             ["Je veux 9 câbles"])
    assert "erreur" in sorties[0][1] and "panier" not in etat


def test_garde_fou_bloque_confirmation_sans_accord():
    # Le modèle « oublie » de demander l'accord et confirme tout de suite : le callback l'en empêche.
    sorties, etat = discuter(
        [appel("preparer_commande"), appel("confirmer_commande"), texte("...")],
        ["Commande mon panier"], etat={"panier": {"ENC-01": 1}})
    assert sorties[1][0] == "confirmer_commande" and "Confirmation du client manquante" in sorties[1][1]["erreur"]
    assert etat["panier"] == {"ENC-01": 1}  # rien n'a été commandé


def test_commande_apres_je_confirme():
    sorties, etat = discuter(
        [appel("preparer_commande"), texte("Total 35 €. Écrivez « je confirme »."),
         appel("confirmer_commande"), texte("Commande enregistrée.")],
        ["Commande mon panier", "Je confirme"], etat={"panier": {"ENC-01": 1}})
    numero = etat["derniere_commande"]
    assert numero.startswith("CMD-") and etat["panier"] == {}
    assert boutique.statut_livraison(numero)["statut"] == "en préparation"


def test_numero_de_carte_bloque_sans_appeler_le_modele():
    # Liste de réponses vide : si le modèle était appelé, pop() lèverait une erreur.
    sorties, _ = discuter([], ["Voici ma carte 4970 1012 3456 7890"])
    assert "ne partagez jamais" in sorties[0][1]


def test_escalade():
    sorties, etat = discuter([appel("escalader_vers_humain", motif="Demande de remboursement"), texte("Transmis.")],
                             ["Je veux être remboursé"])
    assert etat["escalade"]["ticket"].startswith("ESC-")
