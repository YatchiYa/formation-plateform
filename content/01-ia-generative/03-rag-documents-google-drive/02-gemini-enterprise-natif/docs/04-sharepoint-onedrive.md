# 04. SharePoint et OneDrive

Sources officielles (relues le 14/10/2026) :
[Terraform des connecteurs](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/connect-terraform) ·
[Configuration SharePoint côté Microsoft](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/ms-sharepoint/third-party-config) ·
[SharePoint en ingestion](https://docs.cloud.google.com/gemini/enterprise/docs/connect-sharepoint-online-ingestion) ·
[OneDrive](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/ms-onedrive/set-up-data-store).
Non testable sur le projet de test (pas de tenant Microsoft) : à dérouler avec votre administrateur Entra.

## 1. L'application Entra (administrateur Microsoft, une fois)

1. **Microsoft Entra admin center** → **App registrations** → **New registration** (nom : `Gemini Enterprise`).
2. Notez **Application (client) ID** et **Directory (tenant) ID**.
3. Authentification, au choix :
   - **identifiants fédérés (recommandé par Google)** : pas de secret ; le formulaire Gemini Enterprise donne un
     *Subject identifier* à ajouter dans **Certificates & secrets → Federated credentials** ;
   - ou un **client secret** (**Certificates & secrets → New client secret**) : rangez-le dans Secret Manager.
4. **API permissions** (Microsoft Graph, *Application*) puis **Grant admin consent**. Pour SharePoint :
   - `Sites.Read.All` indexe tous les sites **mais ne permet pas de lire les groupes et rôles** (donc les droits) ;
   - `Sites.FullControl.All`, ou `Sites.Selected` + droit `fullcontrol` donné site par site (PowerShell PnP ou
     Graph) : droits lus correctement, accès limité aux sites choisis (**recommandé**).

## 2. SharePoint fédéré, par Terraform

Le secret (si vous n'utilisez pas les identifiants fédérés) :

```bash
gcloud secrets create sharepoint-client-secret --replication-policy=user-managed --locations=europe-west1
printf '%s' 'LA_VALEUR' | gcloud secrets versions add sharepoint-client-secret --data-file=-
```

Dans un fichier `terraform/sharepoint.auto.tfvars` (Terraform le lit seul) :

```hcl
connectors = {
  sharepoint = {
    data_source  = "sharepoint_federated_search"   # forme documentée par Google
    display_name = "SharePoint"
    modes        = ["FEDERATED"]
    params = {
      instance_uri = "https://votre-tenant.sharepoint.com"   # tous les sites ; ou …/sites/un-site
      tenant_id    = "TENANT_ID"
      client_id    = "CLIENT_ID"
    }
    secret_params = { client_secret = "sharepoint-client-secret" }   # ID du secret, jamais la valeur
    entities      = [{ name = "file" }]   # nom d'entité : voir la documentation du connecteur
  }
}
```

`terraform apply`, puis `bash scripts/rattacher.sh`. Le kit donne à l'agent Gemini Enterprise la lecture du secret.
La liste exacte des entités et des paramètres facultatifs (`structured_search_filter`, ex. `Path` =
`https://votre-tenant.sharepoint.com/*`) est dans la page Terraform officielle.

## 3. OneDrive (console)

Rôle nécessaire : `roles/discoveryengine.editor`.

1. Gemini Enterprise → **Data stores** → **Create data store** → **Microsoft OneDrive** → **Select**.
2. **Connector mode** : **Data ingestion** (meilleure recherche, synchro planifiée ou **temps réel** en préversion)
   ou **Federated search** (en direct).
3. **Authentication settings** : Client ID, Client secret (ou *Subject identifier* pour les identifiants fédérés),
   Tenant ID ; en fédéré, **Login** (connexion Microsoft).
4. Fédéré : **Destinations** = URL OneDrive (`https://votre-tenant-my.sharepoint.com`), **Azure Tenant**, filtres
   de chemin éventuels. Ingestion : **Entities to sync**, **Sync frequency**, **Incremental sync frequency**.
5. **Configuration** : **Multi-region** = celui de l'app, nom du connecteur → **Create**. L'ingestion prend
   plusieurs heures (**Creating → Running → Active**).
6. Synchro temps réel (ingestion, préversion) : data store → **Data** → **Real-time sync** → **View/edit** →
   **Enable real-time sync**, secret d'environ 20 caractères → **Save** → état **Running**.
7. `bash scripts/rattacher.sh <ID du data store OneDrive>`, puis dans l'app : **autoriser** Gemini Enterprise à
   accéder à OneDrive (première connexion de chaque personne).

> **Confidentialité (fédéré) :** la question est envoyée à Microsoft, qui peut l'associer à votre identité ; avec
> plusieurs sources fédérées, elle part vers chacune.
