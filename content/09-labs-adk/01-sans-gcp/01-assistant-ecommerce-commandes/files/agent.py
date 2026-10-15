"""Assistant de service client e-commerce (Google ADK 2.10, clé d'API Gemini).

Outils : catalogue, stock, panier (état de session), commande en deux temps
(préparer -> confirmer), statut de livraison, escalade vers un humain.
Garde-fous : deux callbacks déterministes (avant le modèle, avant l'outil).
Données 100 % fictives.
"""
import os
import re

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models import LlmResponse
from google.adk.tools import ToolContext
from google.genai import types

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

# --- « Base de données » fictive -------------------------------------------
CATALOGUE = {
    "CASQ-01": {"nom": "Casque audio sans fil Nova", "prix": 89.0, "stock": 12},
    "CASQ-02": {"nom": "Casque audio filaire Studio", "prix": 49.0, "stock": 0},
    "ENC-01": {"nom": "Enceinte Bluetooth Mini", "prix": 35.0, "stock": 30},
    "CHG-01": {"nom": "Chargeur USB-C 65 W", "prix": 29.0, "stock": 5},
    "CAB-01": {"nom": "Câble USB-C tressé 2 m", "prix": 12.0, "stock": 100},
}
COMMANDES = {
    "CMD-1001": {"statut": "expédiée", "transporteur": "Colis Express", "livraison_prevue": "2026-10-17"},
    "CMD-1002": {"statut": "en préparation", "transporteur": None, "livraison_prevue": "2026-10-20"},
}
ESCALADES: list[str] = []  # file d'attente des conseillers (fictive)
MAX_QUANTITE = 5  # règle métier : au-delà, on passe par le service B2B


# --- Outils (de simples fonctions Python : ADK lit nom, docstring, types) ---
def chercher_produits(requete: str) -> dict:
    """Cherche des produits du catalogue dont le nom contient les mots de la requête.

    Args:
        requete: mots-clés, par exemple "casque" ou "chargeur usb-c".
    """
    mots = requete.lower().split()
    trouves = [
        {"sku": sku, "nom": p["nom"], "prix": p["prix"]}
        for sku, p in CATALOGUE.items()
        if any(m in p["nom"].lower() for m in mots)
    ]
    return {"resultats": trouves} if trouves else {"resultats": [], "message": "Aucun produit trouvé."}


def verifier_stock(sku: str) -> dict:
    """Donne le stock disponible d'un produit.

    Args:
        sku: identifiant produit, par exemple "CASQ-01".
    """
    p = CATALOGUE.get(sku.upper())
    if not p:
        return {"erreur": f"Produit {sku} inconnu."}
    return {"sku": sku.upper(), "stock": p["stock"], "disponible": p["stock"] > 0}


def ajouter_au_panier(sku: str, quantite: int, tool_context: ToolContext) -> dict:
    """Ajoute un produit au panier du client (stocké dans l'état de session).

    Args:
        sku: identifiant produit.
        quantite: nombre d'unités (1 à 5).
    """
    sku = sku.upper()
    p = CATALOGUE.get(sku)
    if not p:
        return {"erreur": f"Produit {sku} inconnu."}
    panier = dict(tool_context.state.get("panier", {}))
    total = panier.get(sku, 0) + quantite
    if quantite < 1 or total > MAX_QUANTITE:
        return {"erreur": f"Quantité refusée : 1 à {MAX_QUANTITE} unités par produit."}
    if total > p["stock"]:
        return {"erreur": f"Stock insuffisant : {p['stock']} disponible(s)."}
    panier[sku] = total
    tool_context.state["panier"] = panier  # on réaffecte : ADK enregistre le changement
    return {"panier": panier}


def calculer_panier(panier: dict) -> dict:
    """Fonction pure : lignes et total d'un panier {sku: quantite}."""
    lignes = [
        {"sku": s, "nom": CATALOGUE[s]["nom"], "quantite": q, "sous_total": CATALOGUE[s]["prix"] * q}
        for s, q in panier.items()
    ]
    return {"lignes": lignes, "total": round(sum(l["sous_total"] for l in lignes), 2)}


def voir_panier(tool_context: ToolContext) -> dict:
    """Affiche le contenu et le total du panier."""
    return calculer_panier(tool_context.state.get("panier", {}))


