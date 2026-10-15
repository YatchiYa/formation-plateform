"""Tests sans clé ni réseau : format JSONL, découpage, score, dry-run du réglage."""
import json

import pytest

from common import LABELS, from_example, parse_label, to_example
from distill import stratified_split
from evaluate import build_contents, pick_shots, run, score
from launch_tuning import build_plan, sdk_objects
from validate_jsonl import check_example, main as validate_main


def test_example_roundtrip_is_valid():
    ex = to_example("Ma facture est en double", "facturation")
    assert check_example(ex) == []
    assert from_example(ex) == ("Ma facture est en double", "facturation")


@pytest.mark.parametrize("bad, msg", [
    ({"contents": []}, "contents manquant"),
    ({"contents": [{"role": "user", "parts": [{"text": "x"}]}]}, "dernier message"),
    ({"contents": [{"role": "assistant", "parts": [{"text": "x"}]}]}, "role"),
    ({"contents": [{"role": "user", "parts": [{"text": "x"}]}, {"role": "model", "parts": [{"text": "autre"}]}]}, "hors étiquettes"),
    ({"messages": [], "contents": [{"role": "user", "parts": [{"text": "x"}]}, {"role": "model", "parts": [{"text": "facturation"}]}]}, "champs inconnus"),
    ({"contents": [{"role": "user", "parts": [{"text": " "}]}, {"role": "model", "parts": [{"text": "facturation"}]}]}, "part vide"),
])
def test_check_example_catches_errors(bad, msg):
    assert any(msg in e for e in check_example(bad))


def test_validate_detects_leak_and_bad_json(tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    line = json.dumps(to_example("ticket commun", "bug_technique"))
    a.write_text(line + "\n")
    b.write_text(line + "\n{pas du json\n")
    assert validate_main([str(a)]) == 0
    assert validate_main([str(a), str(b)]) == 1


def test_parse_label():
    assert parse_label(" Facturation.\n") == "facturation"
    assert parse_label("`bug technique`") == "bug_technique"
    assert parse_label("je ne sais pas") is None


def test_split_is_stratified_and_disjoint():
    rows = [{"ticket": f"{l} {i}", "label": l} for l in LABELS for i in range(20)]
    train, val, test = stratified_split(rows)
    assert (len(train), len(val), len(test)) == (70, 15, 15)
    for part, n in ((train, 14), (val, 3), (test, 3)):
        assert all(sum(r["label"] == l for r in part) == n for l in LABELS)
    ids = [r["ticket"] for r in train + val + test]
    assert len(ids) == len(set(ids)) == 100


def test_few_shot_uses_tuning_format():
    train = [(f"t{i}", LABELS[i % 5]) for i in range(20)]
    shots = pick_shots(train)
    assert len(shots) == 10
    c = build_contents("nouveau", shots)
    assert [m["role"] for m in c[:2]] == ["user", "model"] and c[-1]["parts"][0]["text"] == "nouveau"


def test_run_with_fake_model():
    test = [("a", "facturation"), ("b", "resiliation"), ("c", "bug_technique")]
    answers = iter(["facturation", "facturation", "n'importe quoi"])
    r = run(lambda contents: (next(answers), 10), test, [], "zero-shot")
    assert r["exactitude"] == pytest.approx(1 / 3, abs=1e-3)
    assert r["hors_etiquette"] == pytest.approx(1 / 3, abs=1e-3)
    assert r["tokens_entree_moyens"] == 10 and len(r["erreurs"]) == 2
    assert score(["facturation"], ["facturation"])["rappel_par_etiquette"]["facturation"] == 1.0


def test_dry_run_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "projet-test")
    t, v = tmp_path / "t.jsonl", tmp_path / "v.jsonl"
    t.write_text("".join(json.dumps(to_example(f"ticket {i}", LABELS[i % 5])) + "\n" for i in range(10)))
    v.write_text(json.dumps(to_example("autre", "facturation")) + "\n")
    plan = build_plan(str(t), str(v), epochs=4, adapter_size=4, lr_multiplier=1.0)
    assert plan["training_dataset"]["gcs_uri"] == "gs://lab-adapter-modele-projet-test/train.jsonl"
    assert plan["config"]["labels"] == {"formation-lab": "adapter-modele"}
    assert plan["estimation"]["tokens_factures_estimes"] == plan["estimation"]["tokens_train"] * 4
    dataset, config = sdk_objects(plan)   # paramètres acceptés par le SDK installé
    assert config.epoch_count == 4 and config.adapter_size.value == "ADAPTER_SIZE_FOUR"


def test_dry_run_refuses_invalid_dataset(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"contents": []}\n')
    with pytest.raises(SystemExit):
        build_plan(str(bad), str(bad))
