"""Etapa 5: funil de selecao (Anexo C) e M1-M3 preliminares em reports/."""
from __future__ import annotations

import time
from collections import Counter

from .common import DATA, RAW_DIR, REPORTS, config, read_csv, read_jsonl, write_csv


def _t(v) -> bool:
    return str(v) == "True"


def run() -> None:
    cfg = config()
    files = read_jsonl(RAW_DIR / "skill_files.jsonl")
    log = read_jsonl(RAW_DIR / "search_log.jsonl")
    repos = read_csv(DATA / "repos.csv")
    skills = read_csv(DATA / "skills.csv")
    adoption = read_csv(DATA / "adoption.csv")

    uniq = {(f["repo"], f["path"]) for f in files if f["name"] == "SKILL.md"}
    ok = [r for r in repos if r["status"] == "ok"]
    nofork = [r for r in ok if not _t(r["is_fork"]) and not _t(r["is_mirror"])]
    py = [r for r in nofork if _t(r["is_target_language"])]
    hint_repos = {s["repo"] for s in skills if _t(s["test_hint"])}
    collection = {r["repo"] for r in py if int(r["n_skill_files_found"] or 0) >= 10 or "skill" in r["repo"].split("/")[1].lower()}
    ad_ok = [a for a in adoption if a["status"] == "ok"]
    not_initial = [a for a in ad_ok if not _t(a["t0_is_initial_commit"])]
    complete = [a for a in not_initial if _t(a["post_window_complete"])]
    eligible = [a for a in adoption if _t(a.get("eligible_prescreen"))]
    eligible_nocoll = [a for a in eligible if a["repo"] not in collection]

    funnel = [
        ("Arquivos SKILL.md unicos (repo, caminho) retornados pela busca", len(uniq)),
        ("Repositorios distintos", len({r for r, _ in uniq})),
        ("Repositorios com metadados obtidos", len(ok)),
        ("... nao fork / nao mirror", len(nofork)),
        (f"... linguagem principal {cfg['filters']['primary_language']}", len(py)),
        ("... com >=1 SKILL.md com indicio de teste (triagem, pre-codebook)", len(hint_repos)),
        ("... t0 identificado", len(ad_ok)),
        ("... t0 diferente do commit inicial", len(not_initial)),
        (f"... janela pos completa ate a coleta (C={cfg['windows']['grace_days']}d)", len(complete)),
        (f"... >= {cfg['filters']['min_commits_per_window']} commits em cada janela e nao arquivado", len(eligible)),
        ("... sem sinal de colecao/catalogo de skills (verificar manualmente)", len(eligible_nocoll)),
    ]
    write_csv(REPORTS / "funnel.csv", [{"etapa": k, "n": v} for k, v in funnel])

    t0_month = Counter(a["t0"][:7] for a in ad_ok)
    roots = Counter(s["skills_root"] for s in skills)
    terms = Counter(t for s in skills if _t(s["test_hint"]) for t in s["test_terms"].split(";") if t)
    truncated = [l for l in log if l.get("truncated")]

    md = [f"# Resultados preliminares da API do GitHub\n",
          f"Coleta: {time.strftime('%Y-%m-%d')}. Consultas: " + "; ".join(f"`{q}`" for q in cfg["discovery"]["queries"]),
          f"\nParticoes da busca: {len(log)} (truncadas no teto de 1000: {len(truncated)}).\n",
          "## Funil de selecao (Anexo C)\n", "| Etapa | N |", "|---|---:|"]
    md += [f"| {k} | {v} |" for k, v in funnel]
    md += ["\n## M1 preliminar\n",
           f"Repositorios Python com SKILL.md com indicio de teste: **{len(hint_repos)}** "
           f"(triagem por palavra-chave; o M1 final depende do codebook).",
           f"\nPre-elegiveis para G2: **{len(eligible_nocoll)}** "
           f"(regra de contingencia: N >= 30 para analise confirmatoria).\n",
           "## M3 preliminar: t0 por mes\n", "| Mes | Repositorios |", "|---|---:|"]
    md += [f"| {m} | {n} |" for m, n in sorted(t0_month.items())]
    md += ["\n## Onde as skills ficam (pasta raiz)\n", "| Pasta | SKILL.md |", "|---|---:|"]
    md += [f"| `{k}` | {v} |" for k, v in roots.most_common(15)]
    md += ["\n## Termos de teste na descricao (triagem)\n", "| Termo | Skills |", "|---|---:|"]
    md += [f"| {k} | {v} |" for k, v in terms.most_common(20)]
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
