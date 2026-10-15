# Monitoring & analytics

Tableau de bord : `/admin` (Basic Auth). Périodes 24 h / 7 j / 30 j / 90 j, comparaison avec la période précédente.

## Ce qui est affiché

- Visiteurs uniques, pages vues, sessions, temps moyen par page, défilement moyen, clics, téléchargements
- Visiteurs actifs (5 dernières minutes)
- Trafic dans le temps (pages vues + visiteurs ; survol pour les valeurs, tableau des données)
- Pages les plus lues avec temps moyen, profondeur de défilement, clics, lien vers la carte des clics
- Éléments les plus cliqués, liens externes suivis, téléchargements, sources de trafic
- Progression des lecteurs (leçons commencées / terminées)
- Langues, appareils, navigateurs, pays (si un CDN fournit `cf-ipcountry`)
- Contenu du catalogue et couverture des traductions par langue
- Flux d'activité en direct

**Carte des clics** (`/admin/heatmap`) : la vraie page affichée en 1280 px avec la densité des clics superposée, et le classement des cibles cliquées.

## Événements collectés

| Type | Quand | Données |
|---|---|---|
| `pageview` | chaque page (navigation client comprise) | chemin, langue, référent, largeur d'écran |
| `click` | chaque clic | position (x en % de la largeur, y en px), libellé de l'élément (`data-track`, `aria-label` ou texte), lien |
| `leave` | changement de page / onglet masqué | secondes passées, défilement max (%) |
| `download` | fichier `?dl=1` ou .zip | chemin |

Chaque événement porte un identifiant visiteur aléatoire (cookie `atl_vid`, 1 an, httpOnly) et un identifiant de session (sessionStorage). Le serveur ajoute le type d'appareil et le navigateur déduits du User-Agent.

Pour nommer un clic proprement dans le tableau de bord, ajoutez `data-track="nom"` à un élément (déjà fait sur tous les boutons de la plateforme).

## Vie privée

- Aucune adresse IP stockée, aucun service tiers, aucune empreinte navigateur.
- `Do Not Track` respecté (navigateur et serveur).
- Robots et navigateurs headless ignorés (sauf `TRACK_BOTS=1`).
- Les données restent dans `DATA_DIR/analytics.db`.

Requêtes SQL directes possibles :
```bash
docker compose exec web node -e "const {DatabaseSync}=require('node:sqlite');const d=new DatabaseSync('/data/analytics.db');console.table(d.prepare('select type,count(*) n from events group by type').all())"
```
