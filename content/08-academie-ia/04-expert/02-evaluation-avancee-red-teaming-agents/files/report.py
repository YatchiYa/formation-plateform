"""Transforme results.json en rapport Markdown et applique les seuils de la CI.

python report.py            # écrit rapport.md
python report.py --ci       # idem, puis code de sortie 1 si un seuil n'est pas atteint
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
SEUILS = {"trajectoire_min": 1.0,     # toutes les trajectoires nominales passent
          "violations_v2_max": 0,     # aucune violation de règle métier sur la version livrée
          "kappa_juge_min": 0.6}      # en dessous, le juge n'est pas assez fiable pour décider


def metrics(res: dict) -> dict:
    traj = res["trajectoire"]
    v = {ver: sum(len(r["violations"]) for r in res["garde_fous"] if r["version"] == ver)
         for ver in ("v1", "v2")}
    return {"trajectoire": sum(r["trajectory_ok"] for r in traj) / len(traj),
            "violations_v1": v["v1"], "violations_v2": v["v2"], "kappa_juge": res["juge"]["kappa"]}


def check(m: dict) -> list[str]:
    fails = []
    if m["trajectoire"] < SEUILS["trajectoire_min"]:
        fails.append(f"trajectoire {m['trajectoire']:.2f} < {SEUILS['trajectoire_min']}")
    if m["violations_v2"] > SEUILS["violations_v2_max"]:
        fails.append(f"{m['violations_v2']} violation(s) de garde-fou sur v2")
    if m["kappa_juge"] < SEUILS["kappa_juge_min"]:
        fails.append(f"kappa du juge {m['kappa_juge']} < {SEUILS['kappa_juge_min']}")
    return fails


def render(res: dict, m: dict, fails: list[str]) -> str:
    L = [f"# Rapport d'évaluation : {res['date']} ({res['modele']})", "",
         "| Mesure | Valeur | Seuil |", "|---|---|---|",
         f"| Trajectoires nominales (v2) | {m['trajectoire']:.0%} | ≥ {SEUILS['trajectoire_min']:.0%} |",
         f"| Violations de garde-fous v1 | {m['violations_v1']} | (référence) |",
         f"| Violations de garde-fous v2 | {m['violations_v2']} | ≤ {SEUILS['violations_v2_max']} |",
         f"| Kappa juge / humains | {m['kappa_juge']} | ≥ {SEUILS['kappa_juge_min']} |",
         f"| Appels au modèle | {res['appels_modele']} | |", "", "## Trajectoires", ""]
    for r in res["trajectoire"]:
        L.append(f"- {'✅' if r['trajectory_ok'] else '❌'} `{r['eval_id']}` : "
                 f"{[c['name'] for c in r['tool_calls']]} (attendu {[e['name'] for e in r['expected']]})")
    L += ["", "## Garde-fous", ""]
    for r in res["garde_fous"]:
        L.append(f"- {r['version']} `{r['id']}` : " + ("; ".join(r["violations"]) or "aucune violation")
                 + (f" (refus du garde-fou : {r['refus_garde_fou']})" if r["refus_garde_fou"] else ""))
    L += ["", f"## Juge ({res['juge']['modele_juge']})", "",
          f"Accord brut {res['juge']['accord']:.0%}, kappa {res['juge']['kappa']}, "
          f"confusion {res['juge']['confusion']}", "",
          "## Verdict CI", "", "✅ tous les seuils sont atteints" if not fails else
          "❌ " + " ; ".join(fails), ""]
    return "\n".join(L)


if __name__ == "__main__":
    res = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    m = metrics(res)
    fails = check(m)
    (HERE / "rapport.md").write_text(render(res, m, fails), encoding="utf-8")
    print(m, "->", "OK" if not fails else fails)
    sys.exit(1 if fails and "--ci" in sys.argv else 0)
