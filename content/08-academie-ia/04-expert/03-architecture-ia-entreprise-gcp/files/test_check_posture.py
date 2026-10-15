from check_posture import EXPECTED_APIS, evaluate, mask

N = "123456789"


def levels(results):
    return {name: level for level, name, _ in results}


def test_projet_propre():
    policy = {
        "bindings": [
            {"role": "roles/owner", "members": ["group:admins@exemple.fr"]},
            {"role": "roles/aiplatform.user", "members": ["serviceAccount:app@p.iam.gserviceaccount.com"]},
        ],
        "auditConfigs": [{"service": "aiplatform.googleapis.com",
                          "auditLogConfigs": [{"logType": "DATA_READ"}, {"logType": "DATA_WRITE"}]}],
    }
    r = evaluate(N, set(EXPECTED_APIS), policy, {"app@p.iam.gserviceaccount.com": 0})
    assert all(level == "OK" for level, _, _ in r), r


def test_projet_a_risque():
    default_sa = f"serviceAccount:{N}-compute@developer.gserviceaccount.com"
    policy = {"bindings": [
        {"role": "roles/editor", "members": [default_sa, "serviceAccount:ci@p.iam.gserviceaccount.com"]},
        {"role": "roles/run.invoker", "members": ["allUsers"]},
    ]}
    r = levels(evaluate(N, {"run.googleapis.com"}, policy, {"ci@p.iam.gserviceaccount.com": 2}))
    assert r["Accès public (allUsers)"] == "FAIL"
    assert r["Compte Compute par défaut"] == "FAIL"
    assert r["Comptes de service owner/editor"] == "WARN"
    assert r["Clés de comptes de service"] == "WARN"
    assert r["API attendues"] == "WARN"
    assert r["Audit accès aux données Vertex AI"] == "WARN"


def test_audit_allservices_compte():
    policy = {"bindings": [], "auditConfigs": [{"service": "allServices", "auditLogConfigs": [
        {"logType": "DATA_READ"}, {"logType": "DATA_WRITE"}]}]}
    assert levels(evaluate(N, set(EXPECTED_APIS), policy, {}))["Audit accès aux données Vertex AI"] == "OK"


def test_mask():
    assert mask("user:alice@exemple.fr") == "user:al***@exemple.fr"
    assert mask("allUsers") == "allUsers"
