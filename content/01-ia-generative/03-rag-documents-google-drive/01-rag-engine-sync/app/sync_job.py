"""Point d'entrée du job Cloud Run « <prefix>-sync » : une passe de synchro, rapport en JSON dans les journaux.

RAG Engine n'accepte qu'une opération à la fois par corpus (vérifié). Si une autre passe tourne, on attend et on
recommence la passe ENTIÈRE (listing frais) : la dernière passe lancée voit donc toujours le dernier état.
"""

import json
import sys
import time

import kit

if __name__ == "__main__":
    for attempt in range(60):  # 60 × 15 s = 15 min d'attente au plus
        report = kit.run_sync()
        print(json.dumps(report, ensure_ascii=False))
        if report["statut"] != "occupe":
            break
        time.sleep(15)
    sys.exit(0 if report["statut"] in ("ok", "avertissement") else 1)
