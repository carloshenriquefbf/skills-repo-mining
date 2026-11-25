"""Etapa 3: baixa o conteudo dos SKILL.md dos repositorios candidatos e faz a
triagem por palavra-chave (apoio ao codebook; nao e a classificacao final)."""
from __future__ import annotations

import re

from .common import DATA, RAW_DIR, ROOT, config, parse_frontmatter, read_csv, read_jsonl, skills_root, write_csv
from .gh import GitHub, log

OUT = DATA / "skills.csv"
CONTENT_DIR = DATA / "skills"


def candidate_repos() -> dict[str, dict]:
    """Repos that pass the API-level filters of 5.3.1 (language, fork, archived)."""
    out = {}
    for r in read_csv(DATA / "repos.csv"):
        if r["status"] != "ok" or r["is_target_language"] != "True":
            continue
        if r["is_fork"] == "True" or r["is_mirror"] == "True":
            continue
        out[r["repo"]] = r
    return out


def run(gh: GitHub) -> None:
    rx = re.compile(config()["screening"]["test_regex"])
    repos = candidate_repos()
    files = {}
    for f in read_jsonl(RAW_DIR / "skill_files.jsonl"):
        if f["name"] == "SKILL.md" and f["repo"] in repos:
            files[(f["repo"], f["path"])] = f
    log(f"{len(files)} SKILL.md em {len(repos)} repositorios candidatos")

    rows = []
    for n, ((repo, path), f) in enumerate(sorted(files.items()), 1):
        meta = repos[repo]
        local = CONTENT_DIR / repo.replace("/", "__") / path
        if local.exists():
            text = local.read_text(errors="replace")
        else:
            text = gh.raw_file(repo, meta["default_branch"], path)
            if text is not None:
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_text(text)
        fm = parse_frontmatter(text or "")
        name, desc = fm.get("name", ""), fm.get("description", "")
        hits = sorted({m.group(0).lower() for m in rx.finditer(f"{name} {desc}")})
        hits_body = sorted({m.group(0).lower() for m in rx.finditer(text or "")})
        rows.append({
            "repo": repo,
            "path": path,
            "skills_root": skills_root(path),
            "fetched": text is not None,
            "has_frontmatter": bool(fm),
            "skill_name": name,
            "description": desc.replace("\n", " ")[:500],
            "test_hint": bool(hits),
            "test_terms": ";".join(hits),
            "test_terms_body": ";".join(hits_body[:15]),
            "html_url": f["html_url"],
            "local_file": str(local.relative_to(ROOT)) if text is not None else "",
        })
        if n % 100 == 0:
            log(f"{n}/{len(files)}")
    write_csv(OUT, rows)
    log(f"gravado {OUT}: {sum(r['test_hint'] for r in rows)} skills com indicio de teste")
