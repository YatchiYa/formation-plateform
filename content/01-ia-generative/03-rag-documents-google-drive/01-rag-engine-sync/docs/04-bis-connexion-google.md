# 04-bis. Connexion Google : « Se connecter avec Google », tout mon Drive ou des dossiers

**Le but :** activer le bouton **Se connecter avec Google** de l'interface. Ensuite, chaque personne connecte **son**
Google Drive, choisit **tout son Drive** ou **des dossiers** (sélecteur Google), et active ou non la **synchro
automatique** : ajouts, modifications, renommages et suppressions se propagent seuls.

**Une seule étape manuelle (≈ 5 min, une fois par projet) :** créer le client OAuth dans la console. Google ne
propose pas d'API pour créer un client OAuth avec les portées Drive (vérifié : `gcloud iam oauth-clients` ne gère que
la fédération d'identité, sans Drive). Tout le reste (secrets, clé du sélecteur, service de notifications) est créé
par Terraform ou `deployer_shell.sh`.

---

## 1. Comment ça marche

```
  Vous ─► « Se connecter avec Google » ─► écran Google (choix du compte, accord « voir vos fichiers Drive »)
                                              │ jeton de rafraîchissement → secret <prefix>-google-tokens
  « Tout mon Drive »  ou  « Choisir des dossiers » (sélecteur Google)
          │
          ▼
  job de synchro ──(API Drive, avec VOTRE compte)──► miroir gs://<bucket>/mirror/… ──► RAG Engine
          ▲                                                Docs→.docx, Slides→.pptx, Sheets→.pdf
          │ notifications push (changes.watch)
  Google Drive ──► service public <prefix>-hook (jeton secret vérifié) ──► lance la synchro
```

- Les citations pointent vers le **document Drive d'origine**.
- Le kit ne lit **que** l'API Drive en lecture (`drive.readonly`) : il ne peut rien modifier dans votre Drive.
- La connexion vaut **pour tout le kit** : les documents d'un compte connecté sont interrogeables par toutes les
  personnes qui ouvrent l'interface. Connectez un compte dont le contenu peut être lu par ces personnes.
- Pas besoin de partager quoi que ce soit avec l'agent de service RAG : le kit recopie lui-même les fichiers.

## 2. Créer le client OAuth (console, une fois)

Console Google Cloud, projet du kit → **API et services** → **Google Auth Platform** (anciennement « Écran de
consentement OAuth »).

1. **Commencer** (ou **Branding**) : nom de l'application `Kit RAG Documents`, e-mail d'assistance (le vôtre).
   **Audience** :
   - compte Gmail ou projet sans organisation → **Externe** ;
   - Google Workspace, uniquement les personnes de votre domaine → **Interne** (pas de limite de 7 jours, pas d'écran
     « application non validée »).
   Coordonnées : votre e-mail → accepter → **Créer**.
2. **Audience** → **Utilisateurs test** → **Ajouter des utilisateurs** : les comptes Google qui se connecteront
   (Externe en mode test seulement).
3. **Accès aux données** → **Ajouter ou supprimer des champs d'application** : cochez
   `.../auth/drive.readonly`, `openid`, `.../auth/userinfo.email` (ou collez-les dans « Ajouter manuellement »)
   → **Mettre à jour** → **Enregistrer**.
4. **Clients** → **Créer un client** :
   - Type : **Application Web** ; nom : `rag-kit` ;
   - **Origines JavaScript autorisées** : `http://localhost:8080` ;
   - **URI de redirection autorisés** : `http://localhost:8080/auth/google/callback` ;
   - **Créer**, puis **Télécharger le JSON** (`client_secret_….json`).
5. Ranger le client dans le kit :

```bash
source scripts/config.sh config/test.env
bash scripts/connexion_google.sh ~/Téléchargements/client_secret_*.json
```

Résultat attendu :

```
   client 1234567890-abcdefghijkl… : type Web, redirection http://localhost:8080/auth/google/callback OK
Created version [1] of the secret [rag-kit-oauth-client].
== Connexion Google configurée. Rechargez l'interface : le bouton « Se connecter avec Google » apparaît.
```

Le script refuse un client d'un autre type ou sans la bonne URI de redirection.

## 3. Se connecter et choisir ses sources

