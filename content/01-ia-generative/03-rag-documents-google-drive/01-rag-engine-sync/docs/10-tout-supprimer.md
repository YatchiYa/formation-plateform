# 10. Tout supprimer

**Le but :** retirer le kit proprement, puis (si besoin) arrêter le coût fixe de RAG Engine.

**Ce qui n'est jamais touché :** vos fichiers Google Drive (le kit n'y a que la lecture).

---

## 1. Déployé avec Terraform

```bash
cd gcp_rag/01-rag-engine-sync
source scripts/config.sh config/test.env
cd terraform && terraform destroy
```

Supprime toutes les ressources (vérifié en v1 : `Destroy complete! Resources: 42 destroyed.` ; 53 en v2) : service, job, planification, corpus **et tout l'index**, processeur Document AI,
images, **bucket (fichiers déposés compris)**, comptes de service et leurs droits. Les API restent activées
(`disable_on_destroy = false`), et le palier RagManagedDb n'est **pas** modifié (`deletion_policy = "ABANDON"`).

## 2. Déployé avec le script shell

```bash
source scripts/config.sh config/test.env
bash scripts/supprimer_shell.sh        # demande de taper « oui »
```

Même périmètre que `terraform destroy`.

## 3. Arrêter le coût fixe (RagManagedDb)

Après la suppression, la base Spanner de RAG Engine **continue d'être facturée** (≈ 91 €/mois en Basic, voir
[08](08-couts.md)). Pour l'arrêter, passez le projet+région en **Unprovisioned**.

> **Attention : efface TOUS les corpus RAG Engine du projet dans cette région**, y compris ceux d'autres équipes ou
> d'autres kits. Irréversible. Vérifiez d'abord qu'il n'en reste aucun :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/ragCorpora" | grep displayName
# Rien affiché => aucun corpus : on peut déprovisionner
curl -s -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/ragEngineConfig" \
  -d '{"ragManagedDbConfig": {"unprovisioned": {}}}'
```

**Exécutée le 14/10/2026** sur le projet de test, après `terraform destroy` (aucun corpus restant) : l'état passe à
`unprovisioned` en moins d'une minute, et la facturation Spanner s'arrête.

**Pour reconstruire ensuite**, RAG Engine ne se réactive pas tout seul : gardez `RAG_TIER=basic` dans la
configuration (valeur des fichiers `config/*.env` fournis). Vérifié : depuis un projet déprovisionné, `terraform apply`
remet le palier Basic **puis** crée le corpus ; le script shell fait de même (étape 5).

## 4. Le bucket de Cloud Build

`gcloud builds submit` crée lui-même un bucket `<projet>_cloudbuild` (le code envoyé à la construction). Ni
`terraform destroy` ni `supprimer_shell.sh` n'y touchent, car d'autres constructions du projet peuvent s'en servir.
S'il ne sert à rien d'autre : `gcloud storage rm -r gs://<projet>_cloudbuild`.

## 5. Retirer les partages Drive

> Si vous redéployez ensuite, il faudra **repartager** avec le nouveau `rag-kit-sa@…` : même adresse, nouvelle
> identité (vérifié). L'ancien partage reste dans Drive comme une permission sans adresse : supprimez-la.

Dans Drive, sur chaque dossier : **Partager** → retirer `rag-kit-sa@<projet>.iam.gserviceaccount.com` et
`service-<numéro>@gcp-sa-vertex-rag.iam.gserviceaccount.com` (le second sert à **tous** les corpus RAG Engine du
projet : ne le retirez que si plus rien n'en dépend).
