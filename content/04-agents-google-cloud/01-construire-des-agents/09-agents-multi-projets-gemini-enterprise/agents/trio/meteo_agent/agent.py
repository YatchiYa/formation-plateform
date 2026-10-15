"""Agent MÉTÉO & ÉQUIPEMENT : la météo réelle d'une ville, et quoi porter pour faire son sport.

Deux outils :
  - meteo : météo actuelle + prévisions, via Open-Meteo (gratuit, sans clé, données réelles) ;
  - conseil_equipement : règle des 3 couches, en fonction de la température, de la pluie et du vent.
"""
import json
import urllib.parse
import urllib.request

from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun

# Codes météo WMO (utilisés par Open-Meteo) -> libellé.
CIEL = {0: "ciel dégagé", 1: "plutôt dégagé", 2: "partiellement nuageux", 3: "couvert", 45: "brouillard",
        48: "brouillard givrant", 51: "bruine légère", 53: "bruine", 55: "bruine forte", 61: "pluie faible",
        63: "pluie", 65: "pluie forte", 66: "pluie verglaçante", 67: "pluie verglaçante forte", 71: "neige faible",
        73: "neige", 75: "neige forte", 77: "grains de neige", 80: "averses", 81: "averses fortes",
        82: "averses violentes", 85: "averses de neige", 86: "fortes averses de neige", 95: "orage",
        96: "orage avec grêle", 99: "orage avec forte grêle"}


def _get(url: str, **params) -> dict:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=10) as r:
        return json.load(r)


def meteo(ville: str, jours: int = 1) -> dict:
    """Météo actuelle et prévisions d'une ville (données réelles).

    Args:
        ville: Nom de la ville, ex. "Lille", "Chamonix", "Barcelona".
        jours: Nombre de jours de prévision, de 1 à 7.
    """
    try:
        lieux = _get("https://geocoding-api.open-meteo.com/v1/search", name=ville, count=1, language="fr").get("results")
        if not lieux:
            return {"status": "error", "error_message": f"Ville « {ville} » introuvable."}
        lieu = lieux[0]
        m = _get("https://api.open-meteo.com/v1/forecast", latitude=lieu["latitude"], longitude=lieu["longitude"],
                 timezone="auto", forecast_days=max(1, min(int(jours), 7)),
                 current="temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                 daily="weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max")
    except Exception as e:  # réseau, quota : l'agent l'explique au lieu de planter
        return {"status": "error", "error_message": f"Service météo indisponible : {e}"}
    c, d = m["current"], m["daily"]
    return {
        "status": "success",
        "lieu": f"{lieu['name']} ({lieu.get('country_code', '')})",
        "maintenant": {"temperature_c": c["temperature_2m"], "ressenti_c": c["apparent_temperature"],
                       "pluie_mm": c["precipitation"], "vent_kmh": c["wind_speed_10m"],
                       "ciel": CIEL.get(c["weather_code"], "inconnu")},
        "previsions": [{"date": d["time"][i], "ciel": CIEL.get(d["weather_code"][i], "inconnu"),
                        "min_c": d["temperature_2m_min"][i], "max_c": d["temperature_2m_max"][i],
                        "pluie_mm": d["precipitation_sum"][i], "vent_max_kmh": d["wind_speed_10m_max"][i]}
                       for i in range(len(d["time"]))],
    }


def conseil_equipement(temperature_c: float, pluie_mm: float, vent_kmh: float, activite: str = "") -> dict:
    """Équipement conseillé pour une activité en extérieur (règle des 3 couches).

    Args:
        temperature_c: Température ressentie en °C.
        pluie_mm: Pluie prévue en mm.
        vent_kmh: Vent en km/h.
        activite: Activité prévue, ex. "randonnée", "course à pied", "vélo".
    """
    if temperature_c < 0:
        couches = ["sous-vêtement thermique", "polaire chaude", "veste isolante imperméable"]
        accessoires = ["bonnet", "gants", "tour de cou"]
    elif temperature_c < 10:
        couches = ["sous-vêtement technique manches longues", "polaire légère", "veste coupe-vent"]
        accessoires = ["gants fins", "bandeau"]
    elif temperature_c < 18:
        couches = ["t-shirt technique respirant", "veste légère ou softshell"]
        accessoires = []
    else:
        couches = ["t-shirt technique respirant et léger"]
        accessoires = ["casquette", "crème solaire"] if temperature_c >= 25 else []
    alertes = []
    if pluie_mm >= 1:
        couches[-1] = "veste imperméable et respirante"
        accessoires.append("protection de sac à dos")
    if vent_kmh >= 30:
        alertes.append("vent fort : privilégier un coupe-vent et éviter les crêtes")
    if vent_kmh >= 50:
        alertes.append("rafales dangereuses : reporter les activités exposées (voile, vélo, haute montagne)")
    if temperature_c >= 28:
        alertes.append("chaleur : sortir tôt le matin, boire 500 ml par heure d'effort")
    return {"status": "success", "activite": activite or "sport en extérieur", "couches": couches,
            "accessoires": accessoires, "alertes": alertes}


root_agent = Agent(
    name="meteo_agent",
    model=commun.modele(),
    description="Donne la météo réelle d'une ville (aujourd'hui et jusqu'à 7 jours) et l'équipement conseillé pour faire du sport dehors.",
    instruction=(
        "Tu es l'assistant météo et équipement des équipes Acme. "
        "Pour toute question de météo, appelle toujours l'outil meteo ; ne devine jamais une température. "
        "Si l'utilisateur parle d'une activité ou demande quoi porter, appelle ensuite conseil_equipement avec le "
        "ressenti, la pluie et le vent du jour concerné. Réponds en français, en 5 lignes maximum : "
        "le temps prévu, puis l'équipement, puis les alertes éventuelles."
    ),
    tools=[meteo, conseil_equipement],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