1. `bash scripts/ouvrir_interface.sh` (proxy sur **le port 8080** : c'est celui déclaré dans le client OAuth),
   puis <http://localhost:8080>.
2. **Sources → Google Drive → Se connecter avec Google** → choisissez le compte.
   - En mode test (Externe) : écran « Google n'a pas validé cette application » → **Continuer**.
   - Cochez **« Afficher et télécharger tous vos fichiers Google Drive »** (sinon le kit refuse : « L'accès en
     lecture à Google Drive n'a pas été accordé »).
3. De retour dans l'interface : « Compte … connecté ». Sous le compte :
   - **Tout mon Drive** : vos fichiers et ceux partagés avec vous ;
   - **Choisir des dossiers** : le sélecteur Google s'ouvre, sélection multiple possible.
4. La source apparaît avec un interrupteur **auto** :
   - **auto** coché : notifications push + passe toutes les 5 min (filet de sécurité) ;
   - décoché : uniquement quand vous cliquez **Synchroniser maintenant**.

Plusieurs comptes peuvent être connectés (**Connecter un autre compte Google**). ✕ à côté d'un compte le
**déconnecte** : ses sources, son miroir et ses documents indexés sont retirés, son jeton est détruit.

> **Évitez que deux sources se recouvrent** (par exemple « Tout mon Drive » et un de ses dossiers) : les fichiers
> communs seraient indexés deux fois.

## 4. Délais mesurés (14/10/2026, notifications push actives)

| Dans Drive | Pris en compte par | Délai mesuré |
|---|---|---|
| Création d'un document | notification push | **43 s** |
| Renommage | passe planifiée (pas de notification reçue) | 2 min |
| Mise à la corbeille | notification arrivée 2 min 24 après | 2 min 27 |
| Source en « auto » décochée | passe planifiée : source ignorée ; « Synchroniser maintenant » : indexée | — |

Google regroupe et retarde parfois ses notifications : comptez **de quelques secondes à quelques minutes**, et au
plus `SYNC_SCHEDULE` (5 min par défaut) grâce au filet de sécurité. Pour moins : `SYNC_SCHEDULE="*/2 * * * *"`
(chaque passe est incrémentale : quelques secondes de Cloud Run).

## 5. À savoir (pièges)

| Sujet | Détail |
|---|---|
| **Jetons valables 7 jours en mode test** | Application Externe en « Test » : Google expire le jeton de rafraîchissement au bout de 7 jours ; la synchro de ce compte affiche alors une erreur, il faut se reconnecter. Pour l'éviter : **Audience → Publier l'application** (« En production »). `drive.readonly` étant une portée « restreinte », l'application reste « non validée » (écran d'avertissement, 100 utilisateurs au plus) tant que vous ne demandez pas la validation de Google. En **Interne** (Workspace), rien de tout cela |
| Port 8080 | La redirection OAuth et la clé du sélecteur sont déclarées pour `http://localhost:8080`. Autre port ou URL IAP : ajoutez-la dans le client OAuth, dans `OAUTH_REDIRECT_URI` et dans les référents de la clé `rag-kit-picker` |
| Fichiers non indexables | Formulaires, raccourcis, images, vidéos : comptés « ignorés ». Google Docs/Slides de plus de 10 Mo : export refusé par Drive (« non récupéré » dans le rapport) |
| Canaux push | Ouverts pour 7 jours et renouvelés automatiquement à moins de 24 h de l'expiration ; fermés quand l'auto est coupée ou la source retirée |
| Service `rag-kit-hook` public | Nécessaire pour que Google le joigne ; il n'accepte que les canaux ouverts par le kit (identifiant + jeton secret, sinon 403) et ne fait que lancer une synchro. Désactivable : `PUSH=false` (synchro planifiée seulement) |

## 6. Tester sans écran OAuth

Le compte de service du kit peut servir lui-même de « compte connecté » (mêmes appels Drive : miroir, `changes`,
notifications push). C'est ainsi que le kit a été testé automatiquement :

```bash
curl -s -X POST localhost:8080/api/sources/google -H 'Content-Type: application/json' -H 'Origin: http://localhost:8080' \
  -d '{"compte":"rag-kit-sa@<projet>.iam.gserviceaccount.com","mode":"dossiers",
       "dossiers":[{"id":"<ID du dossier partagé avec rag-kit-sa>","name":"test"}],"auto":true}'
```
