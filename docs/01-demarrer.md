# Démarrer

## Avec Docker (recommandé)

```bash
cp .env.example .env          # puis changez ADMIN_PASSWORD
docker compose up -d --build
```

- Site : http://localhost:3000 (redirige vers `/fr`, `/en`, `/ar` ou `/es` selon le navigateur)
- Monitoring : http://localhost:3000/admin (identifiants `ADMIN_USER` / `ADMIN_PASSWORD`)
- Santé : http://localhost:3000/api/health

`./content` est monté dans le conteneur : **ajoutez ou modifiez un dossier, la page est à jour en ~2 s**, sans rebuild ni redémarrage. Les statistiques et la progression des lecteurs sont dans le volume Docker `atelier-data` (SQLite).

## En local

Node.js ≥ 22.13 requis (SQLite natif `node:sqlite`).

```bash
npm install
ADMIN_PASSWORD=dev npm run dev     # http://localhost:3000
```

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `ADMIN_PASSWORD` | — (obligatoire pour `/admin`) | Sans elle, `/admin` répond 404 |
| `ADMIN_USER` | `admin` | Identifiant du monitoring |
| `SITE_URL` | `http://localhost:3000` | URL publique (balises Open Graph) |
| `PREMIUM_GATE` | `off` | `on` réserve les contenus `access: premium` (voir doc 06) |
| `CONTENT_CACHE_MS` | `1500` | Fréquence de relecture de `content/` |
| `CONTENT_DIR` | `./content` | Emplacement du contenu |
| `DATA_DIR` | `./data` | Emplacement de la base SQLite |
| `TRACK_BOTS` | — | `1` pour compter aussi les navigateurs headless (tests) |

## Tests

```bash
npm run typecheck
npm run e2e        # build de production + 28 tests Playwright de bout en bout
```
