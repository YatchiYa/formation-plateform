# 02. Sources et synchro

## 1. La règle, pour toutes les sources

Toutes les `POLL_SECONDS` (60 s) et à chaque action dans l'interface, une passe (`sync.py`) :

1. demande à chaque source sa liste de fichiers, avec une **version** (date + taille sur le disque ; date de
   modification Drive pour Google) ;
2. **retire** de l'index ce qui n'est plus dans la liste ;
3. **(re)lit** seulement le nouveau et ce dont la version a changé : texte → morceaux → vecteurs ;
4. ne touche à rien d'une source **illisible** (disque débranché, compte déconnecté) : erreur affichée, index gardé.

Une source dont l'interrupteur **auto** est décoché n'est traitée que par **Synchroniser maintenant**.
Formats lus : PDF (texte), Word `.docx` (paragraphes et tableaux), PowerPoint `.pptx`, `.txt`, `.md`, `.html`,
`.csv`, `.json`. Le reste (images, `.doc`/`.xls` anciens…) est ignoré.

## 2. Dossier de l'ordinateur

**Sources → Dossier de l'ordinateur** → chemin (ex. `/home/moi/Documents/Équipe`) → **Ajouter**. Sous-dossiers
compris ; fichiers et dossiers cachés (`.…`) ignorés. Les liens des citations ouvrent le fichier depuis
l'interface (`/fichiers/…`), sans sortir du dossier choisi.

## 3. OneDrive et SharePoint, dès aujourd'hui

Le connecteur direct (Microsoft Graph) est affiché « bientôt ». En attendant, faites synchroniser la bibliothèque par
le client Microsoft, puis ajoutez son dossier comme **dossier de l'ordinateur** :

| Système | Client | Dossier à ajouter (exemple) |
|---|---|---|
| Windows / Mac | Application OneDrive (bibliothèques SharePoint : bouton **Synchroniser** dans SharePoint) | `C:\Users\moi\OneDrive - Société\Équipe` |
| Linux | `rclone` (`rclone mount` ou `rclone bisync`, remote « onedrive ») | `~/OneDrive/Équipe` |

Même idée pour Google Drive sans connexion OAuth : **Google Drive pour ordinateur** (Windows/Mac) ou `rclone`.

> Fichiers « en ligne uniquement » (OneDrive Files On-Demand, Drive en streaming) : marquez le dossier
> **Toujours garder sur cet appareil**, sinon le kit lit des fichiers vides.

## 4. Fichiers déposés

Glisser-déposer (ou cliquer) : rangés dans `data/depots/`, indexés aussitôt. ✕ dans **Documents indexés** les
supprime. 100 Mo max par fichier.

## 5. Tout réindexer

Arrêtez `./rag`, supprimez `data/index.sqlite*`, relancez : tout est relu (les sources et la connexion Google sont
gardées).