def preparer_commande(tool_context: ToolContext) -> dict:
    """Prépare la commande et renvoie le récapitulatif à faire valider par le client.

    N'enregistre RIEN : il faut ensuite que le client confirme explicitement.
    """
    panier = tool_context.state.get("panier", {})
    if not panier:
        return {"erreur": "Le panier est vide."}
    recap = calculer_panier(panier)
    tool_context.state["commande_en_attente"] = recap
    tool_context.state["client_a_confirme"] = False
    return {"recapitulatif": recap, "a_faire": "Demander au client de répondre 'je confirme'."}


def confirmer_commande(tool_context: ToolContext) -> dict:
    """Enregistre la commande préparée. À n'appeler qu'après l'accord explicite du client."""
    recap = tool_context.state.get("commande_en_attente")
    if not recap:
        return {"erreur": "Aucune commande en attente : appeler d'abord preparer_commande."}
    numero = f"CMD-{1001 + len(COMMANDES)}"
    COMMANDES[numero] = {"statut": "en préparation", "transporteur": None, "livraison_prevue": "sous 3 jours ouvrés"}
    for ligne in recap["lignes"]:
        CATALOGUE[ligne["sku"]]["stock"] -= ligne["quantite"]
    tool_context.state["panier"] = {}
    tool_context.state["commande_en_attente"] = None
    tool_context.state["derniere_commande"] = numero
    return {"numero": numero, "total": recap["total"]}


def statut_livraison(numero_commande: str) -> dict:
    """Donne le statut de livraison d'une commande.

    Args:
        numero_commande: par exemple "CMD-1001".
    """
    c = COMMANDES.get(numero_commande.upper())
    return {"numero": numero_commande.upper(), **c} if c else {"erreur": "Commande introuvable."}


def escalader_vers_humain(motif: str, tool_context: ToolContext) -> dict:
    """Transmet la conversation à un conseiller humain (remboursement, litige, colère, hors périmètre).

    Args:
        motif: résumé en une phrase de la demande du client.
    """
    ESCALADES.append(motif)
    ticket = f"ESC-{len(ESCALADES):03d}"
    tool_context.state["escalade"] = {"ticket": ticket, "motif": motif}
    return {"ticket": ticket, "delai": "un conseiller répond sous 2 h ouvrées"}


# --- Garde-fous (callbacks) ---------------------------------------------------
CARTE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
CONFIRMATION = re.compile(r"\b(je confirme|oui,? je valide|je valide)\b", re.I)


def garde_fou_entree(callback_context, llm_request):
    """Avant chaque appel au modèle : bloque les numéros de carte, détecte la confirmation."""
    msg = callback_context.user_content
    texte = " ".join(p.text or "" for p in (msg.parts if msg else []))
    if CARTE.search(texte):
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(
            text="Pour votre sécurité, ne partagez jamais votre numéro de carte ici. "
                 "Le paiement se fait uniquement sur la page sécurisée.")]))
    if callback_context.state.get("commande_en_attente") and CONFIRMATION.search(texte):
        callback_context.state["client_a_confirme"] = True
    return None  # None = on laisse le modèle répondre


def garde_fou_outils(tool, args, tool_context):
    """Avant chaque outil : interdit de confirmer une commande sans accord du client."""
    if tool.name == "confirmer_commande" and not tool_context.state.get("client_a_confirme"):
        return {"erreur": "Confirmation du client manquante : montrer le récapitulatif et attendre 'je confirme'."}
    return None  # None = l'outil s'exécute normalement


INSTRUCTION = """Tu es l'assistant du service client de la boutique en ligne « Atelier Son » (fictive).
Tu réponds en français, poliment, en 4 phrases maximum.
- Utilise TOUJOURS les outils pour les prix, le stock et les commandes ; n'invente jamais un prix ou un délai.
- Pour commander : ajouter_au_panier, puis preparer_commande, montre le récapitulatif (lignes + total)
  et demande au client d'écrire « je confirme ». Appelle confirmer_commande seulement après.
- Remboursement, litige, client mécontent ou demande hors boutique : escalader_vers_humain.
Panier actuel : {panier?}"""

root_agent = Agent(
    name="service_client",
    model=MODEL,
    description="Assistant de commandes et de suivi de livraison.",
    instruction=INSTRUCTION,
    tools=[chercher_produits, verifier_stock, ajouter_au_panier, voir_panier,
           preparer_commande, confirmer_commande, statut_livraison, escalader_vers_humain],
    before_model_callback=garde_fou_entree,
    before_tool_callback=garde_fou_outils,
)
