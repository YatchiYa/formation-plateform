"""Faire l'inventaire du projet des agents, et le nettoyer au besoin.

À quoi sert ce script
  Liste tout ce que les guides ont créé dans le projet des agents (Cloud Run, Agent Runtime, Agent Registry,
  Dialogflow, comptes de service, dépôts d'images, filtres Model Armor, et en option les agents de l'app).
  Sans --supprimer, il ne fait QUE lister. Avec --supprimer, il supprime la liste après confirmation.

Quand l'utiliser
  - docs/12-1-1, partie 13 (tout nettoyer) et 10.5 (supprimer l'agent Dialogflow) ;
  - docs/12-1-2, partie 10 (vérifier qu'il ne reste rien après `terraform destroy`) ;
  - docs/12-3, partie 3.8 (retirer UN agent : --agent).

Prérequis
  - Dans le dossier du projet, venv activé ; configuration chargée dans ce terminal :
      source scripts/config.sh config/12-1-agents-dans-projet-exp.env
    Variables lues : PROJET_AGENTS (--projet), REGION (--region), GE_LOCATION (--location) ;
    pour le type app : PROJET_APP et APP_ID.
  - gcloud connecté (gcloud auth login) ; composants gcloud pour agent-registry et model-armor (gcloud beta).
  - Droits : pour lister, des droits de lecture ; pour supprimer, roles/owner ou les rôles d'admin de
    docs/12-1-1, partie 4 (run, aiplatform, agentregistry, iam, artifactregistry, modelarmor, dialogflow…).
  - Une API non activée ou un droit manquant n'arrête pas le script : ce type est signalé « illisible »
    et ignoré.

Utilisation
  Après « source scripts/config.sh config/<fichier>.env » (projet, région, localisation lus dans la
  configuration) :

    python scripts/nettoyer.py                                  # INVENTAIRE seulement : rien n'est supprimé
    python scripts/nettoyer.py --agent meteo                    # seulement ce qui appartient à l'agent meteo
    python scripts/nettoyer.py --types cloudrun,runtime         # seulement ces types
    python scripts/nettoyer.py --supprimer                      # supprimer la liste (confirmation demandée)
    python scripts/nettoyer.py --supprimer --avec-terraform     # y compris ce que Terraform a créé (plus bas)

  Options :
    --projet ID         projet des agents, défaut $PROJET_AGENTS, ex. --projet aiml-gemini-ent-exp-0zga
    --region R          région, défaut $REGION (sinon europe-west1), ex. --region europe-west1
    --location L        localisation Model Armor et app (eu, us, global), défaut $GE_LOCATION (sinon eu)
    --types T1,T2       types à regarder, ex. --types dialogflow
    --agent CLE         seulement cet agent, ex. --agent velo ; images, armor et dialogflow sont alors exclus
                        (partagés par tous les agents)
    --supprimer         supprimer ce qui est listé (sinon : inventaire seulement)
    --avec-terraform    inclure ce que Terraform a créé (état Terraform perdu, par exemple)
    --oui               ne pas demander de confirmation (scripts), ex. --supprimer --oui

Types : app, registry, cloudrun, runtime, dialogflow, comptes, images, armor (par défaut : tous sauf app).

Ne regarde QUE ce que les guides créent, reconnu à son nom :
  - Cloud Run       <clé>-a2a, <clé>-a2a-shell, <clé>-a2a-console
  - Agent Runtime   <clé>-agent, <clé>-shell, <clé>-console
  - Agent Registry  les mêmes noms que Cloud Run (les agents Agent Runtime partent avec eux)
  - Dialogflow      « Accueil magasin… »
  - comptes         <clé>-a2a-sa, -a2a-shell-sa, -a2a-console-sa, -agent-sa, -shell-sa, -console-sa
                    (+ leurs rôles),
                    agents-build-sa / agents-a2a-build-sa (construction des images)
  - images          dépôts agents-a2a, agents-shell, agents-console
  - armor           agents-, console-, trio-a2a-, trio-runtime-, demo09- … -prompt/response-shield
  - app             (si APP_ID est renseigné) les agents de l'app dont le nom commence par un nom du catalogue
Tout le reste du projet (autres services, comptes Google, etc.) est ignoré.

Créé par Terraform (repéré « [terraform] ») : ignoré sauf --avec-terraform. Supprimez-le plutôt avec
`terraform destroy` (ou en retirant l'agent de AGENTS) : sinon l'état de Terraform croit encore qu'il existe.

Ce qu'il lit / ce qu'il supprime
  Sans --supprimer : LECTURE SEULE (listes gcloud et API REST), relançable à volonté.
  Avec --supprimer : DESTRUCTIF et définitif. Demande de taper l'ID du projet (sauf --oui). Supprime aussi les
  sessions des agents Agent Runtime et retire les rôles des comptes de service avant de les supprimer.
  Aucun fichier local n'est modifié (env-<clé>.yaml, carte-<clé>.json restent : rm -f à la main).

Résultat attendu
  == Inventaire : projet …, région europe-west1, localisation eu
     types : registry, cloudrun, runtime, dialogflow, comptes, images, armor
    cloudrun    meteo-a2a-shell
    runtime     meteo-agent  (ID)                                           [terraform]
  Inventaire seulement : N élément(s) supprimable(s). Pour supprimer : --supprimer
  Projet propre : « Rien à nettoyer. »
  Avec --supprimer : « supprimé   cloudrun    meteo-a2a-shell », puis « Terminé : N supprimé(s), 0 échec(s). »

Erreurs fréquentes et que faire
  - « Projet inconnu : … » : configuration pas chargée -> source scripts/config.sh config/<fichier>.env,
    ou --projet.
  - « (<type> : illisible, ignoré : …) » : API non activée, droit manquant ou composant gcloud absent ;
    les autres
    types sont quand même traités. Activer l'API ou obtenir le droit si ce type compte.
  - « (app : PROJET_APP / APP_ID vides …) » : normal sans app ; sinon remplir le fichier et recharger.
  - « Annulé : rien n'a été supprimé. » : la réponse n'était pas exactement l'ID du projet.
  - « ÉCHEC      <type> <nom> : … » : relancer la commande (seuls les restes sont retentés).
  - N élément(s) [terraform] ignoré(s) : `terraform destroy` dans 01-bis / 02-bis / 04-bis. Si vous utilisez
    --avec-terraform, ensuite `terraform state rm '<adresse>'` pour que Terraform les oublie.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
# Une clé d'agent : mêmes règles que scripts/nouvel_agent.py (lettre, puis lettres/chiffres, 2 à 15).
CLE = r"[a-z][a-z0-9]{1,14}"
# Pour chaque type : 1er motif = « est-ce un élément créé par les guides ? » (sinon : jamais supprimé) ;
# 2e motif = « porte-t-il le nom que lui donne Terraform ? » -> marqué [terraform].
# Les méthodes shell et console ajoutent -shell / -console (Cloud Run, comptes) ou remplacent -agent
# (Agent Runtime) : c'est ce qui les distingue.
MOTIFS = {   # type -> (motif du nom, motif « créé par Terraform »)
    "cloudrun": (rf"^({CLE})-a2a(-shell|-console)?$", rf"^{CLE}-a2a$"),
    "registry": (rf"^({CLE})-a2a(-shell|-console)?$", rf"^{CLE}-a2a$"),
    "runtime": (rf"^({CLE})-(agent|shell|console)$", rf"^{CLE}-agent$"),
    "comptes": (rf"^({CLE})-(a2a-sa|a2a-shell-sa|a2a-console-sa|agent-sa|shell-sa|console-sa|build-sa|a2a-build-sa)@",
                rf"^{CLE}-(a2a|agent|a2a-build)-sa@"),
    "images": (r"^agents-(a2a|shell|console)$", r"^agents-a2a$"),
    "armor": (r"^(agents|console|trio-a2a|trio-runtime|demo09)-(prompt|response)-shield$", r"^(trio-a2a|trio-runtime|demo09)-"),
    "dialogflow": (r"^Accueil magasin", r"^Accueil magasin$"),
}
ROLES_AGENT = ["aiplatform.user", "logging.logWriter", "modelarmor.user", "monitoring.metricWriter", "cloudtrace.agent"]


def gcloud(*args, json_out=True):
    """Lance gcloud ; renvoie sa sortie JSON (texte si json_out=False) ; RuntimeError si échec."""
    r = subprocess.run(["gcloud", *args] + (["--format=json"] if json_out else []), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "erreur gcloud")
    return json.loads(r.stdout or "[]") if json_out else r.stdout


def rest(methode, url, projet, corps=None):
    """Appelle une API REST Google avec le jeton de gcloud ; renvoie le JSON (HTTPError si erreur)."""
    jeton = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
    # X-Goog-User-Project : quota et activation de l'API comptés sur CE projet. Sans lui, certaines API
    # (Dialogflow, Discovery Engine) refusent un jeton d'utilisateur (projet de quota absent ou différent).
    req = urllib.request.Request(url, json.dumps(corps).encode() if corps else None, method=methode,
                                 headers={"Authorization": f"Bearer {jeton}", "Content-Type": "application/json",
                                          "X-Goog-User-Project": projet})
    with urllib.request.urlopen(req, timeout=60) as rep:
        return json.loads(rep.read() or b"{}")


class Inventaire:
    """Liste des éléments trouvés ; une méthode par type (app, registry, cloudrun…) remplit self.elements."""

    def __init__(self, a):
        self.a, self.p, self.r, self.loc = a, a.projet, a.region, a.location
        self.elements = []   # (type, nom affiché, tag terraform, fonction de suppression)

    def garder(self, type_, nom):
        """None = à ignorer (pas créé par les guides, ou pas l'agent --agent) ; True = nom Terraform."""
        motif, motif_tf = MOTIFS[type_]
        if not re.search(motif, nom):
            return None
        if self.a.agent and not nom.startswith(f"{self.a.agent}-"):
            return None
        return bool(re.search(motif_tf, nom))

    def ajouter(self, type_, nom, supprimer, cle=None):
        """Ajoute l'élément s'il est à garder ; cle = nom à tester si le nom affiché contient aussi l'ID."""
        tf = self.garder(type_, cle or nom)
        if tf is None:
            return
        self.elements.append((type_, nom, tf, supprimer))

    # Chaque suppression est une lambda avec argument par défaut (nom=nom) : la valeur est figée à ce tour de
    # boucle ; sans cela, toutes les lambdas supprimeraient le dernier élément de la boucle.

    # --- les types ---------------------------------------------------------------------------------------------
    def app(self):
        """Agents de l'app dont le nom affiché commence par un nom du catalogue (jamais [terraform])."""
        projet_app, app_id = os.getenv("PROJET_APP"), os.getenv("APP_ID")
        if not (projet_app and app_id):
            print("  (app : PROJET_APP / APP_ID vides dans la configuration, ignoré)")
            return
        # Localisation « global » : point d'accès sans préfixe ; eu / us : point d'accès régional.
        host = "discoveryengine.googleapis.com" if self.loc == "global" else f"{self.loc}-discoveryengine.googleapis.com"
        base = f"https://{host}/v1alpha/projects/{projet_app}/locations/{self.loc}/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
        noms = [a["nom_affiche"] for k, a in json.load(open(ICI / "agents/trio/catalogue.json")).items()
                if not self.a.agent or k == self.a.agent]
        for ag in rest("GET", base, projet_app).get("agents", []):
            nom = ag.get("displayName", "")
            if any(nom.startswith(n) for n in noms):
                self.elements.append(("app", f"{nom}  ({ag['name'].split('/')[-1]})", False,
                                      lambda n=ag["name"]: rest("DELETE", f"https://{host}/v1alpha/{n}", projet_app)))

    def registry(self):
        """Services déclarés dans Agent Registry (agents Cloud Run, déclarés avec leur carte A2A)."""
        for s in gcloud("agent-registry", "services", "list", f"--location={self.r}", f"--project={self.p}"):
            nom = s["name"].split("/")[-1]
            self.ajouter("registry", nom, lambda nom=nom: gcloud(
                "agent-registry", "services", "delete", nom, f"--location={self.r}", f"--project={self.p}", "--quiet", json_out=False))

    def cloudrun(self):
        """Services Cloud Run (agents A2A)."""
        for s in gcloud("run", "services", "list", f"--region={self.r}", f"--project={self.p}"):
            nom = s["metadata"]["name"]
            self.ajouter("cloudrun", nom, lambda nom=nom: gcloud(
                "run", "services", "delete", nom, f"--region={self.r}", f"--project={self.p}", "--quiet", json_out=False))

    def runtime(self):
        """Agents Agent Runtime (reasoningEngines), reconnus à leur nom affiché ; ID entre parenthèses."""
        url = f"https://{self.r}-aiplatform.googleapis.com/v1/projects/{self.p}/locations/{self.r}/reasoningEngines"
        for e in rest("GET", url, self.p).get("reasoningEngines", []):
            nom = e["displayName"]
            # force=true : supprime aussi les sessions (sinon refus dès que l'agent a servi)
            self.ajouter("runtime", f"{nom}  ({e['name'].split('/')[-1]})", lambda n=e["name"]: rest(
                "DELETE", f"https://{self.r}-aiplatform.googleapis.com/v1/{n}?force=true", self.p), cle=nom)

    def dialogflow(self):
        """Agents Dialogflow CX « Accueil magasin… » (docs/12-1-1, partie 10)."""
        url = f"https://{self.r}-dialogflow.googleapis.com/v3/projects/{self.p}/locations/{self.r}/agents"
        try:
            agents = rest("GET", url, self.p).get("agents", [])
        except urllib.error.HTTPError as e:
            print(f"  (dialogflow : illisible, erreur {e.code} : API non activée, pas de droit, ou erreur passagère ; ignoré)")
            return
        for ag in agents:
            self.ajouter("dialogflow", ag["displayName"], lambda n=ag["name"]: rest(
                "DELETE", f"https://{self.r}-dialogflow.googleapis.com/v3/{n}", self.p))

    def comptes(self):
        """Comptes de service des agents et de la construction des images."""
        for sa in gcloud("iam", "service-accounts", "list", f"--project={self.p}"):
            self.ajouter("comptes", sa["email"], lambda e=sa["email"]: self.supprimer_compte(e))

    def supprimer_compte(self, email):
        """Retire tous les rôles du compte sur le projet, puis supprime le compte."""
        # D'abord ses rôles sur le projet (sinon ils restent, orphelins, sous le nom « deleted:serviceAccount:… »).
        politique = gcloud("projects", "get-iam-policy", self.p)
        for b in politique.get("bindings", []):
            if f"serviceAccount:{email}" in b.get("members", []):
                gcloud("projects", "remove-iam-policy-binding", self.p, "--condition=None", f"--role={b['role']}",
                       f"--member=serviceAccount:{email}", json_out=False)
        gcloud("iam", "service-accounts", "delete", email, f"--project={self.p}", "--quiet", json_out=False)

    def images(self):
        """Dépôts Artifact Registry des images Cloud Run (le dépôt entier, avec toutes ses images)."""
        for d in gcloud("artifacts", "repositories", "list", f"--location={self.r}", f"--project={self.p}"):
            nom = d["name"].split("/")[-1]
            self.ajouter("images", nom, lambda nom=nom: gcloud(
                "artifacts", "repositories", "delete", nom, f"--location={self.r}", f"--project={self.p}", "--quiet", json_out=False))

    def armor(self):
        """Filtres (templates) Model Armor, dans la localisation --location."""
        # Model Armor n'a que des points d'accès régionaux : gcloud vise modelarmor.<loc>.rep.googleapis.com.
        # (config.sh le fait déjà ; setdefault couvre le cas où la configuration n'a pas été chargée).
        os.environ.setdefault("CLOUDSDK_API_ENDPOINT_OVERRIDES_MODELARMOR", f"https://modelarmor.{self.loc}.rep.googleapis.com/")
        for t in gcloud("model-armor", "templates", "list", f"--location={self.loc}", f"--project={self.p}"):
            nom = t["name"].split("/")[-1]
            self.ajouter("armor", nom, lambda nom=nom: gcloud(
                "model-armor", "templates", "delete", nom, f"--location={self.loc}", f"--project={self.p}", "--quiet", json_out=False))


# Ordre de suppression : d'abord ce qui référence les autres (l'app pointe vers les agents, le registre vers
# Cloud Run), puis les agents, puis ce qu'ils utilisent (comptes, images, filtres).
ORDRE = ["app", "registry", "cloudrun", "runtime", "dialogflow", "comptes", "images", "armor"]   # ordre de suppression


def main():
    """Inventaire, affichage, puis (avec --supprimer et après confirmation) suppression dans l'ordre ORDRE."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projet", default=os.getenv("PROJET_AGENTS"))
    p.add_argument("--region", default=os.getenv("REGION", "europe-west1"))
    p.add_argument("--location", default=os.getenv("GE_LOCATION", "eu"), help="localisation Model Armor et app (eu, us, global)")
    p.add_argument("--types", default=",".join(t for t in ORDRE if t != "app"))
    p.add_argument("--agent", help="seulement cet agent (sa clé, ex. meteo) ; les éléments communs sont alors ignorés")
    p.add_argument("--supprimer", action="store_true", help="supprimer (sinon : inventaire seulement)")
    p.add_argument("--avec-terraform", action="store_true", help="inclure ce que Terraform a créé")
    p.add_argument("--oui", action="store_true", help="ne pas demander de confirmation (scripts)")
    a = p.parse_args()
    if not a.projet:
        sys.exit("Projet inconnu : « source scripts/config.sh config/<fichier>.env » d'abord, ou --projet.")
    types = [t for t in ORDRE if t in a.types.split(",")]
    if a.agent:   # images et filtres sont partagés par tous les agents : jamais supprimés pour UN agent
        types = [t for t in types if t not in ("images", "armor", "dialogflow")]

    inv = Inventaire(a)
    print(f"== Inventaire : projet {a.projet}, région {a.region}, localisation {a.location}"
          + (f", agent {a.agent}" if a.agent else "") + f"\n   types : {', '.join(types)}")
    for t in types:
        try:
            getattr(inv, t)()
        except Exception as e:   # un type illisible (API absente, droit manquant) n'empêche pas les autres
            print(f"  ({t} : illisible, ignoré : {e})")

    if not inv.elements:
        print("\nRien à nettoyer.")
        return
    # e[2] = créé par Terraform : retenu seulement avec --avec-terraform.
    retenus = [e for e in inv.elements if a.avec_terraform or not e[2]]
    print()
    for type_, nom, tf, _ in inv.elements:
        etat = "à supprimer" if (a.avec_terraform or not tf) else "ignoré"
        print(f"  {type_:<11} {nom:<60} {'[terraform] ' if tf else ''}{etat if a.supprimer else ''}")
    ignores = len(inv.elements) - len(retenus)
    if ignores:
        print(f"\n  {ignores} élément(s) [terraform] ignoré(s) : `terraform destroy` dans 01-bis / 02-bis / 04-bis, "
              "ou --avec-terraform si l'état Terraform est perdu.")
    if not a.supprimer:
        print(f"\nInventaire seulement : {len(retenus)} élément(s) supprimable(s). Pour supprimer : --supprimer")
        return
    if not retenus:
        return
    # Garde-fou : taper l'ID du projet (et pas « oui ») oblige à vérifier qu'on est dans le bon projet.
    if not a.oui:
        reponse = input(f"\nSupprimer ces {len(retenus)} élément(s) ? Tapez l'ID du projet ({a.projet}) pour confirmer : ")
        if reponse.strip() != a.projet:
            sys.exit("Annulé : rien n'a été supprimé.")
    # Une suppression qui échoue n'arrête pas les autres : on compte, et on invite à relancer.
    erreurs = 0
    for type_, nom, _, supprimer in retenus:
        try:
            supprimer()
            print(f"  supprimé   {type_:<11} {nom}")
        except Exception as e:
            erreurs += 1
            print(f"  ÉCHEC      {type_:<11} {nom} : {e}")
    print(f"\nTerminé : {len(retenus) - erreurs} supprimé(s), {erreurs} échec(s)."
          + (" Relancez la commande pour réessayer les échecs." if erreurs else "")
          + ("\nAgent Runtime : la suppression se termine en arrière-plan (1 à 2 minutes)." if any(e[0] == "runtime" for e in retenus) else ""))
    if a.avec_terraform and any(e[2] for e in retenus):
        print("Ressources Terraform supprimées hors Terraform : dans le dossier concerné, `terraform plan` les montrera à "
              "recréer. Pour qu'il les oublie : `terraform state list`, puis `terraform state rm '<adresse>'`.")


if __name__ == "__main__":
    main()
