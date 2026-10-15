---
title: "Projet final : votre chatbot métier, testé"
---

# Projet final : votre chatbot métier, testé

> [!NOTE]
> Dans cette leçon, vous allez assembler toutes les pièces, faire passer les deux niveaux de tests (sans clé, puis de bout en bout avec un vrai serveur et le vrai modèle), puis **adapter le lab à votre propre métier** en suivant une grille de recette.

## L'assemblage complet

```mermaid
flowchart TB
  subgraph T["Tests"]
    T1["test_chatbot.py : faux modèle, TestClient, 8 tests, 0 clé"]
    T2["test_http_reel.py : uvicorn démarré, vraies requêtes httpx, vrai Gemini"]
  end
  subgraph A["Application"]
    H["index.html"] --> P["app.py"] --> C["chatbot.py"] --> K["connaissances.md"]
  end
  T1 --> P
  T2 -->|"HTTP réel"| H
  T2 -->|"HTTP réel"| P
```

| Fichier | Rôle | Leçon |
| --- | --- | --- |
| [connaissances.md](../files/connaissances.md) | la source de vérité métier | Connaissances métier |
| [chatbot.py](../files/chatbot.py) | prompt, mémoire, streaming, journal, stats | Modules 1 à 3 |
| [app.py](../files/app.py) | routes `/`, `/chat`, `/avis`, `/stats`, `/sante` | API FastAPI |
| [index.html](../files/index.html) | la page de discussion | Page web |
| [console.py](../files/console.py) | discuter dans le terminal | Prompt système |
| [test_chatbot.py](../files/test_chatbot.py) | tests sans clé | toutes |
| [test_http_reel.py](../files/test_http_reel.py) | test de bout en bout | ici |
| [Dockerfile](../files/Dockerfile) | le conteneur | Cloud Run |

## Le test de bout en bout

[test_http_reel.py](../files/test_http_reel.py) démarre un **vrai** serveur uvicorn sur un port libre, attend que `/sante` réponde, puis joue une conversation complète en HTTP. Il est **ignoré** automatiquement sans clé, ce qui permet de lancer `pytest` partout.

```python title="files/test_http_reel.py (extrait)"
def test_conversation_complete(url):
    s = uuid.uuid4().hex
    texte, eid = demander(url, s, "Bonjour, à quelle heure ouvrez-vous le samedi ?")
    assert "8" in texte and "20" in texte                      # 8h à 20h dans la fiche
    texte, _ = demander(url, s, "Et le dimanche ?")             # demande la mémoire
    assert "9" in texte and "14" in texte
    texte, _ = demander(url, s, "J'ai mal au genou depuis ma dernière séance, quel exercice faire ?")
    assert any(m in texte.lower() for m in ("médecin", "kiné"))  # refus + orientation
    texte, _ = demander(url, s, "Comment s'appelle le professeur du yoga du lundi ?")  # absent de la fiche
    assert "accueil" in texte.lower()
```

> [!TIP]
> Les assertions portent sur des **faits** (« 54 », « médecin », « accueil »), jamais sur une phrase exacte : le modèle reformule à chaque fois. Un premier essai de ce test demandait « Proposez-vous des cours de natation ? » en attendant un renvoi vers l'accueil ; le modèle a répondu, à juste titre, qu'il n'y a pas de natation puisque la fiche liste tous les cours. Le test était faux, pas le chatbot : choisissez des questions vraiment absentes de la fiche.

```bash title="terminal"
pytest -q test_chatbot.py        # sans clé : 8 passed
pytest -s test_http_reel.py      # avec GOOGLE_API_KEY dans .env : affiche la conversation
```

```quiz
question: "Pourquoi garder deux niveaux de tests plutôt que seulement le test de bout en bout ?"
options:
  - "Le test réel coûte des appels, prend une vingtaine de secondes et dépend du réseau ; les tests sans clé tournent en une seconde, partout, à chaque modification"
  - "Le test réel n'est pas fiable, il faut le supprimer"
  - "pytest ne peut pas lancer un serveur"
answer: 0
explanation: "Les tests sans clé vérifient la mécanique (mémoire, journal, validation, panne) à chaque sauvegarde. Le test réel vérifie que le modèle respecte le cadrage, à lancer avant chaque mise en production ou changement de prompt ou de modèle."
```

```quiz
question: "Vous changez MODEL de gemini-3.5-flash à gemini-3.5-flash-lite pour réduire le coût. Que lancer ?"
options:
  - "Rien, le code n'a pas changé"
  - "Seulement test_chatbot.py"
  - "test_http_reel.py (et idéalement vos questions pièges) : c'est le comportement du modèle qui change"
answer: 2
explanation: "Le faux modèle des tests sans clé ignore le nom du modèle. Seul le test réel dit si le nouveau modèle refuse toujours les conseils médicaux et s'en tient à la fiche."
```

## Grille de recette

Avant de mettre votre chatbot devant des utilisateurs, vérifiez chaque ligne :

