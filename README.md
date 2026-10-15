# Atelier — plateforme de formations

Formations pas à pas, articles, présentations et expériences en IA et cloud, publiés **depuis de simples dossiers Markdown**. Créez un dossier dans `content/`, la page existe.

```bash
cp .env.example .env && docker compose up -d --build   # http://localhost:3000
```

- **Contenu** : formations à modules, leçons, articles, diaporamas ; Mermaid, KaTeX, code coloré, vidéos, PDF, Word, PowerPoint, YouTube ; ressources et .zip téléchargeables ; références GitHub/articles.
- **Lecteur** : recherche `Ctrl K`, filtres, progression et reprise, historique, 4 langues (fr, en, ar en RTL, es), clair/sombre, mobile.
- **Monitoring** : `/admin` — visites, temps de lecture, défilement, clics, carte des clics, téléchargements, sources, appareils.
- **Prêt pour la suite** : contenus `access: premium`, point d'accès unique, schéma comptes.

Next.js 16 · React 19 · SQLite natif · Docker · Playwright.

🌐 **En ligne : https://formation.caeky.com**

✍️ **Proposer une formation : [CONTRIBUTING.md](CONTRIBUTING.md)** — une branche, un dossier Markdown, une pull request.

📚 **Documentation : [docs/](docs/README.md)** — [écrire du contenu](docs/02-ecrire-du-contenu.md), [CI/CD et déploiement](docs/07-git-ci-deploiement.md).
