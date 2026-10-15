import json
import assistant_commandes as ac


def faux_llm(script):
    reponses = iter(script)
    return lambda messages, tools: next(reponses)


def appel(name, **args):
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": name, "type": "function",
         "function": {"name": name, "arguments": json.dumps(args)}}]}


def dire(texte):
    return {"role": "assistant", "content": texte}


# 1. Parcours nominal : recherche, stock, récapitulatif, confirmation, commande.
bot = ac.Assistant("c1", llm=faux_llm([
    appel("chercher_produit", texte="café"),
    appel("consulter_stock", ref="P1"),
    dire("3 × Café en grains 1 kg = 54 €. Je confirme ?"),
    appel("creer_commande", ref="P1", quantite=3, confirme=True),
    dire("Commande créée."),
]))
bot.demander("3 cafés")
bot.demander("oui")
assert ac.STOCK["P1"] == 9 and len(ac.COMMANDES) == 1
assert list(ac.COMMANDES.values())[0]["client"] == "c1"   # client_id imposé par le code

# 2. Sans confirmation, rien n'est créé et le modèle reçoit l'erreur.
bot = ac.Assistant("c2", llm=faux_llm([
    appel("creer_commande", ref="P1", quantite=1, confirme=False), dire("ok")]))
bot.demander("1 café")
assert len(ac.COMMANDES) == 1 and "confirmation" in bot.messages[-2]["content"]

# 3. Quantité excessive et stock insuffisant refusés.
assert "hors limites" in ac.Assistant("c3").run_tool(
    appel("creer_commande", ref="P1", quantite=500, confirme=True)["tool_calls"][0])["content"]
assert "Stock insuffisant" in ac.Assistant("c3").run_tool(
    appel("creer_commande", ref="P2", quantite=1, confirme=True)["tool_calls"][0])["content"]

# 4. Escalade explicite, et escalade automatique quand max_steps est atteint.
bot = ac.Assistant("c4", llm=faux_llm([
    appel("transferer_a_un_humain", motif="réclamation"), dire("Un conseiller arrive.")]))
bot.demander("Mon colis est abîmé")
assert ac.FILE_HUMAINE[-1] == {"client": "c4", "motif": "réclamation"}
bot = ac.Assistant("c5", llm=faux_llm([appel("consulter_stock", ref="P1")] * 20))
assert bot.demander("?", max_steps=3) == ac.ESCALADE
assert ac.FILE_HUMAINE[-1]["client"] == "c5"
print("ok : 4 scénarios")
