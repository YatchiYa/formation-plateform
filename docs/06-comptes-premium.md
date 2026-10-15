# Comptes & contenus premium

Aujourd'hui tout est public. La plateforme est **préparée** pour les comptes :

| Déjà en place | Où |
|---|---|
| `access: premium` dans le frontmatter, badge affiché partout | `lib/content.ts`, `components/views.tsx` |
| Un point unique de décision d'accès `canRead(meta, viewer)` | `lib/viewer.ts` |
| Avec `PREMIUM_GATE=on` : les pages premium montrent l'introduction puis un encart verrouillé ; le .zip est refusé | `components/views.tsx`, `app/api/download` |
| Visiteur anonyme persistant (`atl_vid`) et progression rattachée à ce visiteur | `proxy.ts`, `app/api/progress` |
| Tables `users` et `visitors.user_id` pour rattacher l'historique anonyme à un compte | `lib/db.ts` |

## Brancher l'authentification

1. Ajouter un fournisseur (Auth.js / Better Auth : Google, GitHub, lien magique).
2. Dans `getViewer()` (`lib/viewer.ts`), lire la session et renvoyer `user: { id, plan }`.
3. À la connexion : `UPDATE visitors SET user_id = ? WHERE id = ?` puis réécrire `progress.visitor` vers l'id utilisateur pour fusionner l'historique.
4. Paiement (Stripe Checkout) → webhook qui passe `users.plan` à `premium`.
5. `PREMIUM_GATE=on`.

Rien d'autre à modifier dans les pages : elles passent toutes par `canRead()`.
