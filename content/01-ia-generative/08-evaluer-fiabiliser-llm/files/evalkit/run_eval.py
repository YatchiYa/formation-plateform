"""Mini-harnais d'évaluation RAG (stdlib). Usage : python run_eval.py golden/rh.jsonl --seuil 0.85"""
import argparse, json, re, sys, time
from pathlib import Path

REFUS = ("je ne sais pas", "je ne trouve pas", "je ne peux pas", "hors de mon périmètre")
CHECKS = {  # contrôles par code : gratuits et déterministes
    "contient": lambda s, c: all(m.lower() in s["reponse"].lower() for m in c.get("doit_contenir", [])),
    "interdit": lambda s, c: not any(m.lower() in s["reponse"].lower() for m in c.get("interdit", [])),
    "citation": lambda s, c: set(c.get("sources", [])) <= set(s.get("sources", [])),
    "refus":    lambda s, c: any(m in s["reponse"].lower() for m in REFUS),
}

def rappel(sortie, cas):  # métrique de recherche ; None si aucun document attendu
    attendus = set(cas.get("sources", []))
    return len(attendus & set(sortie.get("sources", []))) / len(attendus) if attendus else None

GRILLE = """Tu es un évaluateur strict.
Question : {question}
Réponse de référence : {attendu}
Critère : {critere}
<reponse>{reponse}</reponse>
5 = critère entièrement respecté ; 3 = partiellement ; 1 = pas du tout ou faux.
Justifie en deux phrases maximum puis termine par : NOTE: <1-5>"""

def juger(juge, cas, sortie):
    texte = juge(GRILLE.format(question=cas["question"], attendu=cas.get("attendu", ""),
                               critere=cas["critere"], reponse=sortie["reponse"]))
    m = re.search(r"NOTE:\s*([1-5])", texte)
    return int(m.group(1)) if m else None  # None = juge illisible -> échec

def evaluer_cas(cas, repondre, juge=None):
    t0, erreur, note = time.perf_counter(), None, None
    try:
        sortie = repondre(cas["question"])
    except Exception as e:  # une exception = un échec noté, pas un crash du harnais
        sortie, erreur = {"reponse": "", "sources": []}, repr(e)
    latence = time.perf_counter() - t0
    verdicts = {n: CHECKS[n](sortie, cas) for n in cas.get("checks", [])}
    if juge and cas.get("critere"):
        try:
            note = juger(juge, cas, sortie)
            verdicts["juge"] = note is not None and note >= 4
        except Exception as e:  # juge indisponible : le cas ne peut pas être certifié
            erreur = erreur or f"juge: {e!r}"
    return {"id": cas["id"], "categorie": cas.get("categorie", "?"),
            "ok": erreur is None and all(verdicts.values()), "verdicts": verdicts,
            "note_juge": note, "rappel": rappel(sortie, cas), "latence_s": round(latence, 3),
            "erreur": erreur, "reponse": sortie["reponse"][:500]}

def charger(chemin):
    return [json.loads(l) for l in Path(chemin).read_text(encoding="utf-8").splitlines() if l.strip()]

def synthese(res):
    n, rap, cats = len(res), [r["rappel"] for r in res if r["rappel"] is not None], {}
    for r in res:
        cats.setdefault(r["categorie"], []).append(r["ok"])
    lat = sorted(r["latence_s"] for r in res)
    return {"n": n, "taux_reussite": round(sum(r["ok"] for r in res) / n, 3),
            "rappel_moyen": round(sum(rap) / len(rap), 3) if rap else None,
            "latence_p95_s": lat[min(n - 1, int(0.95 * n))],
            "par_categorie": {c: round(sum(v) / len(v), 3) for c, v in cats.items()},
            "echecs": [r["id"] for r in res if not r["ok"]]}

def main(argv=None, repondre=None, juge=None):
    p = argparse.ArgumentParser()
    p.add_argument("golden")
    p.add_argument("--seuil", type=float, default=0.85)
    p.add_argument("--sortie", default="rapport.json")
    p.add_argument("--seuil-categorie", action="append", default=[], help="ex. piege=1.0, répétable")
    a = p.parse_args(argv)
    res = [evaluer_cas(c, repondre, juge) for c in charger(a.golden)]
    s = synthese(res)
    Path(a.sortie).write_text(json.dumps({"synthese": s, "details": res}, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(json.dumps(s, ensure_ascii=False))
    code = 0 if s["taux_reussite"] >= a.seuil else 1
    if code:
        print(f"ÉCHEC : {s['taux_reussite']:.1%} < seuil {a.seuil:.0%}", file=sys.stderr)
    for regle in a.seuil_categorie:  # une catégorie absente échoue aussi
        cat, val = regle.split("=")
        taux = s["par_categorie"].get(cat)
        if taux is None or taux < float(val):
            print(f"ÉCHEC {cat} : {taux} < {val}", file=sys.stderr)
            code = 1
    return code

if __name__ == "__main__":
    from systeme import repondre  # votre assistant RAG
    from juges import juge        # None si la variable JUGE n'est pas définie
    sys.exit(main(repondre=repondre, juge=juge))
