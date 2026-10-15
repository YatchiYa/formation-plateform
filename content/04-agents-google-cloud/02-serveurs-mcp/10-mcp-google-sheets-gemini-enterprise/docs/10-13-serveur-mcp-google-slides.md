# 10-13. Le serveur MCP Google Slides

**Ce guide répond à :** que sait faire le serveur MCP **Google Slides**, comment le tester, le déployer, le brancher
sur l'assistant principal de Gemini Enterprise et sur l'agent ? Qu'est-ce qui change par rapport à Sheets ?

**En une phrase :** même sécurité, même image, même client OAuth que Sheets. Un **second service** Cloud Run
(`slides-mcp`), un **second connecteur** dans l'app, et **20 outils** pour lire et construire des présentations
avec le compte de l'utilisateur.

> **Testé en vrai (14 octobre 2026)**, projets de test, vraie présentation, vraie API Slides :
> - **les 20 outils**, en local puis sur Cloud Run, appelés comme le connecteur (deux en-têtes) ;
> - le déploiement **par Terraform**, en mise à jour d'un déploiement Sheets existant, sans rien détruire ;
> - **l'agent avec le vrai Gemini** : « lis le classeur, puis ajoute une diapositive État des stocks avec un tableau
>   et une note de l'orateur ». Fait, et vérifié dans la présentation.
>
> **Corrigés pendant ces tests :**
> - le `Dockerfile` ne copiait que `main.py` : il copie maintenant tous les fichiers Python ;
> - dans l'agent, les deux serveurs avaient des outils de même nom (`whoami`, `batch_update`) : les outils Slides
>   sont maintenant préfixés `slides_`.

---

> **Déployer et tester Slides SEUL, ou l'ajouter après Sheets :** [10-14](10-14-un-serveur-a-la-fois.md).

## Sommaire

