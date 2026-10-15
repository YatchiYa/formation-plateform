# Projet 10 « à la 3S » : le serveur MCP et son agent, déployés par GitHub Actions + Terraform

**Guide pas à pas :** [docs/10-15](../docs/10-15-deployer-stack-3s.md).

| Fichier | Rôle |
|---|---|
| `deploy/` | Ce que le pipeline applique : le Terraform du projet 10 (`../terraform`) **tel quel**, état dans GCS (préfixe `10-mcp-sheets`) |
| `deploy/mcp.auto.tfvars` | La configuration déployée (mêmes valeurs que `config/10-mcp.env`) : on la change par pull request |
| `github/deploy-mcp.yml` | Le workflow, à copier dans `.github/workflows/` |

Le **socle** (bucket d'état, compte de déploiement, confiance GitHub) est celui du projet 09 :
[09/03-bis-stack-3s/bootstrap](../../09-agents-multi-projets-gemini-enterprise/03-bis-stack-3s/README.md). Un seul par projet GCP.
