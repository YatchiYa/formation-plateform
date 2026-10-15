# 11. La CLI `ragkit` : activer, désactiver, déployer, surveiller

**Le but :** piloter le kit avec une seule commande, sans retenir les commandes gcloud ni Terraform. Chaque brique
s'active ou se désactive dans le fichier `config/*.env`, puis `./ragkit deploy` applique **seulement la différence**.

`ragkit` n'a besoin que de Python 3 (bibliothèque standard). Il s'appuie sur `scripts/config.sh`, Terraform et les
scripts existants : rien n'est caché, chaque commande lance ce que décrivent les docs 03-x.

> **Testé en vrai** le 14/10/2026 : `status`, `briques`, `activer`/`desactiver`/`set` (sur une copie de la
> configuration), `deploy --plan` (désactiver `planif` + `push` → `0 to add, 2 to change, 3 to destroy` : la
> planification, le service `rag-kit-hook` et son droit public), `deploy`, `sync`, `logs job`, `test` (TOUT EST OK).

---

## 1. Les commandes

| Commande | Effet |
|---|---|
| `./ragkit status` | Configuration, briques actives, URL déployée, corpus, adresse push, dernière synchro et ses alertes |
| `./ragkit briques` | Les briques activables et leur état |
| `./ragkit activer <brique>` / `desactiver <brique>` | Modifie la variable dans le `.env` (garde le commentaire) |
| `./ragkit set VAR valeur` | Change n'importe quelle valeur du `.env` (`MODEL`, `SYNC_SCHEDULE`, `USERS`…) |
| `./ragkit deploy [--plan] [--shell]` | Terraform `apply` (ou `plan`), ou le script gcloud |
| `./ragkit ouvrir` | Ouvre l'interface sur <http://localhost:8080> |
| `./ragkit sync` | Lance une synchro, attend la fin, affiche le rapport |
| `./ragkit logs [job\|web\|hook]` | Derniers journaux (pour le job : rapports de passe et erreurs seulement) |
| `./ragkit google <client.json>` | Configure la connexion Google ([04-bis](04-bis-connexion-google.md)) |
| `./ragkit test [URL] [question attendu]` | Test de bout en bout (interface ouverte) |
| `./ragkit detruire [--shell]` | Supprime tout (Terraform demande `yes`, le script `oui`) |

Autre configuration : `./ragkit -c config/prod.env status` (ou `export RAGKIT_CONFIG=config/prod.env`).

## 2. Les briques

| Brique | Variable | Activée | Désactivée |
|---|---|---|---|
| `push` | `PUSH` | Service public `rag-kit-hook` + canaux Drive : synchro en secondes | Plus de service public ; synchro planifiée et bouton seulement |
| `layout` | `LAYOUT_PARSER` | Document AI lit tableaux et titres des PDF (payant) | Parsing simple, gratuit ; **tout est réindexé** à la passe suivante |
| `planif` | `SYNC_SCHEDULE` | Passe toutes les 5 min (filet de sécurité) | Push et bouton seulement |

Exemple, un kit sans service public et synchro toutes les 2 min :

```bash
./ragkit desactiver push
./ragkit set SYNC_SCHEDULE "*/2 * * * *"
./ragkit deploy --plan     # lire le plan
./ragkit deploy
```

**Ajouter une brique** (pour un mainteneur) : une ligne dans le dictionnaire `BRIQUES` de `ragkit`, la variable dans
`config/*.env`, `scripts/config.sh` (`TF_VAR_…`), `terraform/variables.tf` (+ `count` sur les ressources concernées)
et `scripts/deployer_shell.sh`.
