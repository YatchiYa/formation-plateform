# 10-15. Déployer le serveur MCP et son agent « à la 3S » : GitHub Actions + Terraform

**Le but :** le même déploiement que [10-3 (Terraform)](10-3-deployer-terraform.md) (serveurs MCP Sheets et Slides,
agent A2A, Agent Registry, droits de Gemini Enterprise), mais lancé par **le pipeline** au merge sur `main`, avec
l'identité `agents-deployer-sa` et un état Terraform dans un bucket GCS. Plus de `terraform apply` sur un poste.

**Tout le modèle est expliqué une fois** dans le projet 09 : [12-1-9](../../09-agents-multi-projets-gemini-enterprise/docs/12-1-9-deployer-agents-stack-3s.md)
(ce qu'est la 3S et ce qu'on n'invente pas, le socle, WIF, GitHub, dépannage). Ce guide ne donne que **ce qui change**
pour le projet 10.

> **Vérifié** (15 octobre 2026, projet de test `main-project-511608`) : `validate`, `fmt`, et **`terraform plan`
> réel** du dossier `stack-3s/deploy` : 29 ressources (Sheets + Slides + agent Cloud Run), 27 (Sheets seul + agent
> Cloud Run + agent Agent Runtime). **Pas encore exécuté :** `apply` par le pipeline.

---

## 1. Les fichiers

| Fichier | Rôle |
|---|---|
| `stack-3s/deploy/main.tf` | Backend GCS (préfixe `10-mcp-sheets`) + appel du module `../../terraform` (le Terraform du 10-3, sans copie) |
| `stack-3s/deploy/mcp.auto.tfvars` | Les valeurs de `config/10-mcp.env`, **versionnées** |
| `stack-3s/github/deploy-mcp.yml` | Le workflow : `validate` sur PR, `plan` + `apply` au merge |

## 2. Le socle : celui du 09, une fois par projet

Le serveur MCP est dans le **même projet** que les agents : le socle du 09 sert aux deux. Ses rôles par défaut
couvrent déjà le projet 10 (Agent Registry, Cloud Run, Cloud Build, et `aiplatform.admin` pour l'agent Agent Runtime).
Si le socle n'existe pas encore : [12-1-9, partie 3](../../09-agents-multi-projets-gemini-enterprise/docs/12-1-9-deployer-agents-stack-3s.md#3-le-socle-une-fois).
**3S :** demandez le fournisseur WIF, le compte de déploiement et le bucket d'état.

## 3. Ce qui change par rapport à 10-3

| 10-3 (poste) | 10-15 (pipeline) |
|---|---|
| `source scripts/config.sh config/10-mcp.env` (variables `TF_VAR_*`) | `stack-3s/deploy/mcp.auto.tfvars` (fichier versionné, mêmes valeurs) |
| `OAUTH_CLIENT_IDS=a,b` | `oauth_client_ids = ["a", "b"]` |
| `ALLOWED_DOMAINS=acme.example` | `allowed_domains = ["acme.example"]` |
| `NUM_APP=…` | `ge_project_number = "…"` |
| État dans `terraform/terraform.tfstate` | `gs://<projet>-tfstate/10-mcp-sheets/` |

**Le client OAuth** ([10-5, étape 1](10-5-gemini-enterprise-connecteur-mcp-natif.md)) se crée toujours **à la
main**, dans la console : Google n'a pas d'API pour les clients OAuth « Application Web ». Son **ID** (pas son
secret) va dans `oauth_client_ids` ; sans lui, Terraform s'arrête avant de créer le serveur (précondition).
Le **secret** du client ne passe jamais par Git ni par le pipeline : il se colle dans l'app Gemini Enterprise.

## 4. Brancher et déployer

```bash
mkdir -p .github/workflows
cp 10-mcp-google-sheets-gemini-enterprise/stack-3s/github/deploy-mcp.yml .github/workflows/
```

Les 3 variables du dépôt (`GCP_WIF_PROVIDER`, `GCP_DEPLOYER_SA`, `GCP_TFSTATE_BUCKET`) sont **les mêmes** que pour
le 09 ; si elles existent déjà, rien à faire. Puis :

```bash
git switch -c mcp/premier-deploiement
# modifier stack-3s/deploy/mcp.auto.tfvars : projet, numéro, ID du client OAuth, domaine
git commit -am "mcp : premier déploiement" && git push -u origin mcp/premier-deploiement
```

Pull request → `verifier` (`fmt`, `validate`) → relecture → merge → `deployer` (`plan`, `apply`, 5 à 8 min avec
les deux images). Tests : [10-8](10-8-tester-simuler-verifier.md).

| Je veux | Dans `mcp.auto.tfvars` |
|---|---|
| Sheets seul | `produits_mcp = ["sheets"]` ([10-14](10-14-un-serveur-a-la-fois.md)) |
| L'agent aussi sur Agent Runtime | `deploy_agent_runtime = true` |
| Donner l'accès à l'app | `ge_project_number = "<NUMÉRO du projet de l'app>"` |

## 5. Déjà déployé avec 10-3 sur le poste ?

L'état local et l'état GCS sont **distincts** : le pipeline voudrait tout recréer (et échouerait sur les noms
déjà pris). Déplacer l'état une fois, avant le premier merge :

```bash
cd 10-mcp-google-sheets-gemini-enterprise/terraform && terraform state pull > /tmp/etat-10.json
cd ../stack-3s/deploy && terraform init -backend-config=bucket=<PROJET>-tfstate
terraform state push /tmp/etat-10.json
# les ressources passent dans le module « mcp » (les sources « data. » se relisent seules)
terraform state list | grep -v '^data\.' | while read -r a; do terraform state mv "$a" "module.mcp.$a"; done
terraform plan    # attendu : « without changing any real infrastructure » (seules les sorties changent)
```

> **Vérifié** sur une copie de l'état réel du projet 10 (36 objets dans l'état, Sheets + Slides + agent Cloud Run et Agent
> Runtime) : après ces commandes, `plan` n'annonce **aucune** création, modification ni suppression.

Plus simple sur un projet de test : `terraform destroy` en local, puis laisser le pipeline tout recréer.

## 6. Nettoyer

`terraform destroy` dans `stack-3s/deploy` (avec le compte du pipeline : [12-1-9, partie 6](../../09-agents-multi-projets-gemini-enterprise/docs/12-1-9-deployer-agents-stack-3s.md#6-tester-le-pipeline-sans-github-option)),
puis retirer `.github/workflows/deploy-mcp.yml`. Le socle se supprime depuis le 09, en dernier.
