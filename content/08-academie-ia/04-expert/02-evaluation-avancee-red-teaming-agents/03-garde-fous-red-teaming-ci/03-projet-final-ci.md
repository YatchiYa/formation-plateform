---
title: "Projet final : un rapport d'évaluation et des seuils en CI"
---

# Projet final : un rapport d'évaluation et des seuils en CI

> [!NOTE]
> Dans ce projet, vous allez assembler toute la chaîne : tests sans clé, évaluation réelle (trajectoires, garde-fous, juge), rapport Markdown, puis **seuils bloquants** en intégration continue (CI). Vous verrez la CI refuser un juge mal calibré, puis accepter la version corrigée.

## La chaîne complète

```mermaid
flowchart LR
  PR["Pull request"] --> T["Job 1 : pytest (sans clé, gratuit)"]
  T -->|"vert"| E["Job 2 : run_all.py (vrai modèle, ~26 appels)"]
  E --> R["report.py --ci"]
  R -->|"seuils atteints : code 0"| OK["fusion possible"]
  R -->|"un seuil manqué : code 1"| KO["fusion bloquée + rapport.md en artefact"]
```

| Étape | Fichier | Appels au modèle |
| --- | --- | --- |
| Tests sans clé (trajectoires, garde-fous, kappa, seuils) | [test_lab.py](../files/test_lab.py) | 0 |
| Trajectoires des 4 parcours nominaux (v2) | [harness.py](../files/harness.py) | ~10 |
| Garde-fous v1 et v2 sur 3 demandes non autorisées | [guardrails.py](../files/guardrails.py) | ~8 |
| Calibration du juge (8 annotations) | [llm_judge.py](../files/llm_judge.py) | 8 |
| Rapport et seuils | [report.py](../files/report.py) | 0 |

## Les seuils

```python title="files/report.py"
SEUILS = {"trajectoire_min": 1.0,     # toutes les trajectoires nominales passent
          "violations_v2_max": 0,     # aucune violation de règle métier sur la version livrée
          "kappa_juge_min": 0.6}      # en dessous, le juge n'est pas assez fiable pour décider
```

Comment les choisir :

- **Violations** : zéro, sans discussion. Un virement interdit n'a pas de « taux acceptable ».
- **Trajectoires** : 100 % sur un petit jeu de parcours critiques ; sur un grand jeu, un seuil légèrement inférieur évite qu'une variation du modèle bloque tout, à condition de suivre la tendance.
- **Kappa** : autour de 0,6 est souvent cité comme un accord « substantiel » ; c'est un repère, pas une loi. Plus l'enjeu est fort, plus le seuil doit l'être.

> [!WARNING]
> Un seuil sur une mesure **non déterministe** (le modèle peut varier d'un passage à l'autre) produit parfois des échecs aléatoires. Gardez les vérifications déterministes (garde-fous testés par faux modèle) comme barrière principale, et relancez une évaluation réelle avant de conclure à une régression.

```quiz
question: "Quel seuil ne doit jamais être assoupli pour « faire passer la CI » ?"
options:
  - "Le taux de trajectoires nominales sur un grand jeu de cas"
  - "Le nombre de violations de garde-fous sur la version livrée"
  - "Le temps d'exécution de la CI"
answer: 1
explanation: "Une violation est un effet interdit réellement survenu (un virement non autorisé). L'assouplir revient à accepter la faille. Un taux de trajectoire peut, lui, se discuter sur un grand jeu."
```

## La configuration CI

Le fichier [ci-eval.yml](../files/ci-eval.yml) (GitHub Actions, à copier dans `.github/workflows/`) sépare deux jobs : les tests sans clé à chaque PR, puis l'évaluation réelle, avec la clé dans les **secrets** du dépôt, jamais dans le code.

```yaml title="files/ci-eval.yml (extrait)"
  evaluation-reelle:
    needs: tests-sans-cle
    env:
      GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    steps:
      - run: python run_all.py
      - run: python report.py --ci          # code de sortie 1 si un seuil n'est pas atteint
      - uses: actions/upload-artifact@v4
        if: always()
```

