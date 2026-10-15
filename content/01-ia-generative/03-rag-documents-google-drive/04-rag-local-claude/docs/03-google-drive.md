# 03. Google Drive : connexion, tout le Drive ou des dossiers

**Le but :** **Se connecter avec Google** dans l'interface locale, puis indexer **tout votre Drive** ou **des
dossiers** choisis, mis à jour toutes les 60 s (seuls les fichiers changés sont relus).

Il faut **une fois** un client OAuth « Application Web » (Google exige qu'une application soit déclarée pour lire
Drive). C'est le seul usage de Google Cloud : un projet gratuit suffit, sans facturation ni service déployé.

> **Déjà fait pour le kit 1 ?** Le même client convient : ajoutez simplement l'URI de redirection
> `http://localhost:8765/auth/google/callback` (étape 4) et téléchargez à nouveau le JSON.

## 1. Créer le client OAuth (console Google Cloud, ≈ 5 min)

Projet quelconque (en créer un si besoin, gratuit) → **API et services** :

1. **Bibliothèque** → **Google Drive API** → **Activer**.
2. **Google Auth Platform** → **Commencer** : nom `RAG local`, e-mail d'assistance, **Audience : Externe**
   (compte Gmail) ou **Interne** (Workspace) → **Créer**.
3. **Audience** → **Utilisateurs test** → ajoutez votre compte Google (Externe).
   **Accès aux données** → ajoutez `.../auth/drive.readonly`, `openid`, `.../auth/userinfo.email`.
4. **Clients** → **Créer un client** → **Application Web** :
   - origine JavaScript : `http://localhost:8765` ;
   - URI de redirection : `http://localhost:8765/auth/google/callback` ;
   - **Créer** → **Télécharger le JSON**.
5. Copiez le fichier :

```bash
cp ~/Téléchargements/client_secret_*.json gcp_rag/04-rag-local-claude/data/google_client.json
```

(ou `GOOGLE_CLIENT_FILE=/chemin/vers/client.json` dans `.env`). Rechargez l'interface : le bouton
**Se connecter avec Google** apparaît.

## 2. Se connecter et choisir

1. **Se connecter avec Google** → choisissez le compte → (Externe en test) « application non validée » →
   **Continuer** → cochez l'accès aux fichiers Drive.
2. Sous le compte : **Tout mon Drive** (vos fichiers et ceux partagés avec vous) ou **Choisir des dossiers** : un
   sélecteur s'ouvre (Mon Drive, sous-dossiers, « Partagés avec moi »), cochez puis **Ajouter**.
3. La source apparaît avec son interrupteur **auto**.

Conversion : Google Docs → `.docx`, Slides → `.pptx`, Sheets → `.csv` (première feuille). Les citations ouvrent
le document dans Drive.

## 3. À savoir

| Sujet | Détail |
|---|---|
| Jeton du compte | `data/google_tokens.json` (droits 600). **Déconnecter** (✕ sous le compte) le détruit et retire ses sources |
| Mode test : 7 jours | Application Externe en « Test » : Google expire la connexion après 7 jours → se reconnecter, ou **Publier l'application** (reste « non validée », 100 utilisateurs max). Interne (Workspace) : aucune limite |
| Pas de push | En local, Google ne peut pas joindre votre ordinateur : pas de notifications, mais une passe `changes` toutes les 60 s (une passe sans changement ne télécharge rien) |
| Gros Drive | 1re passe = lecture de tout ; ensuite seulement les changements. Réconciliation complète une fois par jour |
| Recouvrement | Évitez « Tout mon Drive » + un de ses dossiers : fichiers indexés deux fois |
