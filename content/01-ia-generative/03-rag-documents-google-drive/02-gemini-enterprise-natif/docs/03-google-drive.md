# 03. Google Drive (fédéré)

**Ce que vous obtenez :** chaque personne interroge **son** Drive (et les fichiers partagés avec elle, du domaine)
depuis Gemini Enterprise, toujours à jour, sans copie chez Google Cloud.

Source : [documentation officielle](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/gdrive/set-up-data-store)
(relue le 14/10/2026). Non testable sur le projet de test (compte Gmail : pas d'identifiant client Workspace).

## 1. Prérequis (administrateur Workspace)

1. Console d'administration Google → **Données et confidentialité / Fonctionnalités intelligentes** : activer
   « Smart features in Google Workspace » et « Smart features in other Google products ».
2. Si les applications OAuth sont restreintes : autoriser l'application OAuth gérée par Google pour Gemini
   Enterprise (liste d'autorisation).
3. Documents dans un **Drive partagé du domaine** ou appartenant à un utilisateur du domaine.
4. Le fournisseur d'identité de Gemini Enterprise configuré (Google Identity pour Workspace).

## 2. Créer le data store (console)

Connecté avec **un compte du domaine Workspace** :

1. Console Google Cloud → **Gemini Enterprise** → projet de l'app.
2. **Data stores** → **Create data store**.
3. **Source** : cherchez **Google Drive** → **Select** → **Continue**.
4. **Configuration** : **Multi-region** = celui de l'app (`eu`), **Data connector name** (minuscules, chiffres,
   `-`, `_` ; ex. `drive-entreprise`), chiffrement (clé Google ou Cloud KMS).
5. **Create**, puis attendre l'état **Active** dans **Data stores**.
6. Rattacher : `bash scripts/rattacher.sh <ID du data store>` (ID affiché dans la liste des data stores).

> **Changement 2026 :** les filtres par dossier ou Drive partagé **ne sont plus proposés** pour les nouveaux data
> stores Drive : la recherche porte sur tout ce que la personne peut lire dans le domaine. Pour restreindre à
> quelques dossiers : le kit 1 (dossiers choisis) ou des droits Drive adaptés.

## 3. Vérifier

```bash
gcloud auth login vous@entreprise.com          # une vraie personne : les comptes de service sont refusés (403)
source scripts/config.sh config/moi.env
bash scripts/question.sh "Que dit la note de service sur le télétravail ?"
```

La réponse doit citer des documents Drive (liens `docs.google.com`). Documents d'un autre domaine absents ? Gemini
Enterprise → app → **Manage web app features** → **Include cross-domain documents**.
