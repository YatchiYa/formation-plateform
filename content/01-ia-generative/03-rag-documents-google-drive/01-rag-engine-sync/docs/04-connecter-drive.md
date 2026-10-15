# 04. Connecter un dossier Google Drive

**Le but :** brancher un dossier Drive (et tous ses sous-dossiers) sur le kit, en 2 minutes, et savoir le vérifier.

---

## 1. Le principe

Deux comptes Google doivent pouvoir **lire** le dossier :

| Adresse | Pourquoi |
|---|---|
| `rag-kit-sa@<projet>.iam.gserviceaccount.com` | Le kit **liste** le dossier pour savoir ce qui a été ajouté ou **supprimé** |
| `service-<numéro>@gcp-sa-vertex-rag.iam.gserviceaccount.com` | RAG Engine **importe** les fichiers |

L'interface affiche ces deux adresses (cliquer pour copier) ; `source scripts/config.sh …` et
`terraform output partager_drive_avec` aussi.

Le partage est **en lecture seule** : le kit ne peut ni modifier ni supprimer vos fichiers Drive.

## 2. Pas à pas

1. Dans Google Drive, clic droit sur le dossier → **Partager** → **Partager**.
2. Collez la 1re adresse, rôle **Lecteur**, décochez **Envoyer une notification** (un compte de service ne lit pas
   ses mails), **Partager**. Recommencez avec la 2e adresse.
3. Copiez l'URL du dossier (barre d'adresse : `https://drive.google.com/drive/folders/1gYDE…`).
4. Dans l'interface, collez-la dans **Dossiers Google Drive** → **Ajouter**.
   - Le kit vérifie qu'il voit le dossier ; sinon : « Le kit ne voit pas ce dossier. Partagez-le en lecture avec … ».
   - Une synchro démarre aussitôt. Comptez 20 à 60 s pour quelques fichiers.
5. Les fichiers apparaissent dans **Documents indexés** (origine « Drive »).

> **Partager le dossier « parent »** suffit : les sous-dossiers et les fichiers ajoutés plus tard héritent du partage.

**Sans l'interface** : mettez l'ID dans `DRIVE_FOLDERS` du fichier `.env` avant le déploiement (liste séparée par des
espaces). Après le déploiement, la liste se gère dans l'interface (elle est rangée dans `gs://<bucket>/config.json`).

## 3. Vérifier

| Où | Ce qu'on doit voir |
|---|---|
| Interface, **Synchronisation** | `À jour · … · N document(s)` et `Drive « nom » : X ajouté(s) ou modifié(s)` |
| Interface, **Documents indexés** | Les fichiers du dossier **et de ses sous-dossiers** |
| Rapport `gs://<bucket>/sync/last.json` | `"statut": "ok"`, `"non_indexes": []` |

**Le piège n°1 (vérifié) :** si la 2e adresse (agent RAG) manque dans le partage, RAG Engine **ne peut pas lire les
fichiers**. Importé « par dossier », il en importe 0 **sans aucune erreur** ; c'est pourquoi le kit importe fichier
par fichier : RAG Engine répond alors `404 Unable to find some Google Drive resource(s)`, et le kit affiche le
statut **À vérifier** avec le message
« Drive « … » : N fichier(s) illisible(s) pour l'agent RAG (…). Partagez le dossier (lecteur) avec service-…@gcp-sa-vertex-rag… ».
Les autres dossiers continuent d'être synchronisés normalement.

## 4. Ce qui est pris en compte

| Dans Drive, vous… | Dans l'index, au plus tard à la synchro suivante (10 min) |
|---|---|
| ajoutez un fichier (même dans un sous-dossier) | il est indexé |
| modifiez un fichier | il est réindexé (le kit compare la date de modification Drive à la date d'indexation) |
| supprimez un fichier (corbeille) | il est retiré |
| le déplacez hors du dossier | il est retiré |
| retirez le dossier dans l'interface | tous ses fichiers sont retirés |
| retirez le partage avec le kit | **rien n'est supprimé** (sécurité : une panne de partage ne vide pas l'index) et le rapport affiche « Drive … illisible » |

**Types de fichiers** : Google Docs, Slides, Sheets, PDF, Word, PowerPoint, texte, HTML, Markdown… (liste complète :
[types supportés par RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/supported-documents)).
Un fichier non supporté (image, vidéo) est simplement compté « en échec » dans le rapport.

## 5. Drive partagé (Shared Drive) et comptes Workspace

- **Drive partagé** : ajoutez les deux adresses comme **membres** (rôle *Lecteur*) du Drive partagé, ou partagez le
  dossier voulu. Le kit liste avec `supportsAllDrives`.
- **Workspace qui interdit le partage externe** : les adresses `…iam.gserviceaccount.com` sont externes au domaine.
  Un administrateur doit autoriser le partage avec ces comptes (règle de partage par OU, ou liste d'autorisation).
  Sinon Drive refuse le partage. Non testé ici (projet sans Workspace).
