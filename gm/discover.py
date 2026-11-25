"""Etapa 1: descoberta de arquivos SKILL.md pela busca de codigo do GitHub.

Cada consulta do config.toml e particionada recursivamente por `size:` sempre
que total_count > 1000 (teto da API). Cada particao folha e registrada em
data/raw/search_log.jsonl, o que permite retomar a coleta e medir a cobertura
da busca (protocolo, secao 5.3.4).
"""
from __future__ import annotations

import math
import time

from .common import RAW_DIR, append_jsonl, config, read_jsonl
from .gh import GitHub, log

CAP = 1000
FILES = RAW_DIR / "skill_files.jsonl"
SEARCH_LOG = RAW_DIR / "search_log.jsonl"


def _search(gh: GitHub, q: str, page: int = 1):
    data, _ = gh.get("/search/code", {"q": q, "per_page": 100, "page": page})
    return data


def _row(item: dict, query: str) -> dict:
    repo = item["repository"]
    return {
        "query": query,
        "repo": repo["full_name"],
        "repo_id": repo["id"],
        "fork": repo.get("fork"),
        "path": item["path"],
        "name": item["name"],
        "blob_sha": item["sha"],
        "html_url": item["html_url"],
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _collect(gh: GitHub, base: str, lo: int, hi: int, done: set[str]) -> None:
    q = f"{base} size:{lo}..{hi}"
    if q in done:
        return
    first = _search(gh, q)
    total = first["total_count"]
    if total > CAP and hi > lo:
        mid = (lo + hi) // 2
        log(f"{q}: {total} > {CAP}, particionando")
        _collect(gh, base, lo, mid, done)
        _collect(gh, base, mid + 1, hi, done)
        return

    rows = [_row(i, base) for i in first["items"]]
    pages = math.ceil(min(total, CAP) / 100)
    for page in range(2, pages + 1):
        rows += [_row(i, base) for i in _search(gh, q, page)["items"]]
    append_jsonl(FILES, rows)
    append_jsonl(SEARCH_LOG, [{
        "query": q, "base": base, "lo": lo, "hi": hi, "total_count": total,
        "retrieved": len(rows), "truncated": total > CAP,
        "incomplete_results": first.get("incomplete_results"), "status": "done",
    }])
    done.add(q)
    log(f"{q}: total={total} coletados={len(rows)}")


def pilot(gh: GitHub) -> None:
    """Pilot: page 1 (100 results) of each file-size band, per query.

    Spreads the sample across sizes instead of taking the top of the
    best-match ranking. Each band's total_count is logged so the pilot's
    yield can be weighted back to the full query.
    """
    cfg = config()["discovery"]
    width, n = cfg["pilot_band_bytes"], cfg["pilot_bands"]
    bands = [(i * width + (1 if i else 0), (i + 1) * width) for i in range(n - 1)]
    bands.append(((n - 1) * width + 1, cfg["max_file_size"]))
    done = {r["query"] for r in read_jsonl(SEARCH_LOG) if r.get("status") == "done"}
    for base in cfg["queries"]:
        for band, (lo, hi) in enumerate(bands, 1):
            q = f"{base} size:{lo}..{hi}"
            if q in done:
                continue
            data = _search(gh, q)
            rows = [{**_row(i, base), "band": band} for i in data["items"]]
            append_jsonl(FILES, rows)
            append_jsonl(SEARCH_LOG, [{
                "query": q, "base": base, "lo": lo, "hi": hi, "band": band,
                "total_count": data["total_count"], "retrieved": len(rows),
                "incomplete_results": data.get("incomplete_results"),
                "mode": "pilot", "status": "done",
            }])
            log(f"faixa {band:>2} {lo}..{hi}: total={data['total_count']} coletados={len(rows)}")
    rows = read_jsonl(FILES)
    uniq = {(r["repo"], r["path"]) for r in rows}
    log(f"piloto: {len(uniq)} arquivos unicos em {len({r for r, _ in uniq})} repositorios")


def count_only(gh: GitHub) -> None:
    """Total per query + rough collection cost. Logged to count_log.jsonl."""
    cfg = config()["discovery"]
    queries = [("coleta", q) for q in cfg["queries"]]
    queries += [("candidata", q) for q in cfg.get("count_candidates", [])]
    print(f"{'resultados':>11} {'req.':>7} {'tempo':>8}  tipo       consulta")
    for kind, q in queries:
        d = _search(gh, q)
        total = d["total_count"]
        # ~1 req per 100 results + ~15% for partition probes; 10 req/min
        reqs = math.ceil(total / 100 * 1.15) if total else 1
        mins = reqs / 10
        when = f"{mins:.0f} min" if mins < 90 else f"{mins / 60:.1f} h"
        print(f"{total:>11,} {reqs:>7,} {when:>8}  {kind:<10} {q}", flush=True)
        append_jsonl(RAW_DIR / "count_log.jsonl", [{
            "query": q, "kind": kind, "total_count": total,
            "incomplete_results": d["incomplete_results"],
            "counted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }])


def run(gh: GitHub) -> None:
    cfg = config()["discovery"]
    done = {r["query"] for r in read_jsonl(SEARCH_LOG) if r.get("status") == "done"}
    for base in cfg["queries"]:
        _collect(gh, base, 0, cfg["max_file_size"], done)
    rows = read_jsonl(FILES)
    uniq = {(r["repo"], r["path"]) for r in rows}
    log(f"total: {len(uniq)} arquivos unicos em {len({r for r, _ in uniq})} repositorios")
