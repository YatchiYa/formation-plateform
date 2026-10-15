#!/usr/bin/env python3
"""
Import local project repos into content/ as themes, courses and articles.

Re-runnable: each target folder is wiped and copied again, so `python3 scripts/import-repos.py`
after editing a source repo refreshes the site. Secrets and build junk are never copied
(.env, tfstate, tfvars, keys, venvs...); the script stops if anything that looks like a secret
slipped through.

Usage: python3 scripts/import-repos.py [--src /home/yarab/Bureau/trash]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

SKIP_DIRS = {"venv", ".venv", "node_modules", ".terraform", ".git", "__pycache__", ".adk", ".ruff_cache",
             ".pytest_cache", ".mypy_cache", "terraform.tfstate.d", "mcptest", "dist", ".idea", ".vscode"}
SAFE_DOTFILES = {".gitignore", ".dockerignore"}
SKIP_FILE = re.compile(r"(^\.|\.tfstate|\.tfvars$|\.pem$|\.key$|\.p12$|credential|client_secret|^token.*\.json$|sa-key|"
                       r"service[-_]account.*\.json$|\.zip$|\.pyc$|\.log$|\.sqlite3?$|\.db$)", re.I)
SECRET = re.compile(r"(AIza[0-9A-Za-z_\-]{35}|ya29\.[0-9A-Za-z_\-]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----\s*\n[A-Za-z0-9+/=]{40,}|"
                    r"ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{40,}|xox[baprs]-[0-9A-Za-z-]{10,}|sk-ant-[0-9A-Za-z_\-]{20,}|"
                    r"sk-[A-Za-z0-9]{40,}|GOCSPX-[0-9A-Za-z_\-]{20,}|\"private_key\":\s*\"-----)")

AUTHOR = ["Youcef"]

# ------------------------------------------------------------ anonymize ---
# The site is public: client names and identifiers are replaced everywhere (text, file names,
# inside .docx/.pptx), consistently, so links between files keep working. Order matters.
# (pattern, replacement) pairs applied everywhere when anonymizing. Client terms are defined in
# scripts/import-config.local.py; anything listed there is also refused by the final check.
ANONYMIZE: list = []
PLACEHOLDER_NUMBERS = {"123456789012", "111122223333"}
_numbers: dict = {}


def _fake_number(m: "re.Match") -> str:
    n = m.group(2)
    if n in PLACEHOLDER_NUMBERS:
        return m.group(0)
    _numbers.setdefault(n, str(100000000000 + len(_numbers) + 1))
    return m.group(1) + _numbers[n]


def anonymize_text(t: str) -> str:
    for a, b in ANONYMIZE:
        t = re.sub(a, b, t)
    # Real GCP project numbers (service agents, resource names) → stable fake numbers.
    return re.sub(r"(service-|projects/)(\d{10,13})", _fake_number, t)


TEXT_EXT = {".md", ".txt", ".py", ".tf", ".hcl", ".sh", ".yaml", ".yml", ".json", ".toml", ".html", ".csv", ".ts", ".js",
            ".mjs", ".ini", ".cfg", ".rego", ".sql", ".example", ".exemple", ".ipynb", ".svg", ".xml", ".env"}


def anonymize_tree(root: Path):
    import zipfile
    # 1. contents
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in TEXT_EXT or p.name in {"Dockerfile", "Makefile", ".gitignore", ".dockerignore"}:
            t = p.read_text(encoding="utf-8", errors="ignore")
            a = anonymize_text(t)
            if a != t:
                p.write_text(a, encoding="utf-8")
        elif ext in {".docx", ".pptx", ".xlsx"}:
            tmp = p.with_suffix(p.suffix + ".tmp")
            changed = False
            with zipfile.ZipFile(p) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename.endswith((".xml", ".rels")):
                        new = anonymize_text(data.decode("utf-8", errors="ignore")).encode("utf-8")
                        changed |= new != data
                        data = new
                    zout.writestr(item, data)
            tmp.replace(p) if changed else tmp.unlink()
            if changed and ext == ".pptx" and shutil.which("soffice"):
                # Regenerate the PDF export from the anonymized deck.
                subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(p.parent), str(p)],
                               capture_output=True, timeout=180)
    # 2. names (deepest first so parents are renamed last)
    for p in sorted(root.rglob("*"), key=lambda x: -len(x.parts)):
        new = anonymize_text(p.name)
        if new != p.name:
            target = p.with_name(new)
            if target.exists() and p.is_file():
                target.unlink()
            p.rename(target)
    # 3. PDFs can't be rewritten: one that still names the client (no deck to regenerate it from) is dropped.
    for p in root.rglob("*.pdf"):
        forbidden = "|".join(a for a, _ in ANONYMIZE) or r"(?!x)x"
        if re.search(forbidden, p.name) or re.search(forbidden, pdf_text(p)):
            print(f"  - removed {p.relative_to(ROOT)} (PDF naming the client, no editable source)")
            p.unlink()


def pdf_text(p: Path) -> str:
    try:
        from pypdf import PdfReader
        return " ".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    except ImportError:
        # Without pypdf, be conservative: compressed PDF text can't be checked, treat it as dirty.
        return " ".join(a for a, _ in ANONYMIZE)
    except Exception:
        return ""

# ---------------------------------------------------------------- themes ---
THEMES = {
    "04-agents-google-cloud": dict(
        title="Agents IA sur Google Cloud",
        icon="🤖",
        description="Le parcours complet : agents ADK, Agent Runtime, Gemini Enterprise, serveurs MCP et sécurité, tout en Terraform.",
        body_from="README.md",  # the learning-path README at the root of the source folder
    ),
    "04-agents-google-cloud/01-construire-des-agents": dict(
        title="Construire et publier des agents",
        icon="🛠️",
        description="De l'agent ADK sur Cloud Run à Gemini Enterprise, Google Chat et les agents multi-projets.",
    ),
    "04-agents-google-cloud/02-serveurs-mcp": dict(
        title="Serveurs MCP",
        icon="🔌",
        description="Donner des outils aux agents : serveurs MCP privés sur Cloud Run, Agent Registry, Google Sheets et Slides.",
    ),
    "04-agents-google-cloud/03-securite-gemini-enterprise": dict(
        title="Sécuriser Gemini Enterprise",
        icon="🛡️",
        description="Model Armor, socle de sécurité en 6 couches, note de sécurité appliquée et contrôles de conformité.",
    ),
    "05-skills-gemini-enterprise": dict(
        title="Skills Gemini Enterprise",
        icon="🧰",
        description="160 skills prêts à importer dans Gemini Enterprise, classés en 17 métiers. Lisez-les, téléchargez-les, adaptez-les.",
        body_from="README.md",
    ),
}

# --------------------------------------------------------------- projects ---
# src: folder under --src ; dst: folder under content/ ; type: course | article
# Source repos → content/. The real list lives in scripts/import-config.local.py (gitignored),
# because source folder names can name clients. Format:
# dict(src="01-mon-projet", dst="04-theme/01-sous-theme/01-mon-projet", type="course" | "article",
#      level="beginner", duration="2h", tags=[...], description="...", usecases=[...], platforms=[...],
#      modules={"docs": ("Titre du module", 0)}, rebuild=["python3 scripts/build_pdf.py"])
PROJECTS: list = []

SKILL_DOMAINS = {
    "01-productivity": ("Productivité", "⏱️"), "02-communication": ("Communication", "✉️"),
    "03-management-leadership": ("Management & leadership", "🧭"), "04-hr-people": ("RH & talents", "🤝"),
    "05-sales-b2b": ("Vente B2B", "💼"), "06-retail-store-ops": ("Magasins & retail", "🏬"),
    "07-customer-service": ("Service client", "🎧"), "08-marketing-ecommerce": ("Marketing & e-commerce", "📣"),
    "09-product-design": ("Produit & conception", "📐"), "10-data-analytics": ("Data & analytics", "📊"),
    "11-engineering-it": ("Ingénierie & IT", "💻"), "12-project-management": ("Gestion de projet", "🗂️"),
    "13-finance-procurement": ("Finance & achats", "💶"), "14-legal-compliance": ("Juridique & conformité", "⚖️"),
    "15-sustainability": ("Développement durable", "🌱"), "16-knowledge-search": ("Recherche & connaissance", "🔎"),
    "17-ai-adoption": ("Adoption de l'IA", "✨"),
}


# ---------------------------------------------------------------- helpers ---
def yaml_str(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def frontmatter(d: dict) -> str:
    out = ["---"]
    for k, v in d.items():
        if v is None or v == [] or v == "":
            continue
        if k == "references":
            out.append("references:")
            for r in v:
                out.append(f"  - title: {yaml_str(r['title'])}\n    url: {r['url']}")
        elif isinstance(v, list):
            out.append(f"{k}: [{', '.join(yaml_str(x) for x in v)}]")
        elif isinstance(v, (int, float)):
            out.append(f"{k}: {v}")
        else:
            out.append(f"{k}: {yaml_str(str(v))}")
    out.append("---\n")
    return "\n".join(out)


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if SKIP_FILE.search(f) and f not in SAFE_DOTFILES and not f.endswith((".example", ".exemple", ".sample")):
                continue
            s = Path(root) / f
            t = dst / s.relative_to(src)
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, t)
            n += 1
    return n


def references_from(md: str, limit=8):
    """External links of a README, GitHub/docs first, deduplicated."""
    refs, seen = [], set()
    for title, url in re.findall(r"\[([^\]]{3,120})\]\((https?://[^)\s]+)\)", md):
        u = url.rstrip(".,")
        if u in seen or "localhost" in u or "console.cloud.google.com" in u:
            continue
        seen.add(u)
        refs.append({"title": re.sub(r"[`*_]", "", title).strip(), "url": u})
    refs.sort(key=lambda r: (0 if "github.com" in r["url"] else 1 if "/docs" in r["url"] else 2))
    return refs[:limit]


def git_date(path: Path) -> str:
    try:
        return subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(path)], cwd=path.parent,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def file_date(path: Path) -> str:
    from datetime import date
    return date.fromtimestamp(path.stat().st_mtime).isoformat()


def write_index(dir_: Path, meta: dict, body: str = ""):
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / "index.md").write_text(frontmatter(meta) + body, encoding="utf-8")


# ---------------------------------------------------------------- import ---
def import_projects(src_root: Path):
    for p in PROJECTS:
        src, dst = src_root / p["src"], CONTENT / (anonymize_text(p["dst"]) if ANON else p["dst"])
        if not src.exists():
            print(f"  ! missing {src}, skipped")
            continue
        shutil.rmtree(dst, ignore_errors=True)
        n = copy_tree(src, dst)
        if ANON:
            anonymize_tree(dst)
        for cmd in p.get("rebuild", []):
            r = subprocess.run(cmd, shell=True, cwd=dst, capture_output=True, text=True, timeout=300)
            print(f"    rebuild `{cmd}`: {'ok' if r.returncode == 0 else 'FAILED ' + r.stderr[-200:]}")
        readme = dst / "README.md"
        body = strip_frontmatter(readme.read_text(encoding="utf-8")) if readme.exists() else f"# {p['src']}\n"
        # `../README.md` meant the learning-path README, now the index of the agents theme.
        path_index = os.path.relpath(CONTENT / "04-agents-google-cloud" / "index.md", dst)
        body = body.replace("](../README.md", "](" + path_index)
        # Root-level PDF decks are worth reading inline.
        decks = sorted(x.name for x in dst.glob("*.pdf"))
        if decks:
            body += "\n\n## Supports\n\n" + "\n\n".join(f"![{Path(d).stem.replace('-', ' ')}](./{d})" for d in decks) + "\n"
        meta = dict(type=p["type"], description=p["description"], tags=p["tags"], level=p["level"], duration=p["duration"],
                    usecases=p.get("usecases", []), platforms=p.get("platforms", []),
                    date=file_date(src / "README.md") if (src / "README.md").exists() else "", updated=git_date(src),
                    authors=AUTHOR, references=references_from(body))
        # Keep the README name: every relative link in the repos points at README.md files.
        readme.write_text(frontmatter(meta) + body, encoding="utf-8")
        for folder, spec in (p.get("modules") or {}).items():
            mdir = dst / folder
            if spec and mdir.is_dir():
                title, order = spec
                (mdir / "index.md").write_text(frontmatter(dict(title=title, order=order)), encoding="utf-8")
        print(f"  ✓ {p['src']:45} → {dst.relative_to(ROOT)}  ({n} files)")


def import_learning_path_index(src_root: Path):
    for rel, t in THEMES.items():
        d = CONTENT / rel
        body = ""
        if t.get("body_from") and rel == "04-agents-google-cloud":
            body = strip_frontmatter((src_root / t["body_from"]).read_text(encoding="utf-8"))
            body = anonymize_text(body) if ANON else body
        meta = dict(type="category", title=t["title"], icon=t["icon"], description=t["description"])
        if rel == "05-skills-gemini-enterprise":
            continue  # written by import_skills
        write_index(d, meta, body)


def import_skills(src_root: Path):
    src = src_root / "skills-agents-gemini-entreprise"
    dst = CONTENT / "05-skills-gemini-enterprise"
    if not src.exists():
        return
    shutil.rmtree(dst, ignore_errors=True)
    t = THEMES["05-skills-gemini-enterprise"]
    readme = strip_frontmatter((src / "README.md").read_text(encoding="utf-8"))
    readme = readme.replace("](CATALOG.md", "](00-catalogue.md").replace("](docs/SKILL-STANDARD.md", "](00-standard-skill.md")
    write_index(dst, dict(type="category", title=t["title"], icon=t["icon"], description=t["description"]), readme)
    # Loose articles of the theme
    for name, title, desc in [("CATALOG.md", "Catalogue des 160 skills", "Une ligne par skill, par métier."),
                              ("docs/SKILL-STANDARD.md", "Le standard d'écriture d'un skill", "Les règles que suit chaque skill de la bibliothèque.")]:
        f = src / name
        if f.exists():
            out = dst / ("00-catalogue.md" if name == "CATALOG.md" else "00-standard-skill.md")
            out.write_text(frontmatter(dict(title=title, description=desc, tags=["skills", "gemini-enterprise"], authors=AUTHOR))
                           + re.sub(r"\A#[^\n]*\n", "", strip_frontmatter(f.read_text(encoding="utf-8"))), encoding="utf-8")
    # Tooling stays downloadable (theme .zip) but never becomes pages.
    for extra in ("evals", "scripts"):
        if (src / extra).exists():
            copy_tree(src / extra, dst / f"_{extra}")
    skills_dir = dst / "skills"
    write_index(skills_dir, dict(type="category", title="Les skills par métier", icon="📚", order=1,
                                 description="17 métiers, 160 skills. Chaque skill se lit ici et se télécharge prêt à importer (.zip ou .md)."))
    count = 0
    for domain in sorted((src / "skills").iterdir()):
        if not domain.is_dir():
            continue
        title, icon = SKILL_DOMAINS.get(domain.name, (domain.name, "📁"))
        ddst = skills_dir / domain.name
        write_index(ddst, dict(type="category", title=title, icon=icon, description=f"Skills Gemini Enterprise : {title.lower()}."))
        for skill in sorted(domain.iterdir()):
            if not (skill / "SKILL.md").exists():
                continue
            sdst = ddst / skill.name
            copy_tree(skill, sdst)
            # Ready-to-upload packages sit next to the skill and show up as downloads.
            for packaged, ext in ((src / "dist" / "zip" / domain.name / f"{skill.name}.zip", "zip"),
                                  (src / "dist" / "md" / domain.name / f"{skill.name}.md", "md")):
                if packaged.exists():
                    (sdst / "files").mkdir(exist_ok=True)
                    shutil.copy2(packaged, sdst / "files" / packaged.name)
            count += 1
    if ANON:
        anonymize_tree(dst)
    print(f"  ✓ skills-agents-gemini-entreprise               → content/05-skills-gemini-enterprise  ({count} skills)")


def scan_secrets() -> list:
    hits = []
    for root, _, files in os.walk(CONTENT):
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".pdf", ".pptx", ".docx", ".zip", ".xlsx"}:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in SECRET.finditer(text):
                hits.append(f"{p.relative_to(ROOT)}: {m.group(0)[:16]}…")
    return hits


ANON = True
LOCAL_CONFIG = ROOT / "scripts" / "import-config.local.py"
if LOCAL_CONFIG.exists():
    exec(compile(LOCAL_CONFIG.read_text(encoding="utf-8"), str(LOCAL_CONFIG), "exec"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT.parent))
    ap.add_argument("--no-anonymize", action="store_true", help="keep client names (never for a public site)")
    a = ap.parse_args()
    global ANON
    ANON = not a.no_anonymize
    src = Path(a.src).resolve()
    print(f"Importing from {src}")
    import_learning_path_index(src)
    import_projects(src)
    import_skills(src)
    if ANON:
        forbidden = "|".join(a for a, _ in ANONYMIZE) or r"(?!x)x"
        left = [str(p.relative_to(ROOT)) for p in CONTENT.rglob("*") if p.is_file() and re.search(forbidden, p.name + (p.read_text("utf-8", "ignore") if p.suffix in TEXT_EXT else pdf_text(p) if p.suffix == ".pdf" else ""))]
        if left:
            print("\n✋ Client name still present in:\n  " + "\n  ".join(left[:20]))
            sys.exit(1)
        print("Anonymized: no client name left.")
    hits = scan_secrets()
    if hits:
        print("\n✋ Possible secrets found in content/ — remove them before publishing:\n  " + "\n  ".join(hits))
        sys.exit(1)
    print("No secrets detected.")


if __name__ == "__main__":
    main()
