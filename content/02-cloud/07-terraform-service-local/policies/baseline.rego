# Politiques du service (évaluées par Conftest sur le plan JSON de chaque PR).
# Ressource simulée : terraform_data dont input.kind = "google_storage_bucket".
package main

import rego.v1

buckets contains rc if {
	some rc in input.resource_changes
	rc.type == "terraform_data"
	rc.change.after.input.kind == "google_storage_bucket"
	some action in rc.change.actions
	action in {"create", "update"}
}

# 1. Résidence des données : UE uniquement.
deny contains msg if {
	some rc in buckets
	loc := upper(rc.change.after.input.location)
	not startswith(loc, "EU")
	not startswith(loc, "EUROPE-")
	msg := sprintf("%s : localisation '%s' interdite (UE uniquement)", [rc.address, rc.change.after.input.location])
}

# 2. Labels obligatoires (responsabilité, refacturation).
required_labels := {"owner", "env", "cost_center"}

deny contains msg if {
	some rc in buckets
	some label in required_labels
	not rc.change.after.input.labels[label]
	msg := sprintf("%s : label obligatoire '%s' manquant", [rc.address, label])
}

# 3. Pas d'accès public.
deny contains msg if {
	some rc in buckets
	rc.change.after.input.public == true
	msg := sprintf("%s : bucket public interdit", [rc.address])
}
