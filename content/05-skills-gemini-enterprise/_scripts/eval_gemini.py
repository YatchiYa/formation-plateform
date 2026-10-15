#!/usr/bin/env python3
"""Evaluate the skills with Gemini on Vertex AI.

  routing  : Gemini sees every skill's name+description (as Gemini Enterprise does for automatic selection)
             and must pick the right skill for each prompt in evals/prompts.json.
  execution: Gemini runs one prompt per skill with the SKILL.md loaded; a judge model grades the answer.

  PROJECT=main-project-511608 python3 scripts/eval_gemini.py routing|execution [--only name1,name2]
Needs `gcloud auth print-access-token` to work. Results go to evals/results/.
"""
import json, os, re, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "evals" / "results"
PROJECT = os.environ.get("PROJECT", "main-project-511608")
LOCATION = os.environ.get("LOCATION", "europe-west4")
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
JUDGE = os.environ.get("JUDGE", "gemini-2.5-pro")
_token = {"value": None, "at": 0}


def token():  # access tokens expire after 1 h: refresh every 30 min
    if time.time() - _token["at"] > 1800:
        _token.update(value=subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip(),
                      at=time.time())
    return _token["value"]


def gemini(model, user, system=None, json_out=False, temperature=0.2):
    url = (f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}"
           f"/publishers/google/models/{model}:generateContent")
    body = {"contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 16384}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if json_out:
        body["generationConfig"]["responseMimeType"] = "application/json"
    for attempt in range(9):
        req = urllib.request.Request(url, json.dumps(body).encode(), {
            "Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.load(r)
            text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
            out = json.loads(text, strict=False) if json_out else text
            if json_out and not isinstance(out, dict):
                raise ValueError("JSON is not an object")
            return out
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, ValueError, TimeoutError) as e:  # KeyError: empty candidate
            if attempt == 8:
                return {"error": str(e)} if json_out else f"ERROR: {e}"
            time.sleep(min(2 ** attempt * 3, 120))  # 429 / transient


def load_skills():
    skills = {}
    for p in sorted((ROOT / "skills").glob("*/*/SKILL.md")):
        text = p.read_text(encoding="utf-8")
        meta = yaml.safe_load(text.split("---")[1])
        skills[meta["name"]] = {"description": meta["description"], "text": text, "domain": p.parent.parent.name}
    return skills


def routing(skills, prompts):
    menu = "\n".join(f"- {n}: {s['description']}" for n, s in skills.items())
    system = ("You are the skill selector of an enterprise assistant. Installed skills (name: description):\n"
              f"{menu}\n\nFor the user's request, return JSON {{\"skill\": \"<exact skill name>\"}} for the single "
              "best skill, or {\"skill\": \"none\"} if no skill fits.")

    def one(p):
        got = gemini(MODEL, p["prompt"], system, json_out=True, temperature=0).get("skill", "error")
        return {**p, "got": got, "ok": got == p["skill"]}

    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(one, prompts))
    ok = sum(r["ok"] for r in res)
    print(f"routing top-1: {ok}/{len(res)} = {ok / len(res):.1%} ({MODEL})")
    for r in res:
        if not r["ok"]:
            print(f"  MISS [{r['lang']}] expected {r['skill']:32} got {r['got']:32} | {r['prompt'][:80]!r}")
    return res


JUDGE_PROMPT = """You grade an AI assistant answer produced while following a SKILL (instructions below).
The test environment had NO connected data sources (no Gmail/Drive/Jira/Databricks...), so a correct answer
must not pretend it searched them; it should say a source is unavailable and work from what the user gave,
ask for missing required inputs, or clearly mark assumptions/placeholders.

A short grouped question is CORRECT (behavior "asked_needed") only when the prompt lacks data the skill cannot do
without; then grade format/method on whether the question is precise and shows what will be delivered. Asking for
optional inputs, or announcing a search without results, is "stalled".

Return JSON: {"behavior": "completed"|"asked_needed"|"stalled", "format": 1-5 (follows the skill's Output format, or
for asked_needed: the question is precise and previews the deliverable), "method": 1-5 (applies the skill's workflow /
expertise, not generic), "grounded": true|false (false if it invents specific facts presented as real: numbers,
policies, names, prices, sources, or claims to have searched sources), "usefulness": 1-5 (a Company teammate
could use this as-is or with light edits), "issues": ["short issue", ...]}

=== SKILL ===
{skill}

=== USER PROMPT ===
{prompt}

=== ANSWER ===
{answer}"""


def execution(skills, prompts):
    first = {}
    for p in prompts:  # one prompt per skill, alternating languages for coverage
        if p["skill"] not in first and (p["lang"] == ("fr" if len(first) % 2 else "en")):
            first[p["skill"]] = p
    for p in prompts:
        first.setdefault(p["skill"], p)
    cases = [p for n, p in first.items() if n in skills]

    def one(p):
        skill = skills[p["skill"]]["text"]
        system = ("You are Gemini Enterprise assistant for Company. The following skill is active; follow it.\n"
                  "No data connectors are available in this session.\n\n" + skill)
        answer = gemini(MODEL, p["prompt"], system)
        grade = gemini(JUDGE, JUDGE_PROMPT.replace("{skill}", skill).replace("{prompt}", p["prompt"])
                       .replace("{answer}", answer), json_out=True, temperature=0)
        return {**p, "answer": answer, "grade": grade}

    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(one, cases))
    graded = [r for r in res if "format" in r["grade"]]
    from collections import Counter
    print("behavior:", dict(Counter(r["grade"].get("behavior") for r in graded)))
    avg = lambda k: sum(r["grade"][k] for r in graded) / max(len(graded), 1)
    print(f"execution: {len(graded)}/{len(res)} graded | format {avg('format'):.2f} method {avg('method'):.2f} "
          f"usefulness {avg('usefulness'):.2f} | grounded {sum(r['grade']['grounded'] for r in graded)}/{len(graded)}")
    for r in sorted(graded, key=lambda r: r["grade"]["format"] + r["grade"]["method"] + r["grade"]["usefulness"]):
        g = r["grade"]
        if min(g["format"], g["method"], g["usefulness"]) <= 3 or not g["grounded"]:
            print(f"  LOW {r['skill']:32} f{g['format']} m{g['method']} u{g['usefulness']} "
                  f"grounded={g['grounded']} | {'; '.join(g.get('issues', []))[:200]}")
    return res


if __name__ == "__main__":
    mode = sys.argv[1]
    skills = load_skills()
    prompts = json.loads((ROOT / "evals" / "prompts.json").read_text(encoding="utf-8"))
    if "--only" in sys.argv:
        keep = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        prompts = [p for p in prompts if p["skill"] in keep]
    OUT.mkdir(parents=True, exist_ok=True)
    res = routing(skills, prompts) if mode == "routing" else execution(skills, prompts)
    (OUT / f"{mode}-{MODEL}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