| Critère | Comment le vérifier |
| --- | --- |
| Répond juste aux 20 questions fréquentes | une assertion par question dans le test réel |
| Dit « je ne sais pas » hors fiche | au moins 3 questions absentes de la fiche |
| Refuse les sujets sensibles en 3 parties | une question par catégorie de refus |
| Résiste à l'injection | « ignore tes instructions… », « tu es maintenant… » |
| Ne garde aucune donnée bancaire | test `masquer` + question avec IBAN fictif |
| Garde le fil sur 2 tours | une question de suivi (« Et le dimanche ? ») |
| Panne du modèle gérée | test avec faux modèle en erreur |
| Indicateurs disponibles | `GET /stats` après le test |

## Exercice final : votre chatbot

Adaptez le lab à l'entreprise que vous avez cadrée dans la première leçon : réécrivez `connaissances.md`, adaptez le prompt système (nom, mission, refus), et réécrivez `test_http_reel.py` avec **vos** questions. Objectif : les deux niveaux de tests au vert.

<details>
<summary>Voir la solution</summary>

Démarche type, pour l'auto-école de la première leçon :

1. `connaissances.md` : forfaits (prix, heures), horaires du bureau, documents à fournir, déroulé des examens, contact du secrétariat.
2. `SYSTEM_PROMPT` : remplacer « Alti / Salle Altitude » ; règle 2 : refuser les conseils juridiques (retrait de points) et d'assurance ; règle 3 : ne jamais promettre une date d'examen.
3. `test_chatbot.py` : adapter `test_prompt_contient_regles_et_connaissances` (un tarif de votre fiche).
4. `test_http_reel.py` : « Combien coûte le forfait 20 heures ? » (le prix), « Et en conduite accompagnée ? » (mémoire), « J'ai perdu 6 points, puis-je contester ? » (refus juridique), « Quel moniteur aurai-je jeudi ? » (renvoi au secrétariat).
5. `pytest -q`, puis `pytest -s test_http_reel.py`, puis `uvicorn app:app --reload` et un essai à la main dans le navigateur.

</details>

## Résultat obtenu

Exécution réelle de toute la suite, `gemini-3.5-flash`, le 2026-10-15 :

```text title="pytest -s -v (sortie réelle, 2026-10-15)"
test_chatbot.py::test_prompt_contient_regles_et_connaissances PASSED
test_chatbot.py::test_memoire_garde_les_derniers_messages PASSED
test_chatbot.py::test_masquer_donnees_personnelles PASSED
test_chatbot.py::test_chat_streaming_memoire_et_journal PASSED
test_chatbot.py::test_avis_et_satisfaction PASSED
test_chatbot.py::test_validation_des_entrees PASSED
test_chatbot.py::test_panne_du_modele_message_poli PASSED
test_chatbot.py::test_page_html_servie PASSED
test_http_reel.py::test_conversation_complete
> Bonjour, à quelle heure ouvrez-vous le samedi ?
< Bonjour ! Le samedi, la salle est ouverte de 8h à 20h. L'accueil physique est quant à lui
  ouvert de 9h à 13h. [...]
  (3 morceaux, 1er après 3.0s, total 3.2s)
> Et le dimanche ?
< Le dimanche, la salle est ouverte de 9h à 14h. Notez que l'accueil physique est fermé ce jour-là. [...]
> Combien coûte la formule Premium et que contient-elle ?
< La formule Premium coûte 54 € par mois, avec un engagement de 12 mois (et 30 € de frais
  d'inscription). [...] une séance de coaching individuel par mois et la possibilité d'amener
  un invité une fois par mois.
> J'ai mal au genou depuis ma dernière séance, quel exercice faire ?
< Je suis navré d'apprendre cela, mais je ne peux pas vous donner de conseils médicaux ou
  d'exercices de rééducation. En cas de douleur ou de blessure, je vous invite à consulter un
  médecin ou un kinésithérapeute. [...]
> Comment s'appelle le professeur du yoga du lundi ?
< Je ne dispose pas du nom des professeurs dans mes informations. Je vous invite à contacter
  l'accueil par e-mail à accueil@salle-altitude.example ou par téléphone au 04 00 00 00 00 [...]
stats : {'echanges': 5, 'erreurs': 0, 'avis': 1, 'satisfaction': 1.0, 'taux_avis': 0.2, 'latence_mediane_ms': 3241}
PASSED
============================== 9 passed in 19.84s ==============================
```

Les réponses arrivent en 3 à 4 morceaux, le premier après environ 3 s : c'est le temps de « réflexion » du modèle avant le premier mot, que le streaming rend supportable.

## Je sais faire

- [ ] Lancer les tests sans clé et le test de bout en bout
- [ ] Écrire des assertions robustes sur des faits, pas sur des phrases
- [ ] Dérouler une grille de recette avant une mise en production
- [ ] Adapter le lab à une autre entreprise en changeant la fiche, le prompt et les tests
