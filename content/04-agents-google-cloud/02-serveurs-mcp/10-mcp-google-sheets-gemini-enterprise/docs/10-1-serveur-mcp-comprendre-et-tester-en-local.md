# 10-1. Le serveur MCP Google Sheets : comprendre, lancer, tester sur votre poste

**Ce guide répond à :** que fait `mcp_server/main.py`, ligne par ligne ? Comment l'installer et le lancer sur un
Mac ou un PC Linux ? Comment le tester d'abord sans compte Google, puis sur un vrai classeur ?

> **Testé (13 octobre 2026), Python 3.14 :** les tests simulés passent, et les 17 outils passent sur un vrai
> classeur, avec la vraie API Sheets, en local. Résultats réels à la partie 5.

---

## Sommaire

1. [Ce que fait le serveur](#1-ce-que-fait-le-serveur)
2. [Les 17 outils](#2-les-17-outils)
3. [Les contrôles de sécurité dans le code](#3-les-contrôles-de-sécurité-dans-le-code)
4. [Installer sur votre poste](#4-installer-sur-votre-poste)
5. [Tester](#5-tester)
6. [Le piège des formules : la locale du classeur](#6-le-piège-des-formules--la-locale-du-classeur)
7. [Modifier ou ajouter un outil](#7-modifier-ou-ajouter-un-outil)

---

## 1. Ce que fait le serveur

`mcp_server/main.py` est un serveur **FastMCP** (bibliothèque Python de référence pour MCP), exposé en HTTP sur
`/mcp`. Il fait 3 choses :

1. **Vérifier le jeton de l'utilisateur** (`CompanyGoogleTokenVerifier`). Google lui confirme :
   - le client OAuth qui a émis le jeton (`aud`) ;
   - les portées accordées ;
   - l'e-mail du compte.

   Le serveur refuse si l'un de ces points n'est pas celui attendu (partie 3). Le résultat est gardé 5 minutes, pour
   ne pas interroger Google à chaque requête.
2. **Exposer 17 outils.** Chacun a :
   - une description et des paramètres typés, que le modèle lit ;
   - des **annotations** (lecture, écriture, destructif), dont Gemini Enterprise se sert pour demander confirmation.
3. **Appeler Google Sheets ou Drive avec le jeton de l'utilisateur** (fonction `google()`). Les erreurs de Google
   sont traduites en messages clairs : 401 « reconnectez », 403 « pas les droits », 404 « introuvable »,
   429 « réessayez dans une minute ».

Chaque outil écrit une ligne de **journal d'audit** : qui, quel outil, quel classeur, quelle plage. Le contenu des
cellules n'est **jamais** écrit.

Le serveur est **sans état** (`stateless_http=True`) : Cloud Run peut lancer plusieurs copies sans rien partager.

## 2. Les 17 outils

| Outil | Rôle | Type |
|---|---|---|
| `whoami` | Le compte Google connecté (test de connexion) | Lecture |
| `search_spreadsheets` | Trouver des classeurs par nom (Mon Drive et Drive partagés) | Lecture |
| `get_spreadsheet_info` | Titre, lien, **locale**, onglets (taille, lignes figées) | Lecture |
| `read_range` | Lire une plage : valeurs affichées, brutes, ou formules | Lecture |
| `read_ranges` | Lire jusqu'à 20 plages en un appel | Lecture |
| `find_in_sheet` | Les cellules qui contiennent un texte | Lecture |
| `write_range` | Écrire en **remplaçant** une plage (formules acceptées) | **Destructif** |
| `append_rows` | Ajouter des lignes à la fin d'un tableau | Écriture |
| `clear_range` | Effacer les valeurs d'une plage | **Destructif** |
| `create_spreadsheet` | Créer un classeur, avec ses onglets | Écriture |
| `add_sheet` / `rename_sheet` | Ajouter / renommer un onglet | Écriture |
| `delete_sheet` | Supprimer un onglet et son contenu | **Destructif** |
| `insert_dimension` | Insérer des lignes ou des colonnes | Écriture |
| `delete_dimension` | Supprimer des lignes ou des colonnes | **Destructif** |
| `format_range` | Gras, italique, couleurs, format de nombre, alignement | Écriture |
| `batch_update` | **Toute l'API Sheets** : tri, filtres, fusion, mise en forme conditionnelle, graphiques, validation, protection… | **Destructif** |

Les plages s'écrivent en notation A1 : `Ventes!A1:D20`, `'Mon onglet'!A:A`, `B2`.

> **Pas d'outil qui supprime un fichier.** Le serveur demande la portée `drive.metadata.readonly`, qui permet de
> chercher un classeur par son nom mais pas d'en lire le contenu ni de le supprimer. Supprimer ou vider des onglets
> et des plages reste possible (outils destructifs). Dans Gemini Enterprise, ils demandent une confirmation, et vous
> choisissez de les activer ou non (10-5).

## 3. Les contrôles de sécurité dans le code

| Contrôle | Où | Effet |
|---|---|---|
| Démarrage **refusé** sans `OAUTH_CLIENT_IDS` | début de `main.py` | Une erreur de configuration ne peut pas donner un serveur qui accepte n'importe quel jeton |
| **Audience** du jeton = un de nos clients OAuth | `GoogleTokenVerifier(audience=…)` | Un jeton émis pour une autre application est refusé (attaque du « confused deputy ») |
| Portée **`spreadsheets`** obligatoire | `required_scopes` | Un jeton sans accès Sheets est refusé |
| E-mail **vérifié** et du **domaine autorisé** | `CompanyGoogleTokenVerifier` | Les comptes Gmail personnels et les autres organisations sont refusés |
| Appels Google **avec le jeton de l'utilisateur** | `google()` | Le serveur n'a aucun droit propre : les droits Drive de chacun s'appliquent |
| **20 000 cellules** maximum par lecture | `MAX_CELLS_PER_READ` | Ne pas envoyer un classeur entier au modèle (`truncated: true`) |
| Journal d'audit **sans contenu** | `audit()` | Traçabilité sans fuite de données |

## 4. Installer sur votre poste

Dans le dossier `10-mcp-google-sheets-gemini-enterprise` :

```bash
python3 -m venv .venv && source .venv/bin/activate      # Python 3.12, 3.13 ou 3.14
pip install -r mcp_server/requirements.txt              # fastmcp, uvicorn, httpx : pas de watchdog
```

**Attendu :** `Successfully installed fastmcp-4.1.0 …`.

**Tester aussi l'agent en local** (facultatif) : il faut en plus `google-adk`. Sur le Mac Acme, `google-adk`
tire `watchdog`, qui ne s'installe pas (voir 12-1-1, partie 2 du projet 09). Prenez l'environnement du projet 09,
qui marche déjà, et ajoutez-y `fastmcp` :
```bash
source ../09-agents-multi-projets-gemini-enterprise/.venv/bin/activate
pip install fastmcp==4.1.0
```
Sur un PC Linux, il suffit de faire `pip install -r agent/requirements.txt` dans le même `.venv`.

**Le déploiement ne demande rien de plus** : les images sont construites par Cloud Build dans Google Cloud (10-2).

## 5. Tester

### 5.1 Sans compte Google (2 secondes)

```bash
python tests/test_server.py
```
Ce test lance le serveur en HTTP, comme sur Cloud Run. Un client MCP l'appelle, et Google est remplacé par un faux
Google en mémoire.

**Résultat obtenu :**
```
  ok  notation A1
  ok  rejeté : jeton invalide
  ok  rejeté : jeton émis pour une autre application (audience)
  ok  rejeté : compte hors domaine acme.example
  ok  rejeté : scope Sheets absent
  ok  accepté : alice@acme.example
Outils (17) : add_sheet, append_rows, batch_update, clear_range, create_spreadsheet, …
  ok  search, info, read_range, read_ranges, find_in_sheet
  ok  write, append, clear, create, add/rename/delete sheet, insert/delete rows-cols, format, batch_update
  ok  erreur Google traduite en message clair (404)

OK : tous les tests passent (23 appels Google simulés, tous avec le jeton de l'utilisateur).
```

### 5.2 Sur un vrai classeur, en local

Il faut :
- un **jeton utilisateur** qui a la portée Sheets. Comment l'obtenir : [10-8, partie 2](10-8-tester-simuler-verifier.md#2-obtenir-un-jeton-de-test) ;
- un classeur que ce compte peut **modifier**.

Le serveur doit accepter le client OAuth qui a émis ce jeton. Donnez-le-lui **en local seulement** :
```bash
export USER_TOKEN=<le jeton>
AUD=$(curl -s "https://oauth2.googleapis.com/tokeninfo?access_token=$USER_TOKEN" | python3 -c 'import json,sys; print(json.load(sys.stdin)["aud"])')
OAUTH_CLIENT_IDS=$AUD ALLOWED_DOMAINS=acme.example PORT=8091 python mcp_server/main.py &
MCP_URL=http://localhost:8091/mcp SPREADSHEET_ID=<ID du classeur> python tests/test_reel.py
```
Le test travaille dans un onglet temporaire `test-mcp-<heure>`, qu'il supprime à la fin : votre classeur est rendu
intact.

**Résultat obtenu** (classeur de test « Produit, Prix, Stock ») :
```
tools/list : 17 outils
whoami                : sheets-utilisateur-test@…
search_spreadsheets   : 1 classeur(s), dont le classeur de test
get_spreadsheet_info  : « MCP Sheets - test Acme (projet 10) », locale fr_FR, onglets ['Untitled']
read_range            : [['Produit', 'Prix', 'Stock'], ['Vélo', '299', '12'], ['Tente', '149', '30'], ['Sac à dos', '39', '80']]
read_ranges           : 2 plages
find_in_sheet         : [{'cell': 'Untitled!A3', 'value': 'Tente'}]
add_sheet             : test-mcp-232344
write_range           : 9 cellules (formules =B2*12/10 : valables dans toutes les locales)
append_rows           : 'test-mcp-232344'!A4:C4
format_range          : en-tête en gras + fond, format monétaire
batch_update (tri)    : [['Vélo', 299, 358.8], ['Tente', 149, 178.8], ['Sac', 39, 46.8]]
read_range (FORMULA)  : [['=B2*12/10']]
insert/delete_dimension : 2 lignes insérées puis supprimées
clear_range           : colonne C effacée
rename_sheet          : test-mcp-232344-r
delete_sheet          : test-mcp-232344-r (classeur rendu intact)
create_spreadsheet    : refusé pour ce compte (accès refusé : …)
OK : test réel terminé
```
`create_spreadsheet` est refusé ici parce que le compte de test est un **compte de service**, qui n'a pas d'espace
Drive. Avec un vrai compte utilisateur, le classeur est créé et son lien est renvoyé.

### 5.3 Avec MCP Inspector (interface graphique, facultatif)

```bash
npx @modelcontextprotocol/inspector
```
- Transport : **Streamable HTTP** ; URL : `http://localhost:8091/mcp` ;
- en-tête `Authorization` : `Bearer <le jeton>` ;
- **Connect** → **Tools** → **List Tools** : les 17 outils apparaissent, et on peut les appeler un par un.

## 6. Le piège des formules : la locale du classeur

**Constaté en testant :** dans un classeur en **fr_FR** (le cas chez Acme), `=B2*1.2` donne
`#ERROR! (Formula parse error.)`. L'API lit les formules **dans la langue du classeur** :

| Locale (`get_spreadsheet_info` → `locale`) | Décimale | Séparateur d'arguments | Exemple |
|---|---|---|---|
| `fr_FR` | `,` | `;` | `=SOMME(B2:B9;C2)` · `=B2*1,2` |
| `en_US` | `.` | `,` | `=SUM(B2:B9,C2)` · `=B2*1.2` |

La consigne est maintenant dans les instructions du serveur et dans la description du paramètre `values` : le modèle
la lit et adapte ses formules. Le test réel utilise `=B2*12/10`, qui marche dans toutes les locales.

## 7. Modifier ou ajouter un outil

1. Ajoutez une fonction `@mcp.tool(annotations={...})` dans `mcp_server/main.py`. Sa docstring et ses `Field(description=…)`
   sont ce que lit le modèle. Utilisez `RO`, `WRITE` ou `DESTRUCTIVE` pour les annotations.
2. Appelez Google avec `await google("GET"|"POST"|…, url, …)`. Le jeton de l'utilisateur est ajouté tout seul.
3. Ajoutez `audit("nom_outil", …)` : jamais de contenu de cellule.
4. Testez : `python tests/test_server.py`, puis `python tests/test_reel.py`.
5. Régénérez la liste publiée dans Agent Registry : `python scripts/gen_toolspec.py`.
6. Redéployez : `./scripts/deployer.sh mcp`. Dans Gemini Enterprise : **Actions** → **Reload custom actions**, puis
   activez le nouvel outil.
