# 04. Dépannage

| Symptôme / message | Cause | Solution |
|---|---|---|
| « Clé Claude absente : renseignez ANTHROPIC_API_KEY dans .env » | Pas de clé (ou clé vide) | `ANTHROPIC_API_KEY=sk-ant-…` dans `.env`, relancer `./rag`. La recherche marche déjà : `http://localhost:8765/api/recherche?q=…` |
| « Claude : … 401 / authentication » | Clé invalide ou révoquée | Nouvelle clé sur console.anthropic.com |
| « Claude : … 429 » | Limite de débit du compte | Réessayer ; `CLAUDE_MODEL=claude-sonnet-5-5` |
| La réponse ne trouve pas un document présent | Pas encore indexé, format non lu, PDF scanné | **Documents indexés** ; rapport de synchro (« en échec ») ; `/api/recherche?q=…` montre les extraits envoyés |
| « Dossier introuvable » | Chemin erroné ou disque débranché | Corriger le chemin ; l'index est gardé tant que le dossier manque |
| Fichiers OneDrive/Drive indexés vides | Fichiers « en ligne uniquement » | « Toujours garder sur cet appareil » sur le dossier |
| Google : `redirect_uri_mismatch` | URI absente du client OAuth, ou autre port | Ajouter `http://localhost:8765/auth/google/callback` au client ; garder `PORT=8765` |
| Google : `access_denied` | Compte absent des utilisateurs test | Google Auth Platform → Audience → Utilisateurs test |
| Google : « Compte … non connecté » ou `invalid_grant` | Jeton expiré (7 jours en mode test) ou accès retiré | Se reconnecter ([03](03-google-drive.md)) |
| 1er lancement long | Téléchargement du modèle local (≈ 220 Mo) | Une fois ; ou `EMBEDDINGS=voyage` |
| Tout est réindexé au démarrage | Modèle d'embeddings changé | Normal (vecteurs incompatibles) |
| `Address already in use` | Port 8765 pris | `PORT=8766` dans `.env` (et l'URI de redirection Google correspondante) |
