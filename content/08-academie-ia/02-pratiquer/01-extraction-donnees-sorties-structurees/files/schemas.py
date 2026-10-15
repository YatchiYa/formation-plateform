"""Les trois schémas d'extraction, en Pydantic.

Le même modèle Pydantic sert deux fois :
1. il est envoyé à Gemini comme `response_schema` (forme du JSON) ;
2. il valide la réponse (types, contraintes, règles métier).
"""
import re
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

CATALOGUE = {"CAF-1KG", "CAF-250", "THE-200", "TIS-100", "SUC-1KG", "GOB-50"}


class Extraction(BaseModel):
    """Champs communs : l'auto-évaluation du modèle, utilisée pour la revue humaine."""
    confiance: float = Field(ge=0, le=1, description="Confiance globale dans l'extraction, entre 0 et 1.")
    champs_incertains: list[str] = Field(
        description="Noms des champs devinés ou ambigus. Un champ simplement absent (null) n'en fait pas partie.")


# --- CV -------------------------------------------------------------------
class NiveauEtudes(str, Enum):
    BAC = "bac"
    BAC2 = "bac+2"
    BAC3 = "bac+3"
    BAC5 = "bac+5"
    DOCTORAT = "doctorat"


class CV(Extraction):
    nom: str = Field(description="Prénom et nom de la personne.")
    email: Optional[str] = Field(None, description="Adresse e-mail, null si absente.")
    telephone: Optional[str] = Field(None, description="Téléphone tel qu'écrit, null si absent.")
    ville: Optional[str] = Field(None, description="Ville de résidence, null si absente.")
    annees_experience: int = Field(ge=0, le=50, description="Années d'expérience professionnelle, arrondi à l'entier.")
    niveau_etudes: NiveauEtudes = Field(description="Plus haut diplôme obtenu (master ou ingénieur = bac+5, licence = bac+3, BTS/DUT = bac+2).")
    competences: list[str] = Field(description="Compétences techniques citées, une par élément, telles qu'écrites.")

    @field_validator("email")
    @classmethod
    def email_valide(cls, v):
        if v is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", v, re.I):
            raise ValueError(f"e-mail invalide : {v!r}")
        return v


# --- E-mail de commande ---------------------------------------------------
class Urgence(str, Enum):
    NORMALE = "normale"
    URGENTE = "urgente"


class ModeLivraison(str, Enum):
    LIVRAISON = "livraison"
    RETRAIT = "retrait"


class Ligne(BaseModel):
    reference: str = Field(description="Référence produit du catalogue, par exemple CAF-1KG.")
    quantite: int = Field(ge=1, description="Quantité commandée (une douzaine = 12).")

    @field_validator("reference")
    @classmethod
    def reference_connue(cls, v):
        if v not in CATALOGUE:
            raise ValueError(f"référence {v!r} absente du catalogue {sorted(CATALOGUE)}")
        return v


class Commande(Extraction):
    client: str = Field(description="Nom de l'entreprise cliente.")
    contact: str = Field(description="Prénom et nom de la personne qui écrit.")
    lignes: list[Ligne] = Field(min_length=1, description="Lignes de la commande FINALE (tenir compte des corrections).")
    date_livraison: Optional[date] = Field(None, description="Date souhaitée au format AAAA-MM-JJ, calculée à partir de la date de l'e-mail. null si non précisée.")
    urgence: Urgence
    mode: ModeLivraison = Field(description="livraison à l'adresse du client, ou retrait sur place.")


# --- Compte rendu de réunion ---------------------------------------------
class StatutProjet(str, Enum):
    DANS_LES_TEMPS = "dans_les_temps"
    EN_RETARD = "en_retard"
    BLOQUE = "bloque"


class Action(BaseModel):
    responsable: str = Field(description="Prénom de la personne responsable.")
    tache: str = Field(description="La tâche, en quelques mots.")
    echeance: Optional[date] = Field(None, description="Date limite AAAA-MM-JJ, null si aucune.")


class CompteRendu(Extraction):
    projet: str = Field(description="Nom du projet.")
    date_reunion: date
    participants: list[str] = Field(description="Prénoms des participants présents (pas les excusés).")
    statut: StatutProjet
    actions: list[Action] = Field(description="Actions décidées, une par responsable et par tâche.")
    prochaine_reunion: Optional[date] = Field(None, description="Date de la prochaine réunion, null si non fixée.")

    @model_validator(mode="after")
    def echeances_apres_reunion(self):
        for a in self.actions:
            if a.echeance and a.echeance < self.date_reunion:
                raise ValueError(f"échéance {a.echeance} antérieure à la réunion du {self.date_reunion}")
        return self


SCHEMAS = {"cv": CV, "commande": Commande, "compte_rendu": CompteRendu}
