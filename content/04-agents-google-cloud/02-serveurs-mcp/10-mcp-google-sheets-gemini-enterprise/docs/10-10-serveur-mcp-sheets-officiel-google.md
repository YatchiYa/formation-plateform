# 10-10. Chemin 3 : le serveur MCP Google Sheets officiel de Google

**Ce guide répond à :** Google propose son propre serveur MCP pour Sheets (`sheetsmcp.googleapis.com`). Que fait-il,
peut-on le brancher sur Gemini Enterprise, et faut-il l'utiliser à la place du nôtre ?

> **Testé en vrai (13 octobre 2026)** sur le projet de test :
> - activation du service ;
> - `initialize` ;
> - `tools/list` ;
> - un appel d'outil, refusé sans inscription à la preview.
>
> Les réponses réelles sont plus bas.

---

## 1. Ce que c'est

Google héberge des serveurs MCP **distants** pour ses produits. Pour Sheets :

| | Valeur |
|---|---|
| Adresse | `https://sheetsmcp.googleapis.com/mcp/v1` (Streamable HTTP) |
| Services à activer | `sheets.googleapis.com` **et** `sheetsmcp.googleapis.com` |
| Authentification | OAuth 2.0, client **Application Web** |
| Portées | `drive.readonly`, `drive.file`, `spreadsheets.readonly`, `spreadsheets` |
| Statut | **Developer Preview** : le projet doit être inscrit au Google Workspace Developer Preview Program |

## 2. Ce qu'on a obtenu

```bash
gcloud services enable sheetsmcp.googleapis.com --project=$PROJET
```
**Résultat obtenu :** `Operation "operations/…" finished successfully.` L'activation passe, même sans facturation.

`initialize` puis `tools/list`, avec un jeton qui a la portée `spreadsheets` :
```
{"result":{"capabilities":{"tools":{"listChanged":false}},"protocolVersion":"2025-06-18","serverInfo":{"name":"StatelessServer","version":"ESF"}}}
get_values         | lecture  | Returns a range of values from a spreadsheet.
get_spreadsheet    | lecture  | Returns the spreadsheet content for the given spreadsheet.
update_spreadsheet | écriture | Applies one or more updates to the spreadsheet.
update_values      | écriture | Sets values in a range of a spreadsheet.
update_formulas    | écriture | Sets formulas in a range of a spreadsheet.
insert_dimension   | écriture | Inserts rows or columns in a sheet at a particular index.
```
Un appel d'outil (`get_values`) :
```
Access to this tool requires that your Google Cloud project (1016292184448) is enrolled in the Google Workspace
Developer Preview Program. Please see https://developers.google.com/workspace/preview
```
Avec l'en-tête `X-Goog-User-Project`, il faut en plus `roles/serviceusage.serviceUsageConsumer` sur ce projet
(message obtenu).

## 3. Le nôtre ou le leur ?

| | Serveur officiel (`sheetsmcp`) | Notre serveur (`sheets-mcp`) |
|---|---|---|
| Hébergement, mises à jour | Google | Nous (Cloud Run, environ 1 fichier Python) |
| Disponibilité | Preview, **sur inscription** | Tout de suite |
| Outils | 6 : valeurs, formules, structure (`update_spreadsheet` = batchUpdate), insertion | 17 : **recherche par nom**, lecture multiple, recherche de texte, création de classeur, onglets, mise en forme simple, batchUpdate… |
| Contrôle du domaine (`acme.example`) | Par le consentement Interne et les contrôles de l'admin Workspace | En plus, **dans le serveur** (refus testé) |
| Journal d'audit par outil | Journaux Google Workspace / Cloud | Le nôtre (`tool_call`), sans contenu |
| Consignes pour le modèle (locale des formules, prudence) | Les descriptions de Google, en anglais | Les nôtres, en français, avec la locale |
| Réseau | Domaine Google : rien à autoriser côté Cloud Run | `*.run.app` à autoriser dans les domaines de sortie |

**Notre recommandation :** **notre serveur** maintenant, parce qu'il est disponible, plus complet, contrôlé et
journalisé chez nous.
- Inscrivez un projet de test à la preview pour évaluer le serveur officiel.
- Passez-y quand il sera disponible pour tous, si ses 6 outils vous suffisent.
- Les deux peuvent coexister dans l'app : deux connecteurs.

## 4. Le brancher sur Gemini Enterprise (quand vous serez inscrits)

Même écran que [10-5, étape 4](10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-4--le-data-store--custom-mcp-server--console-de-lapp),
avec :

| Champ | Valeur |
|---|---|
| MCP Server URL | `https://sheetsmcp.googleapis.com/mcp/v1` |
| Authorization URL / Token URL | `https://accounts.google.com/o/oauth2/v2/auth` / `https://oauth2.googleapis.com/token` |
| Paramètres | `access_type=offline&prompt=consent&hd=acme.example` |
| Client ID / secret | Un client OAuth **du projet inscrit** (les quotas et l'inscription y sont rattachés) |
| Scopes | `https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.readonly` |
| Domaines de sortie | `sheetsmcp.googleapis.com`, `accounts.google.com`, `oauth2.googleapis.com` |

Pas de droit Cloud Run à donner : ce n'est pas un service Cloud Run.

**Non testé dans une app** : il faut l'inscription à la preview et une app. Commencez par un essai sur un projet de
test.

**Slides :** Google a aussi `slidesmcp.googleapis.com` (4 outils, preview) : comparaison dans [10-13, partie 10](10-13-serveur-mcp-google-slides.md#10-le-serveur-slides-officiel-de-google).

**Sources :**
- [Configurer le serveur MCP Sheets](https://developers.google.com/workspace/sheets/api/guides/configure-mcp-server)
- [Configurer les serveurs MCP Google Workspace](https://developers.google.com/workspace/guides/configure-mcp-servers)
- [Produits Google avec serveur MCP](https://docs.cloud.google.com/mcp/supported-products)
- [Google Workspace Developer Preview](https://developers.google.com/workspace/preview)