1. [Les 20 outils](#1-les-20-outils)
2. [Comment c'est construit](#2-comment-cest-construit)
3. [Tester en local](#3-tester-en-local)
4. [Déployer](#4-déployer)
5. [Le brancher sur l'assistant principal (connecteur)](#5-le-brancher-sur-lassistant-principal-connecteur)
6. [L'agent : Sheets et Slides ensemble](#6-lagent--sheets-et-slides-ensemble)
7. [Agent Registry](#7-agent-registry)
8. [Ce qu'on demande dans le chat](#8-ce-quon-demande-dans-le-chat)
9. [Bon à savoir, et si ça bloque](#9-bon-à-savoir-et-si-ça-bloque)
10. [Le serveur Slides officiel de Google](#10-le-serveur-slides-officiel-de-google)

---

## 1. Les 20 outils

| Outil | Rôle | Type |
|---|---|---|
| `whoami` | Le compte Google connecté | Lecture |
| `search_presentations` | Trouver des présentations par nom (Mon Drive et Drive partagés) | Lecture |
| `get_presentation_info` | Titre, lien, format (pt), diapositives : numéro, objectId, mise en page, titre, notes ou non | Lecture |
| `read_slide` | Une diapositive en détail : chaque élément (zone du modèle, texte, tableau, image, position et taille en pt) et les notes | Lecture |
| `read_presentation_text` | Tout le texte et toutes les notes, diapositive par diapositive : pour résumer, relire, traduire | Lecture |
| `get_slide_thumbnail` | Une image PNG de la diapositive (adresse temporaire) | Lecture |
| `list_layouts` | Les mises en page du **thème** de la présentation, avec leurs zones (titre, corps…) | Lecture |
| `create_presentation` | Créer une présentation | Écriture |
| `add_slide` | Ajouter une diapositive **en remplissant les zones du modèle** (titre, corps) et les notes. Mise en page prédéfinie ou celle du modèle d'entreprise | Écriture |
| `duplicate_slide` / `move_slide` | Dupliquer, déplacer | Écriture |
| `insert_text_box` | Zone de texte libre, position et taille en points | Écriture |
| `insert_image` | Image depuis une adresse https publique | Écriture |
| `create_table` | Tableau rempli (la 1re ligne en en-tête) | Écriture |
| `format_text` | Gras, italique, souligné, taille, couleur, police, alignement d'une zone | Écriture |
| `set_background` | Couleur de fond d'une diapositive | Écriture |
| `delete_slide` | Supprimer une diapositive | **Destructif** |
| `replace_text` | Remplacer un texte partout (ou sur certaines diapositives) : modèles à compléter | **Destructif** |
| `set_speaker_notes` | Écrire les notes de l'orateur (remplace l'existant) | **Destructif** |
| `batch_update` | **Toute l'API Slides** : formes, lignes, graphiques Sheets, vidéos, listes à puces, groupes, superposition… | **Destructif** |

**Ce qui le rend bon pour un modèle :**
- les diapositives se désignent par leur **numéro** (1, 2, 3…) ou leur objectId ;
- les positions sont en **points** (une diapositive 16:9 fait 720 × 405 pt) ;
- `add_slide` **remplit les zones du modèle**, donc le rendu suit le thème de Acme au lieu de zones posées au
  hasard ;
- `list_layouts` donne les mises en page du **modèle d'entreprise** ;
- tout ce qui n'a pas d'outil dédié passe par `batch_update`.

## 2. Comment c'est construit

```
mcp_server/
├── noyau.py          COMMUN : vérification du jeton (audience, portée, domaine), appels Google avec le jeton
│                     de l'utilisateur, audit, recherche Drive, outil whoami
├── outils_sheets.py  les 16 outils Sheets (+ whoami = 17)
├── outils_slides.py  les 19 outils Slides (+ whoami = 20)
└── main.py           PRODUIT=sheets (défaut) ou PRODUIT=slides : choisit les outils
```
- **Une seule image**, déployée deux fois : `sheets-mcp` (`PRODUIT=sheets`) et `slides-mcp` (`PRODUIT=slides`).
- **Même sécurité** pour les deux : Cloud Run privé, compte de service **sans rôle**, jeton de l'utilisateur vérifié
  puis utilisé, journal d'audit sans contenu.
- **Portée exigée** par le serveur Slides : `https://www.googleapis.com/auth/presentations`. Pour la recherche par
  nom : `drive.metadata.readonly`, qui donne les noms des fichiers seulement.

## 3. Tester en local

Il faut une présentation que le compte du jeton peut **modifier**, et un jeton avec la portée `presentations`
([10-8, partie 2](10-8-tester-simuler-verifier.md#2-obtenir-un-jeton-de-test) : ajoutez
`https://www.googleapis.com/auth/presentations` aux portées).
```bash
cd mcp_server && PRODUIT=slides OAUTH_CLIENT_IDS=<aud du jeton> ALLOWED_DOMAINS=<domaine> PORT=8095 python main.py &
cd .. && MCP_URL=http://localhost:8095/mcp PRESENTATION_ID=<ID> python tests/test_reel_slides.py
```
Le test ajoute des diapositives de test, utilise les 20 outils, puis **supprime** ses diapositives : la présentation
est rendue intacte.

**Résultat obtenu :**
```
tools/list : 20 outils
whoami                 : sheets-utilisateur-test@…
search_presentations   : 1 présentation(s), dont celle de test
get_presentation_info  : « MCP Slides - test Acme (projet 10) », 1 diapositive(s), format [720.0, 405.0] pt
list_layouts           : 11 mises en page, ex. ['Diapositive de titre', 'En-tête de section', 'Titre et corps', …]
add_slide              : mcp_ae702d531f944d6d (3 zones remplies : titre, corps, notes)
duplicate_slide        : SLIDES_API154424528_0
move_slide             : copie placée en position 1
insert_text_box/format : mcp_bac3b67410824f9c ; mise en forme ['bold', 'foregroundColor', 'alignment']
insert_image           : mcp_21c21205fb654cdc
create_table           : 3 x 2
set_background         : fond #F5F6FB
replace_text           : 3 remplacement(s)
set_speaker_notes      : notes remplacées = True
batch_update (ligne)   : 1 réponse
read_slide             : [('zone', 'TITLE', "Bilan magasin Villeneuve-d'Asc"), ('zone', 'BODY', "Chiffre d'affaires : 120 k€…"), ('text_box', None, 'Objectif 2027 : +15 %'), ('image', …), ('line', …)]
                         notes : 'Notes mises à jour par le MCP.'
read_presentation_text : 3 diapositives ; diapo 1 : "Bilan magasin Villeneuve-d'Ascq\nChiffre d'affaires : 120 k€\nVisiteurs : 18 400…"
get_slide_thumbnail    : 200 x 113 px, https://lh7-us.googleusercontent.com/…
delete_slide           : 2 diapositive(s) de test supprimée(s)
présentation rendue intacte : 1 diapositive(s)
create_presentation    : refusé pour ce compte (accès refusé…)   ← compte de service sans Drive ; un vrai utilisateur, si
OK : test réel Slides terminé
```

## 4. Déployer

| Méthode | Commande | Ce qui se passe |
|---|---|---|
| Script | `./scripts/deployer.sh mcp` | Construit **une** image, déploie `sheets-mcp` **et** `slides-mcp`. `./scripts/deployer.sh mcp slides` : seulement Slides |
| Terraform | `terraform apply` (variable `produits_mcp`, par défaut `["sheets", "slides"]`) | Un service, des droits et une entrée Agent Registry par produit |
| Console | [10-4, étape 4](10-4-deployer-console.md#étape-4--le-serveur-mcp), une 2e fois, avec le nom `slides-mcp` et la variable **`PRODUIT` = `slides`** | Même image que Sheets |

`preparer` active aussi l'API Google Slides (`slides.googleapis.com`). Terraform aussi.

**Résultat obtenu** (Terraform, mise à jour d'un déploiement Sheets existant) :
```
  # google_agent_registry_service.mcp[0] has moved to google_agent_registry_service.mcp["sheets"]
  # google_agent_registry_service.mcp["slides"] will be created
  # google_cloud_run_v2_service.mcp["sheets"] will be updated in-place
  # google_cloud_run_v2_service.mcp["slides"] will be created
  # google_cloud_run_v2_service_iam_member.mcp["slides serviceAccount:service-<NUM_APP>@…"] will be created
  # google_cloud_run_v2_service_iam_member.mcp["slides serviceAccount:sheets-agent-sa@…"] will be created
  # google_project_service.apis["slides.googleapis.com"] will be created
  …
Apply complete!
mcp_urls = {
  "sheets" = "https://sheets-mcp-<NUM>.europe-west1.run.app/mcp"
  "slides" = "https://slides-mcp-<NUM>.europe-west1.run.app/mcp"
}
```
Les droits de Sheets **ne bougent pas**, parce que Terraform garde leurs clés. L'adresse Slides chez Acme sera
`https://slides-mcp-433175138344.europe-west1.run.app/mcp`.

## 5. Le brancher sur l'assistant principal (connecteur)

**Ce sont les mêmes étapes que pour Sheets** ([10-12](10-12-pas-a-pas-mcp-dans-assistant-principal.md)). Seules
ces lignes changent :

| Étape de 10-12 | Pour Slides |
|---|---|
| 4. Client OAuth | **Le même client.** Dans **Data access**, ajoutez la portée `https://www.googleapis.com/auth/presentations` |
| 7. Déployer | `./scripts/deployer.sh mcp` (les deux), ou `./scripts/deployer.sh mcp slides` |
| 8. Droit d'appel | **Cloud Run** → **`slides-mcp`** → **Security** → **Add principal** → `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` → **Cloud Run Invoker**. Ou `./scripts/deployer.sh droits-app` : il traite les deux |
| 9. Règles d'organisation | Ajoutez le domaine de sortie `slides-mcp-433175138344.europe-west1.run.app` |
| 11. Formulaire | Un **2e** « Custom MCP Server » (voir ci-dessous) |
| 12. Actions | Les 20 actions : d'abord les **7 de lecture** (`whoami`, `search_presentations`, `get_presentation_info`, `read_slide`, `read_presentation_text`, `get_slide_thumbnail`, `list_layouts`) |
| 13. Brancher sur l'app | Ajoutez aussi le data store **Google Slides** |

**Le formulaire « Custom MCP Server » pour Slides :**

| Champ | Valeur |
|---|---|
| Authentication method | **OAuth 2.0** |
| MCP Server URL | `https://slides-mcp-433175138344.europe-west1.run.app/mcp` |
| Authorization URL | `https://accounts.google.com/o/oauth2/v2/auth` |
| Authorization URL Parameters | `&access_type=offline&prompt=consent&hd=acme.example` |
| Token URL | `https://oauth2.googleapis.com/token` |
| Client ID / Client Secret | **les mêmes** que pour Sheets |
| Scopes | `openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/presentations https://www.googleapis.com/auth/drive.metadata.readonly` |
| Enable PKCE Support | **cochez-le** |
| Use HTTP Basic Authentication | laissez-le coché |
| Nom du data connector | `Google Slides` |

`./scripts/deployer.sh fiche` affiche ce formulaire, rempli (« Modalité 1 bis »), dès que `slides-mcp` est déployé.

## 6. L'agent : Sheets et Slides ensemble

Quand `slides-mcp` existe, `./scripts/deployer.sh agent` (et `agent-runtime`, et Terraform) donne à l'agent :
- la variable `MCP_SLIDES_URL` : l'agent reçoit **aussi** les 20 outils Slides ;
- le droit **Cloud Run Invoker** sur `slides-mcp`.

Dans l'agent, les outils Slides sont **préfixés** `slides_` : `slides_add_slide`, `slides_batch_update`… Sans
préfixe, `whoami` et `batch_update` existeraient en double, et l'un masquerait l'autre. **Vu en test** : 35 outils au
lieu de 37. C'est corrigé ; le test vérifie maintenant 37 outils distincts.

**L'autorisation de l'agent** doit contenir la portée `presentations`.
- `./scripts/deployer.sh autorisation …` l'ajoute toute seule quand `slides-mcp` existe, et `fiche` l'affiche.
- Si l'autorisation a été créée **avant** Slides, recréez-la : supprimez-la, recréez-la, puis rattachez l'agent. Sinon
  l'agent ne pourra pas toucher aux présentations (Google répond « portée manquante »).

**Résultat obtenu** (agent A2A sur Cloud Run, vrai Gemini, appelé comme Gemini Enterprise) :
```
> Lis le classeur 1H-w96… puis ajoute à la fin de la présentation 1zy2Z… une diapositive « État des stocks » avec un
  tableau Produit / Prix / Stock, et en notes de l'orateur le produit le plus en stock.
< J'ai lu le classeur et j'ai effectué les modifications demandées dans la présentation.
  1. Lecture des stocks : Vélo 12 (299), Tente 30 (149), Sac à dos 80 (39). Le produit le plus en stock est le Sac à dos.
  2. Mise à jour de la présentation : ajout d'une diapositive « État des stocks » à la fin ; tableau Produit / Prix /
     Stock ; note de l'orateur : « Le produit le plus en stock est : Sac à dos (80 unités). » [liens]
```
Relu dans la présentation : la note de l'orateur est bien là. Ajouter une diapositive à la fin ne détruit rien, donc
l'agent n'a pas demandé confirmation. Il la demande avant de remplacer ou de supprimer, comme pour Sheets
([10-8](10-8-tester-simuler-verifier.md#4-sur-cloud-run--comme-gemini-enterprise)).

## 7. Agent Registry

`./scripts/deployer.sh registre` (ou Terraform) déclare **les deux** serveurs : « Google Sheets (MCP) » et « Google
Slides (MCP) ».

`scripts/gen_toolspec.py` génère :
- `terraform/toolspec-sheets.json` : 17 outils, 6 917 octets ;
- `terraform/toolspec-slides.json` : 20 outils, 9 007 octets.

La limite est de 10 Ko. Le script s'arrête de lui-même si elle est dépassée.

## 8. Ce qu'on demande dans le chat

| Demande (assistant principal, connecteur Google Slides) | Attendu |
|---|---|
| « Liste mes présentations sur le bilan » | Les présentations, avec leurs liens |
| « Résume la présentation `<lien>` et ses notes » | Le résumé, diapositive par diapositive |
| « Ajoute une diapositive Titre et corps : titre Bilan Lille, trois points… » | Confirmation (selon les actions activées), puis la diapositive au thème |
| « Remplace 2025 par 2026 dans toute la présentation » | **Confirmation** (destructif), puis le nombre de remplacements |
| « Écris les notes de l'orateur de la diapositive 3 » | **Confirmation** (remplace), puis c'est fait |
| Avec l'agent : « Fais une diapositive à partir du classeur Ventes » | Lecture du classeur, puis la diapositive avec un tableau |

## 9. Bon à savoir, et si ça bloque

| Point | Explication |
|---|---|
| `insert_image` : erreur | L'image doit avoir une adresse **https publique** (PNG, JPEG ou GIF, moins de 50 Mo). Google la télécharge lui-même : une image du Drive privé ne marche pas |
| `add_slide` : « pas de zone pour : corps » | La mise en page choisie n'a pas de zone de corps (par exemple `TITLE_ONLY`). Prendre `TITLE_AND_BODY`, ou une mise en page du modèle (`list_layouts`) |
| Le modèle Acme | `list_layouts` liste ses mises en page ; passez leur **objectId** à `add_slide` (`layout=`) |
| `get_slide_thumbnail` | L'adresse renvoyée ne vaut qu'environ 30 minutes |
| `create_presentation` refusé | Le compte n'a pas d'espace Drive (compte de service). Un utilisateur réel n'a pas ce problème |
| Toutes les actions : « portée manquante » | La portée `presentations` n'est pas dans le connecteur (ou dans l'autorisation de l'agent) : l'ajouter, puis se reconnecter |
| Conteneur `slides-mcp` qui ne démarre pas | Journaux Cloud Run. Vu une fois : `No module named 'outils_slides'`, quand le `Dockerfile` ne copiait que `main.py`. C'est corrigé (`COPY *.py ./`) |

## 10. Le serveur Slides officiel de Google

Google a aussi un serveur MCP Slides officiel (`slidesmcp.googleapis.com`, Developer Preview). **Testé le 14 octobre
2026** : l'API s'active, et `tools/list` répond, avec **4 outils** :
- `read_presentation` ;
- `read_slide_page` ;
- `read_slide_page_thumbnail` ;
- `update_presentation` (batchUpdate brut).

Pour l'utiliser, il faut l'inscription à la preview, comme pour Sheets ([10-10](10-10-serveur-mcp-sheets-officiel-google.md)).

| | Officiel | Le nôtre |
|---|---|---|
| Outils | 4, bruts (le modèle doit écrire du JSON batchUpdate) | 20, prêts à l'emploi + `batch_update` pour le reste |
| Remplir le modèle d'entreprise | À écrire soi-même | `add_slide` + `list_layouts` |
| Recherche par nom, notes, tableaux, images, texte complet | Non | Oui |
| Contrôle du domaine dans le serveur, journal d'audit | Non (côté Workspace) | Oui |
| Disponibilité | Preview, sur inscription | Tout de suite |
