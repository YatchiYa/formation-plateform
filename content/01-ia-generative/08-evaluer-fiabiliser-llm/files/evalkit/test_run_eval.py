from run_eval import main, charger, evaluer_cas
from systeme import repondre
assert main(["golden/demo.jsonl", "--seuil", "0.6", "--sortie", "/dev/null"], repondre=repondre) == 0
assert main(["golden/demo.jsonl", "--seuil", "0.9", "--sortie", "/dev/null"], repondre=repondre) == 1
juge = lambda prompt: "Correct.\nNOTE: 5"
r = evaluer_cas(charger("golden/demo.jsonl")[0], repondre, juge)
assert r["ok"] and r["note_juge"] == 5
boom = lambda q: 1 / 0
assert evaluer_cas(charger("golden/demo.jsonl")[0], boom)["ok"] is False

def juge_ko(prompt): raise TimeoutError("quota")
assert evaluer_cas(charger("golden/demo.jsonl")[0], repondre, juge_ko)["ok"] is False
print("tests OK")
assert main(["golden/demo.jsonl", "--seuil", "0.5", "--seuil-categorie", "frequent=1.0", "--sortie", "/dev/null"], repondre=repondre) == 1
assert main(["golden/demo.jsonl", "--seuil", "0.5", "--seuil-categorie", "piege=1.0", "--sortie", "/dev/null"], repondre=repondre) == 1
assert main(["golden/demo.jsonl", "--seuil", "0.5", "--seuil-categorie", "sans-reponse=1.0", "--sortie", "/dev/null"], repondre=repondre) == 0
print("tests seuils OK")
