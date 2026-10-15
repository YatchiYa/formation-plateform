# Les scripts du projet 09 : lequel sert à quoi

Chaque script commence par un **en-tête détaillé** : ce qu'il fait, quand l'utiliser, ses prérequis, toutes ses options
avec un exemple, ce qu'il crée ou supprime, le résultat attendu, les erreurs fréquentes. Cette page en donne la carte.
Sans argument (ou avec `--help` pour les scripts Python à options), la plupart affichent leur mode d'emploi.

## Avant tout : deux règles

1. **Lancer depuis le dossier du projet**, Python du projet activé :
   ```bash
   cd ~/Desktop/09-agents-multi-projets-gemini-enterprise && source .venv/bin/activate
   ```
2. **Charger la configuration** (pour tous les scripts qui touchent Google Cloud). Dans chaque nouveau terminal, et
   toujours avec `source`, jamais derrière un `|` :
   ```bash
   source scripts/config.sh config/12-1-agents-dans-projet-exp.env      # ou config/12-2-agents-dans-projet-app.env
   ```
   Les scripts lisent alors `$PROJET_AGENTS`, `$REGION`, `$AGENTS_LISTE`, `$GE_SA`…, sans rien retaper.

**Légende du tableau :**
- 👁 = lecture seule, ne change rien ;
- ♻ = se relance sans danger (ce qui existe est gardé) ;
- ⚠ = crée ou supprime des ressources dans Google Cloud.

## La carte des scripts

### Configuration et vérifications

| Script | Il sert à | Exemple | |
|---|---|---|---|
| `config.sh` | Charger le fichier de configuration dans le terminal : variables pour gcloud, les scripts et Terraform (`TF_VAR_…`, espace de travail), vérification des valeurs, résumé | `source scripts/config.sh config/12-1-agents-dans-projet-exp.env` | 👁 |
| `verifier_droits.sh` | Vérifier **vos** droits sur le projet des agents, étape par étape (OK / MANQUANT + rôle à demander), rôles de groupe compris | `./scripts/verifier_droits.sh` | 👁 |
| `verifier_api.sh` | Vérifier des API sur un projet et activer **seulement** celles qui manquent | `./scripts/verifier_api.sh $PROJET_AGENTS run.googleapis.com cloudbuild.googleapis.com` | ♻ |

### Déployer les agents (sans Terraform)

| Script | Il sert à | Exemple | |
|---|---|---|---|
| `deployer_shell.sh` | **Méthode shell sans rien taper** : préparer (filtres, dépôt, compte de construction), déployer sur Cloud Run (image par Cloud Build), sur Agent Runtime, déclarer au registre, tester ; `oauth` (API Google des agents OAuth) ; `carte` (la fiche à coller dans Gemini Enterprise). Agents lus dans `AGENTS` | `./scripts/deployer_shell.sh cloudrun` · `… runtime taille` | ⚠ ♻ |
| `deployer_agent_runtime.py` | Déployer **un** agent sur Agent Runtime par l'API (ou en supprimer un) | `python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --agent meteo_agent --nom meteo-shell --compte-service …` | ⚠ ♻ (refuse un doublon) |
| `carte_a2a.py` | Écrire la **carte A2A** d'un agent (à coller dans Gemini Enterprise), ou les variables d'environnement de son service Cloud Run | `python3 scripts/carte_a2a.py meteo https://meteo-a2a-shell-NUM.europe-west1.run.app > carte-meteo.json` | 👁 |

### Tester

| Script | Il sert à | Exemple | |
|---|---|---|---|
| `test_trio.py` | Tests **hors ligne** des agents de `agents/trio` (outils, Model Armor, catalogue) | `python scripts/test_trio.py` → `tests trio OK (9 scénarios, 6 agents)` | 👁 |
| `test_agents.py` | Tests hors ligne des agents du dossier `terraform/` racine (stock, orchestrateur, appel entre agents) | `python scripts/test_agents.py` | 👁 |
| `query.py` | Poser une question à un agent **Agent Runtime** déployé (voir les outils appelés) | `AGENT_NAME=projects/…/reasoningEngines/ID python scripts/query.py - "question"` | 👁 |
| `simuler_gemini_enterprise.sh` | Appeler les agents **comme le fera Gemini Enterprise**, avant de toucher à l'app : `preparer`, `droits`, `tout` (bilan ACCEPTÉ / REFUSÉ), `oauth` (avec / `--sans-jeton`), `retirer-droits` ; ou un agent : `a2a URL`, `runtime NOM` (docs/12-1-5) | `./scripts/simuler_gemini_enterprise.sh tout` | ⚠ (simulateur et ses droits seulement) |

Les tests des agents **déployés sur Cloud Run** sont dans `01-bis-cloud-run-a2a/test.sh` ; ceux d'Agent Runtime
(Terraform) dans `02-bis-agent-runtime/test.sh` ; Dialogflow : `04-bis-dialogflow/test.sh`.

### Agent Registry

| Script | Il sert à | Exemple | |
|---|---|---|---|
| `registry.py` | Explorer le registre d'un projet (le vôtre ou celui d'une autre équipe) : agents, serveurs MCP, et comment les ajouter | `python scripts/registry.py $PROJET_AGENTS europe-west1` | 👁 |
| `autoriser_passerelle.sh` | Mode « Agents depuis Agent Registry » : donner (ou retirer) au compte de l'app le droit de passer la passerelle vers une entrée du registre | `./scripts/autoriser_passerelle.sh meteo-a2a-shell` · `… retirer` | ⚠ ♻ |

### Gemini Enterprise (l'app)

