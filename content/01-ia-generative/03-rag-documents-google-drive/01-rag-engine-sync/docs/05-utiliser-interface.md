# 05. Utiliser l'interface

**Le but :** ouvrir l'interface, brancher des documents, poser des questions, et savoir lire ce qu'elle affiche.

---

## 1. L'ouvrir

Le service est **privé**. Le proxy de gcloud l'ouvre sur votre poste avec votre identité :

```bash
source scripts/config.sh config/test.env
bash scripts/ouvrir_interface.sh          # = gcloud run services proxy rag-kit --region=… --port=8080
```

Puis <http://localhost:8080>. Laissez le terminal ouvert (Ctrl+C pour fermer). Un collègue fait pareil sur son poste,
s'il est dans `USERS` (ou propriétaire du projet).

## 2. L'écran

```
┌──────────────────────────────┬──────────────────────────────────────────────────┐
│ Documents Drive              │ Assistant                  [Nouvelle conversation]│
│ projet · région              │                                                  │
│                              │                      Votre question ─────────▶   │
│ Dossiers Google Drive        │  ┌────────────────────────────────────────────┐  │
│ [URL ou ID du dossier][Ajouter]│ Réponse… avec les sources surlignées      │  │
│ 2 adresses à mettre en partage│  │ Sources : ▇politique-teletravail▇         │  │
│ • Mon dossier             ✕  │  └────────────────────────────────────────────┘  │
│                              │                                                  │
│ Déposer des fichiers         │                                                  │
│ ┌ Glissez vos fichiers ici ┐ │                                                  │
│                              │                                                  │
│ Synchronisation              │                                                  │
│ À jour · 14/10 à 13:05 · …   │                                                  │
│ [Synchroniser maintenant]    │                                                  │
│                              │                                                  │
│ Documents indexés (12)       │ [Votre question…                    ] [Envoyer]  │
└──────────────────────────────┴──────────────────────────────────────────────────┘
```

Sur téléphone, les panneaux s'empilent (gestion en haut, conversation en dessous).

| Zone | Ce qu'on y fait |
|---|---|
| **Sources → Google Drive** | **Se connecter avec Google**, puis **Tout mon Drive** ou **Choisir des dossiers** (sélecteur Google) ; interrupteur **auto** par source ; ✕ pour retirer une source ou déconnecter un compte ([04-bis](04-bis-connexion-google.md)) |
| **Sources → Dossier partagé avec le kit** | Sans connexion : coller l'URL d'un dossier partagé avec les 2 adresses ([04](04-connecter-drive.md)) |
| **Sources → OneDrive, SharePoint** | Affichés « bientôt » |
| **Déposer des fichiers** | Glisser-déposer ou cliquer ; plusieurs fichiers à la fois ; 30 Mo max par fichier (au-delà : mettez-le dans Drive) |
| **Synchronisation** | État de la dernière passe ; « Synchroniser maintenant » ; avertissements (partage manquant, fichier en échec) |
| **Documents indexés** | Tout ce que l'assistant peut lire ; ✕ sur un fichier **déposé** le supprime (les fichiers Drive se suppriment dans Drive) |
| **Assistant** | Questions ; chaque source est un lien surligné vers le document (Drive, ou téléchargement pour un dépôt) |

## 3. Bien poser ses questions

- L'assistant ne répond **qu'avec les documents**. S'il ne trouve pas : « Je ne trouve pas cette information dans
  les documents. » — il n'invente pas.
- Il cherche plusieurs fois si besoin ; une question précise (« Quelle est l'indemnité mensuelle de télétravail ? »)
  marche mieux qu'un mot seul.
- **Nouvelle conversation** repart de zéro (le contexte des questions précédentes est oublié).
- Si deux documents se contredisent, il le signale en citant les deux.

## 4. Les messages et ce qu'ils veulent dire

| Message | Sens | Que faire |
|---|---|---|
| « Synchronisation lancée. » | Le job tourne (20 s à quelques minutes) | Rien, l'état se met à jour seul |
| « Synchronisation lancée. » alors qu'une autre tournait | Les passes se suivent (une seule à la fois sur le corpus) | Rien : la vôtre attend son tour puis prend vos changements |
| **À vérifier** + « N fichier(s) illisible(s) pour l'agent RAG » | Agent RAG absent du partage | Ajouter la 2e adresse au partage ([04](04-connecter-drive.md)) |
| « Drive « … » illisible » | Le kit ne voit plus le dossier (partage retiré, dossier supprimé) | Repartager, ou retirer le dossier de la liste |
| « Le kit ne voit pas ce dossier » (à l'ajout) | 1re adresse absente du partage | Partager avec `rag-kit-sa@…` puis réessayer |
| « La recherche dans les documents a échoué » | Problème de droits ou de service côté Google | [09-depannage](09-depannage.md) |

## 5. Lancer en local

Pour modifier l'interface ou l'agent sans redéployer, sur le **même** corpus et bucket :

```bash
source scripts/config.sh config/test.env
python3.12 -m venv .venv && .venv/bin/pip install -r app/requirements.txt
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly
export CORPUS="$(cd terraform && terraform output -raw corpus)" LAYOUT_PARSER="" SYNC_JOB="" \
       GOOGLE_GENAI_USE_VERTEXAI=true GOOGLE_CLOUD_PROJECT=$PROJECT_ID GOOGLE_CLOUD_LOCATION=$MODEL_LOCATION
cd app && ../.venv/bin/python main.py      # http://localhost:8080
```

- `SYNC_JOB=""` : « Synchroniser » fait la passe **dans le processus** (pas besoin du job).
- Drive : en local, c'est **votre** compte qui liste les dossiers (d'où le scope `drive.readonly`). Le mode local a
  été testé sur les dépôts, la synchro et le chat ; la partie Drive en local ne l'a pas été (elle l'a été en déployé).
- `LAYOUT_PARSER=""` : parsing simple ; mettez le nom du processeur pour le garder (voir `terraform state show`).
  **Attention :** changer de parsing réindexe tout à la passe suivante.
