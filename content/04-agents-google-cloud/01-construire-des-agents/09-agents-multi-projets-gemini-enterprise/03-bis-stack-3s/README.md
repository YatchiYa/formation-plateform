# 03-bis. Les agents du 01-bis, déployés « à la 3S » (GitHub Actions + Terraform, sans clé)

**Pour qui :** équipes Acme qui déploient sur la **3S** (*Self Service Stack*) : aucun `terraform apply` depuis
un poste, tout passe par une pull request et le pipeline.
**Guide pas à pas :** [docs/12-1-9](../docs/12-1-9-deployer-agents-stack-3s.md).

| Dossier / fichier | Rôle | Qui |
|---|---|---|
| `bootstrap/` | Le socle, une fois par projet : bucket d'état, compte `agents-deployer-sa`, confiance GitHub (WIF) | Admin du projet. **3S :** déjà fourni |
| `deploy/` | Ce que le pipeline applique : le Terraform du [01-bis](../01-bis-cloud-run-a2a/README.md) **tel quel**, état dans GCS | Le pipeline |
| `deploy/agents.auto.tfvars` | La configuration déployée (projet, agents, numéro de l'app) : on la change par pull request | L'équipe |
| `github/deploy-agents.yml` | Le workflow : `validate` sur PR, `plan` + `apply` au merge sur `main`. À copier dans `.github/workflows/` | L'équipe |

Le même socle sert au projet 10 (serveur MCP) : [10/stack-3s](../../10-mcp-google-sheets-gemini-enterprise/stack-3s/README.md).
