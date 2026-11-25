"""Etapa 2: metadados dos repositorios descobertos via GraphQL (lotes de 40)."""
from __future__ import annotations

import json

from .common import DATA, RAW_DIR, config, read_jsonl, write_csv
from .gh import GitHub, log

OUT = DATA / "repos.csv"
BATCH = 40

FRAGMENT = """
fragment R on Repository {
  nameWithOwner databaseId isFork isArchived isTemplate isMirror isPrivate
  createdAt pushedAt stargazerCount forkCount diskUsage description
  primaryLanguage { name }
  licenseInfo { spdxId }
  defaultBranchRef { name target { ... on Commit { history { totalCount } } } }
  languages(first: 15, orderBy: {field: SIZE, direction: DESC}) {
    totalSize edges { size node { name } }
  }
  repositoryTopics(first: 20) { nodes { topic { name } } }
}
"""


def _query(repos: list[str]) -> str:
    parts = []
    for i, full in enumerate(repos):
        owner, name = full.split("/", 1)
        parts.append(f"r{i}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ ...R }}")
    return "query {\n" + "\n".join(parts) + "\nrateLimit { cost remaining resetAt }\n}\n" + FRAGMENT


def _flatten(full: str, r: dict | None) -> dict:
    if r is None:
        return {"repo": full, "status": "not_found"}
    langs = r["languages"]
    total = langs["totalSize"] or 0
    py = sum(e["size"] for e in langs["edges"] if e["node"]["name"] == "Python")
    branch = r["defaultBranchRef"] or {}
    target = branch.get("target") or {}
    return {
        "repo": full,
        "status": "ok",
        "canonical_name": r["nameWithOwner"],
        "repo_id": r["databaseId"],
        "primary_language": (r["primaryLanguage"] or {}).get("name"),
        "py_bytes_share": round(py / total, 4) if total else 0.0,
        "is_fork": r["isFork"],
        "is_archived": r["isArchived"],
        "is_template": r["isTemplate"],
        "is_mirror": r["isMirror"],
        "created_at": r["createdAt"],
        "pushed_at": r["pushedAt"],
        "stars": r["stargazerCount"],
        "forks": r["forkCount"],
        "disk_kb": r["diskUsage"],
        "default_branch": branch.get("name"),
        "default_branch_commits": (target.get("history") or {}).get("totalCount"),
        "license": (r["licenseInfo"] or {}).get("spdxId"),
        "topics": ";".join(n["topic"]["name"] for n in r["repositoryTopics"]["nodes"]),
        "description": (r["description"] or "").replace("\n", " ")[:300],
    }


def run(gh: GitHub) -> None:
    files = read_jsonl(RAW_DIR / "skill_files.jsonl")
    repos = sorted({f["repo"] for f in files})
    log(f"{len(repos)} repositorios para consultar")
    rows = []
    for start in range(0, len(repos), BATCH):
        chunk = repos[start:start + BATCH]
        res = gh.graphql(_query(chunk))
        data = (res or {}).get("data") or {}
        for i, full in enumerate(chunk):
            rows.append(_flatten(full, data.get(f"r{i}")))
        rl = data.get("rateLimit") or {}
        log(f"{start + len(chunk)}/{len(repos)}  graphql remaining={rl.get('remaining')}")

    # skill counts per repo help flag skill collections/catalogs (exclusion in 5.3.1)
    per_repo: dict[str, set] = {}
    for f in files:
        if f["name"] == "SKILL.md":
            per_repo.setdefault(f["repo"], set()).add(f["path"])
    lang = config()["filters"]["primary_language"]
    for r in rows:
        r["n_skill_files_found"] = len(per_repo.get(r["repo"], ()))
        r["is_target_language"] = r.get("primary_language") == lang
    write_csv(OUT, rows)
    log(f"gravado {OUT}")
