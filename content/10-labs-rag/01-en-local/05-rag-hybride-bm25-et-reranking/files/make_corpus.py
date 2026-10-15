"""Génère le corpus fictif (80 documents techniques) et les 25 questions de référence.

Produit fictif : « Hélio », une plateforme d'intégration de données éditée par une entreprise imaginaire.
Le corpus est construit pour reproduire les deux pièges classiques d'un RAG documentaire :
  - des documents presque identiques qui ne diffèrent que par un identifiant (codes d'erreur, paramètres) ;
  - des procédures rédigées avec un vocabulaire différent de celui des questions (synonymes).

Usage : python make_corpus.py   ->  écrit corpus.jsonl et questions.json à côté du script.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

MODULES = [
    ("export", "l'export des rapports"),
    ("import", "l'import des fichiers CSV"),
    ("sync", "la synchronisation avec l'ERP"),
    ("archive", "l'archivage nocturne"),
]

# (suffixe, symptôme, cause, résolution) ; {m} = clé du module
SYMPTOMS = [
    ("1", "le délai d'attente est dépassé", "le serveur distant ne répond pas avant la limite configurée",
     "augmentez {m}.timeout_s ou réduisez {m}.batch_size"),
    ("2", "l'authentification est refusée", "le jeton de service a expiré ou a été révoqué",
     "régénérez le jeton dans Console > Sécurité > Jetons de service"),
    ("3", "le quota journalier est atteint", "le nombre d'opérations autorisées par jour est épuisé",
     "attendez minuit UTC ou demandez une hausse de quota à l'administrateur"),
    ("4", "le format des données est invalide", "une colonne ne respecte pas le schéma déclaré",
     "corrigez le fichier source puis relancez avec l'option --strict désactivée pour lister les lignes fautives"),
    ("5", "l'espace disque est insuffisant", "le volume de travail temporaire est plein",
     "videz /var/helio/tmp ou augmentez {m}.tmp_quota_go"),
]

PARAMS = [
    ("timeout_s", "fixe le délai maximal, en secondes, accordé à chaque appel distant de {label}", [30, 60, 120, 300]),
    ("retry_max", "fixe le nombre maximal de nouvelles tentatives de {label} après un échec", [3, 5, 2, 8]),
    ("batch_size", "fixe le nombre d'enregistrements traités par lot pendant {label}", [500, 1000, 200, 5000]),
    ("parallelism", "fixe le nombre de tâches exécutées en parallèle pendant {label}", [4, 2, 8, 1]),
    ("log_level", "fixe le niveau de détail des journaux produits par {label}", ["INFO", "WARN", "DEBUG", "INFO"]),
]

PROCEDURES = [
    ("proc-purger-cache", "Purger le cache des connecteurs",
     "Lorsque les connecteurs renvoient des données périmées, ouvrez Console > Connecteurs, sélectionnez le connecteur puis cliquez sur « Purger le cache ». La commande équivalente est helio connector purge <nom>. La purge invalide les métadonnées mémorisées et force une relecture complète du schéma."),
    ("proc-rotation-jetons", "Rotation des jetons de service",
     "Les jetons de service expirent après 90 jours. Pour en créer un nouveau sans interruption, générez le jeton de remplacement, déployez-le dans les secrets de l'orchestrateur, puis révoquez l'ancien après 24 heures de recouvrement."),
    ("proc-restauration", "Restaurer une sauvegarde",
     "Les sauvegardes sont conservées 30 jours. Exécutez helio backup list pour afficher les points de restauration, puis helio backup restore <id> --target staging. Vérifiez l'environnement de recette avant de promouvoir en production."),
    ("proc-mise-a-jour", "Mettre à niveau Hélio vers une version mineure",
     "Arrêtez les planifications avec helio scheduler pause, appliquez le paquet de mise à niveau, lancez helio migrate puis relancez les planifications. Une mise à niveau mineure ne modifie jamais le format des fichiers de configuration."),
    ("proc-ajout-utilisateur", "Ajouter un utilisateur",
     "Un administrateur invite un collègue depuis Console > Équipe > Inviter. Le rôle par défaut est Lecteur. Les rôles Éditeur et Administrateur doivent être attribués explicitement et sont tracés dans le journal d'audit."),
    ("proc-sso", "Configurer l'authentification unique SAML",
     "Déclarez Hélio comme fournisseur de service dans votre annuaire, importez le fichier de métadonnées XML dans Console > Sécurité > SAML et associez l'attribut email. Conservez un compte administrateur local en secours."),
    ("proc-webhook", "Recevoir des notifications par webhook",
     "Dans Console > Notifications, ajoutez une URL HTTPS. Chaque appel est signé par l'en-tête X-Helio-Signature calculé en HMAC-SHA256 avec le secret partagé. Rejetez les requêtes dont la signature ne correspond pas."),
    ("proc-planification", "Planifier une tâche récurrente",
     "Une planification utilise la syntaxe cron à cinq champs. Exemple : 0 2 * * * lance la tâche chaque jour à 2 h UTC. Les fuseaux horaires locaux ne sont pas pris en charge dans les expressions."),
    ("proc-export-manuel", "Lancer un export manuel",
     "Depuis la page du rapport, choisissez Exporter puis le format (CSV, Parquet ou XLSX). Les exports de plus de 2 millions de lignes sont automatiquement découpés en plusieurs fichiers numérotés."),
    ("proc-masquage", "Masquer les colonnes sensibles",
     "Déclarez une règle de masquage dans Console > Gouvernance : choisissez la colonne et la méthode (hachage, troncature ou remplacement par des étoiles). La règle s'applique à toutes les lectures, y compris les exports."),
    ("proc-quota", "Demander une hausse de quota",
     "Seul un administrateur peut demander une hausse. Ouvrez Console > Abonnement > Quotas, indiquez le module concerné et le volume journalier visé. La hausse prend effet au prochain renouvellement quotidien."),
    ("proc-diagnostic", "Générer un paquet de diagnostic",
     "Exécutez helio support bundle : la commande rassemble les journaux des sept derniers jours, la configuration sans les secrets et l'état des planifications dans une archive à transmettre au support."),
    ("proc-mode-maintenance", "Activer le mode maintenance",
     "Le mode maintenance suspend toutes les planifications et affiche un bandeau aux utilisateurs. Activez-le avec helio maintenance on --message \"texte\" ; les tâches en cours se terminent normalement."),
    ("proc-schema-evolution", "Gérer l'ajout d'une colonne dans une source",
     "Quand une source ajoute une colonne, Hélio la détecte au prochain chargement et la marque « nouvelle ». Validez-la dans l'onglet Schéma pour qu'elle soit propagée vers les destinations."),
    ("proc-suppression-projet", "Supprimer un projet",
     "La suppression d'un projet est différée de 7 jours, pendant lesquels il peut être restauré depuis la corbeille. Passé ce délai, les données et l'historique sont effacés définitivement."),
    ("proc-api-cle", "Créer une clé d'API personnelle",
     "Dans Profil > Clés d'API, cliquez sur Créer. La clé n'est affichée qu'une seule fois. Elle hérite des droits de l'utilisateur et peut être limitée à certains projets."),
    ("proc-reseau", "Autoriser Hélio dans le pare-feu",
     "Ouvrez les flux sortants HTTPS vers les plages d'adresses publiées dans Console > Réseau. Les connecteurs sur site utilisent en plus le port 8443 vers la passerelle."),
    ("proc-passerelle", "Installer la passerelle sur site",
     "La passerelle est un conteneur à exécuter dans votre réseau : docker run helio/gateway avec la variable GATEWAY_TOKEN. Elle relaie les connexions vers les bases internes sans les exposer sur Internet."),
    ("proc-audit", "Consulter le journal d'audit",
     "Le journal d'audit liste chaque connexion, modification de droits et export, avec l'horodatage et l'adresse IP. Il est conservé 400 jours et exportable en CSV par un administrateur."),
    ("proc-alerte", "Créer une alerte sur l'échec d'une tâche",
     "Dans la fiche de la tâche, ajoutez une règle d'alerte « échec » ou « durée supérieure à ». Les alertes peuvent être envoyées par e-mail, webhook ou messagerie d'équipe."),
]

NOTES = [
    ("note-3-2-0", "Note de version 3.2.0", "Nouveau connecteur Parquet en lecture. Le paramètre export.batch_size accepte désormais jusqu'à 10 000 enregistrements."),
    ("note-3-2-1", "Note de version 3.2.1", "Correction d'une fuite mémoire de la passerelle sur site lors de connexions longues. Mise à jour recommandée pour tous les clients utilisant la passerelle."),
    ("note-3-3-0", "Note de version 3.3.0", "Arrivée des règles de masquage par colonne. Le journal d'audit trace désormais les exports."),
    ("note-3-3-2", "Note de version 3.3.2", "Les jetons de service émis avant la 3.3.0 sont invalidés : régénérez-les. Corrige une élévation de privilèges sur le rôle Éditeur."),
    ("note-3-4-0", "Note de version 3.4.0", "La synchronisation avec l'ERP prend en charge la reprise après coupure : un lot interrompu reprend à la dernière ligne validée."),
    ("note-3-4-1", "Note de version 3.4.1", "Le délai par défaut de sync.timeout_s passe de 60 à 120 secondes. L'import CSV détecte automatiquement le séparateur."),
    ("note-3-5-0", "Note de version 3.5.0", "Nouvelle commande helio support bundle. Les planifications peuvent être mises en pause projet par projet."),
    ("note-3-5-1", "Note de version 3.5.1", "Fin de prise en charge de TLS 1.1 pour les webhooks. Les URL de notification doivent accepter TLS 1.2 au minimum."),
    ("inc-2026-01", "Rapport d'incident de janvier 2026", "Pendant 3 heures, l'archivage nocturne a échoué sur la région Europe à cause d'un volume temporaire saturé. Correctif : surveillance du remplissage et purge automatique à 80 %."),
    ("inc-2026-02", "Rapport d'incident de février 2026", "Des exports XLSX volumineux produisaient des fichiers tronqués au-delà d'un million de lignes. Correctif : découpage automatique en plusieurs fichiers."),
    ("inc-2026-03", "Rapport d'incident de mars 2026", "Une rotation de certificat côté fournisseur d'identité a bloqué les connexions SAML pendant 40 minutes. Recommandation : garder un compte administrateur local."),
    ("inc-2026-04", "Rapport d'incident d'avril 2026", "La synchronisation ERP a créé des doublons après une coupure réseau : les lots étaient rejoués depuis le début. Corrigé par la reprise à la dernière ligne validée."),
    ("inc-2026-05", "Rapport d'incident de mai 2026", "Des webhooks ont été envoyés deux fois pendant une mise à niveau. Les destinataires doivent traiter les notifications de façon idempotente grâce à l'en-tête X-Helio-Delivery-Id."),
    ("inc-2026-06", "Rapport d'incident de juin 2026", "Le quota journalier de l'import a été atteint dès 10 h par un script client en boucle. Ajout d'une alerte à 80 % du quota."),
    ("faq-tarifs", "Comment est calculée la facture ?", "La facture mensuelle dépend du nombre d'opérations traitées et du nombre de connecteurs actifs. Les environnements de recette ne sont pas facturés."),
    ("faq-retention", "Combien de temps les journaux sont-ils gardés ?", "Les journaux techniques sont conservés 30 jours, le journal d'audit 400 jours. Une durée plus longue est possible via un export vers votre propre stockage."),
    ("faq-regions", "Où sont hébergées les données ?", "Chaque organisation choisit une région à la création : Europe ou Amérique du Nord. Les données ne quittent pas la région choisie, sauvegardes comprises."),
    ("faq-limites", "Quelles sont les limites d'un fichier importé ?", "Un fichier CSV importé ne doit pas dépasser 5 Go ni 400 colonnes. Au-delà, découpez-le ou utilisez le connecteur Parquet."),
    ("faq-support", "Quels sont les horaires du support ?", "Le support répond du lundi au vendredi de 8 h à 18 h (heure de Paris). Les incidents de gravité 1 sont pris en charge 24 h sur 24 pour l'offre Entreprise."),
    ("faq-sla", "Quel est l'engagement de disponibilité ?", "L'offre Entreprise garantit 99,9 % de disponibilité mensuelle de la console et de l'API. Les maintenances planifiées sont annoncées 7 jours à l'avance."),
]


def build_corpus() -> list[dict]:
    docs = []
    for mi, (m, label) in enumerate(MODULES):
        for suffix, symptom, cause, fix in SYMPTOMS:
            code = f"HEL-{4 + mi}0{suffix}0"  # ex. HEL-4010, HEL-5020…
            docs.append({"id": f"err-{code}", "title": f"Erreur {code}",
                         "text": f"Erreur {code} pendant {label} : {symptom}. Cause : {cause}. Résolution : {fix.format(m=m)}."})
    for mi, (m, label) in enumerate(MODULES):
        for name, desc, defaults in PARAMS:
            docs.append({"id": f"par-{m}.{name}", "title": f"Paramètre {m}.{name}",
                         "text": f"Le paramètre {m}.{name} {desc.format(label=label)}. Valeur par défaut : {defaults[mi]}. Il se règle dans le fichier helio.yaml, section {m}."})
    for pid, title, text in PROCEDURES + NOTES:
        docs.append({"id": pid, "title": title, "text": f"{title}. {text}"})
    return docs


# type : "identifiant" (code ou nom exact), "paraphrase" (synonymes absents du document), "mixte"
QUESTIONS = [
    ("Que signifie l'erreur HEL-6030 et comment la corriger ?", ["err-HEL-6030"], "identifiant"),
    ("J'obtiens HEL-4040, que dois-je faire ?", ["err-HEL-4040"], "identifiant"),
    ("Comment résoudre HEL-7050 ?", ["err-HEL-7050"], "identifiant"),
    ("Quelle est la cause de l'erreur HEL-5020 ?", ["err-HEL-5020"], "identifiant"),
    ("HEL-6010 apparaît chaque nuit, pourquoi ?", ["err-HEL-6010"], "identifiant"),
    ("Quelle est la valeur par défaut de archive.parallelism ?", ["par-archive.parallelism"], "identifiant"),
    ("À quoi sert sync.batch_size ?", ["par-sync.batch_size"], "identifiant"),
    ("Valeur par défaut de import.log_level ?", ["par-import.log_level"], "identifiant"),
    ("Que fait la commande helio support bundle ?", ["proc-diagnostic", "note-3-5-0"], "identifiant"),
    ("À quoi sert l'en-tête X-Helio-Delivery-Id ?", ["inc-2026-05"], "identifiant"),
    ("Comment vider la mémoire temporaire d'une source de données qui renvoie des infos dépassées ?", ["proc-purger-cache"], "paraphrase"),
    ("Mon collègue doit pouvoir se connecter à l'outil, comment lui donner accès ?", ["proc-ajout-utilisateur"], "paraphrase"),
    ("Comment revenir à l'état d'hier après une fausse manipulation ?", ["proc-restauration"], "paraphrase"),
    ("Peut-on cacher les numéros de sécurité sociale dans les tableaux partagés ?", ["proc-masquage"], "paraphrase"),
    ("Comment être prévenu quand un traitement plante ?", ["proc-alerte", "proc-webhook"], "paraphrase"),
    ("Nos bases internes ne sont pas accessibles depuis Internet, comment les relier à l'outil ?", ["proc-passerelle"], "paraphrase"),
    ("Qui a téléchargé des données le mois dernier ?", ["proc-audit"], "paraphrase"),
    ("Mon tableur de plusieurs millions de lignes sortait coupé, c'est réglé ?", ["inc-2026-02", "proc-export-manuel"], "paraphrase"),
    ("Est-ce que nos informations peuvent partir aux États-Unis ?", ["faq-regions"], "paraphrase"),
    ("Le service est-il joignable le week-end en cas de panne grave ?", ["faq-support"], "paraphrase"),
    ("Combien de fois l'archivage nocturne réessaie-t-il après un échec ?", ["par-archive.retry_max"], "mixte"),
    ("Quel délai par défaut pour les appels distants de la synchronisation ERP ?", ["par-sync.timeout_s", "note-3-4-1"], "mixte"),
    ("L'import CSV refuse mon jeton, quel code d'erreur et quelle solution ?", ["err-HEL-5020"], "mixte"),
    ("Pourquoi la synchronisation ERP a-t-elle créé des doublons ?", ["inc-2026-04", "note-3-4-0"], "mixte"),
    ("Quelle taille maximale pour un fichier CSV importé ?", ["faq-limites"], "mixte"),
]


if __name__ == "__main__":
    docs = build_corpus()
    ids = {d["id"] for d in docs}
    assert len(docs) == 80 and len(ids) == 80, len(docs)
    for q, rel, _ in QUESTIONS:
        assert set(rel) <= ids, rel
    with open(HERE / "corpus.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    qs = [{"question": q, "relevant": rel, "type": t} for q, rel, t in QUESTIONS]
    (HERE / "questions.json").write_text(json.dumps(qs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(docs)} documents, {len(qs)} questions")