| Script | Il sert à | Exemple | |
|---|---|---|---|
| `connecter_app.sh` | **Connecter** les agents déployés à l'app : `apps` (trouver APP_ID), `verifier` (lecture seule), `droits` (projet des agents), `ajouter` (dans l'app), `lister`, `retirer` ; liste + confirmation avant tout changement (docs/12-1-4) | `./scripts/connecter_app.sh verifier` · `… droits` · `… ajouter meteo` | 👁 / ⚠ ♻ |
| `add_agent_to_ge.sh` | Ajouter à l'app un agent déjà déployé (Agent Runtime ou A2A), avec le droit nécessaire ; lister ; retirer | `./scripts/add_agent_to_ge.sh a2a carte-meteo.json "Météo (A2A)"` · `… list` · `… delete "Météo (A2A)"` | ⚠ ♻ (pas de doublon) |
| `register_agent.sh` | Appelé **par Terraform** (`PUBLIER=oui`) pour ajouter / retirer un agent de l'app ; remplace sans doublon | (automatique) | ⚠ ♻ |
| `autorisation_oauth.sh` | Créer / renommer / lister / supprimer une **autorisation OAuth** dans l'app (agents qui agissent avec le compte de l'utilisateur) ; nom affiché dans l'encadré « Autoriser » | `./scripts/autorisation_oauth.sh create acces-gmail client_secret.json "…/gmail.readonly" "Gmail (lecture seule)"` · `… renommer acces-gmail "Gmail"` | ⚠ |
| `personnaliser_agent.sh` | Soigner un agent déjà dans l'app : nom, questions proposées, texte de saisie, langue, icône (valeurs du catalogue) ; avant/après, confirmation, retour arrière | `GE_PROJECT=… GE_APP=… ./scripts/personnaliser_agent.sh "Nom actuel" courriels` · `… --annuler avant-<ID>.json` | ⚠ (modifie seulement l'agent dans l'app, retour arrière possible) |
| `fiche_ge.py` | La fiche d'un agent pour la console Gemini Enterprise (appelé par `deployer_shell.sh carte`) | `./scripts/deployer_shell.sh carte courriels` | 👁 |

### Créer, nettoyer

| Script | Il sert à | Exemple | |
|---|---|---|---|
| `nouvel_agent.py` | Créer le **squelette** d'un nouvel agent (dossier, `agent.py`, entrée du catalogue) | `python scripts/nouvel_agent.py velo "Atelier vélo" "…"` | ⚠ (fichiers locaux) |
| `nettoyer.py` | **Inventaire** de ce que les guides ont créé dans le projet, puis suppression **après confirmation** | `python scripts/nettoyer.py` (inventaire) · `--agent meteo` · `--supprimer` | 👁 / ⚠ |

### Utilisés par Terraform (rien à lancer)

| Script | Il sert à |
|---|---|
| `pack.py` | Empaqueter le code d'**un** agent (son dossier + le code commun) pour Agent Runtime, toujours avec les mêmes octets : même code = rien à redéployer |
| `register_agent.sh` | Voir plus haut |

### Générer les documents (PDF, PowerPoint)

| Script | Il produit |
|---|---|
| `build_pdf_tuto.py` | `Gemini-Enterprise-Agents-Tutoriel-Pas-a-Pas.pdf` (tutoriel pas à pas) |
| `build_pdf.py` | `Gemini-Enterprise-Agents-Guide-Equipes.pdf` (guide pour les équipes, PM, RH) |
| `pdf_style.py` | Le style commun des deux PDF (polices, couleurs, tableaux) : n'est pas lancé seul |
| `build_pptx.js` | `Gemini-Enterprise-Agents-Guide-Equipes.pptx` (présentation) |

Commandes (depuis le dossier du projet) :

```bash
python3 scripts/build_pdf_tuto.py            # le python3 du SYSTÈME (reportlab), pas celui du .venv
python3 scripts/build_pdf.py
npm install --prefix ~/pptx-deps pptxgenjs react react-dom sharp react-icons     # une fois
NODE_PATH=~/pptx-deps/node_modules node scripts/build_pptx.js Gemini-Enterprise-Agents-Guide-Equipes.pptx
```

Les polices nécessaires, les chemins propres à ce poste et les erreurs fréquentes sont dans l'en-tête de chacun.

## Quel script à quelle étape (méthode shell, docs/12-1-1)

```
 1. source scripts/config.sh config/…env                  configuration
 2. ./scripts/verifier_api.sh $PROJET_AGENTS …            API
 3. ./scripts/deployer_shell.sh preparer                  filtres, dépôt, compte de construction
 4. ./scripts/deployer_shell.sh cloudrun | runtime        déployer
 5. ./scripts/deployer_shell.sh registre                  catalogue
 6. ./scripts/deployer_shell.sh tester                    tester
 7. ./scripts/deployer_shell.sh carte [clé]               la fiche pour Gemini Enterprise (carte-<clé>.json, chemin…)
    (agents OAuth, docs/12-1-8 : « oauth » avant, CLIENT_ID=… devant « carte », personnaliser_agent.sh après l'ajout)
 8. ./scripts/simuler_gemini_enterprise.sh tout          simuler l'appel de l'app (docs/12-1-5)
 9. ./scripts/connecter_app.sh verifier | droits | ajouter  connecter à l'app (docs/12-1-4)
10. python scripts/nettoyer.py [--supprimer]              inventaire / nettoyage
```

Avec Terraform (docs/12-1-2), seuls `config.sh` et `verifier_api.sh` se lancent à la main. Terraform appelle `pack.py`
et `register_agent.sh` tout seul.
