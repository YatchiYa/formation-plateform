# 06. Supprimer

1. **Détacher** les data stores de l'app (console Gemini Enterprise → app → **Connected data stores** (« Données connectées ») → retirer), sinon
   la suppression d'un data store rattaché est refusée.
2. `source scripts/config.sh config/moi.env && cd terraform && terraform destroy` : bucket (et fichiers déposés),
   data store des dépôts, planification, compte de synchro, connecteurs Terraform. L'app n'est supprimée que si le kit
   l'a créée (`CREATE_APP=true`).
3. Data stores Drive / OneDrive créés dans la console : console → **Data stores** → supprimer.

> **Un data store supprimé bloque son ID plusieurs heures** (vérifié : `is being deleted, please wait … could take a
> couple of hours`). Pour redéployer tout de suite, changez `PREFIX`.