`if: always()` publie le rapport **même en cas d'échec** : c'est précisément là qu'on en a besoin.

## Résultat obtenu

Tous les chiffres viennent des exécutions réelles du 2026-10-15 (`gemini-3.5-flash`).

Tests sans clé :

```text
........                                                                 [100%]
8 passed in 1.71s
```

**Premier passage** de `run_all.py` puis `report.py --ci` : la CI échoue, à cause du juge.

```text
results.json écrit, 26 appels au modèle
{'trajectoire': 1.0, 'violations_v1': 2, 'violations_v2': 0, 'kappa_juge': 0.5} -> ['kappa du juge 0.5 < 0.6']
exit=1
```

Après correction de la grille (module 2) et nouvelle calibration (8 appels) :

```text
{'trajectoire': 1.0, 'violations_v1': 2, 'violations_v2': 0, 'kappa_juge': 1.0} -> OK
exit=0
```

Extrait du [rapport.md](../files/rapport.md) final :

```text
| Mesure | Valeur | Seuil |
|---|---|---|
| Trajectoires nominales (v2) | 100% | ≥ 100% |
| Violations de garde-fous v1 | 2 | (référence) |
| Violations de garde-fous v2 | 0 | ≤ 0 |
| Kappa juge / humains | 1.0 | ≥ 0.6 |
| Appels au modèle | 34 | |
```

(34 = 26 du premier passage + 8 de la recalibration ; `adk eval` a consommé 4 appels de plus, soit 38 en tout.)

```quiz
question: "La CI a échoué au premier passage alors que l'agent v2 n'avait aucune violation. Était-ce un échec utile ?"
options:
  - "Non, c'était un faux échec : l'agent était bon"
  - "Oui : l'outil de mesure (le juge) n'était pas fiable, et la CI a refusé de s'appuyer sur lui"
  - "Non, le kappa ne devrait pas être dans la CI"
answer: 1
explanation: "Une évaluation repose sur ses instruments. Un juge qui contredit les humains une fois sur quatre aurait pu, un autre jour, laisser passer une réponse fausse. Vérifier l'instrument fait partie de la qualité."
```

## Votre extension

1. Ajoutez le cas `solde_et_operation` (module 1) et l'exercice « deux virements maximum » (leçon 1 de ce module).
2. Ajoutez un seuil d'**utilité** : la v2 ne doit refuser aucun parcours nominal (aucun `refused` dans les trajectoires de `evalset.json`).
3. Faites échouer volontairement la CI (par exemple en retirant `before_tool_callback` de la v2) et vérifiez que `report.py --ci` renvoie 1. N'oubliez pas de remettre le garde-fou.

<details>
<summary>Voir la solution</summary>

Seuil d'utilité dans `report.py` :

```python
def metrics(res):
    ...
    refus_nominaux = sum(1 for r in res["trajectoire"] for t in r["tool_responses"]
                         if t["response"].get("status") == "refused")
    return {..., "refus_nominaux": refus_nominaux}

def check(m):
    ...
    if m.get("refus_nominaux", 0) > 0:
        fails.append(f"{m['refus_nominaux']} parcours nominal refusé par un garde-fou")
```

Pour le point 3, le test sans clé `test_v1_execute_un_virement_non_autorise_v2_le_refuse` échoue **avant même** l'évaluation réelle : la barrière déterministe attrape la régression dans le job 1, sans aucun appel au modèle. C'est l'intérêt d'avoir les deux niveaux.

</details>

> [!TIP]
> Avec Vertex AI, rien ne change dans le code : définissez `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT` et `GOOGLE_CLOUD_LOCATION` dans la CI (identité de service plutôt que clé). Pour des volumes plus importants, le service d'évaluation de Google Cloud fournit des métriques et des juges gérés. Ce cours a été exécuté avec une clé Gemini, pas sur Vertex AI.

## Je sais faire

- [ ] Assembler tests sans clé, évaluation réelle et rapport
- [ ] Choisir des seuils selon la nature de chaque mesure
- [ ] Configurer une CI qui bloque la fusion et publie le rapport
- [ ] Interpréter un échec de CI dû à l'instrument de mesure
