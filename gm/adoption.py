"""Etapa 4: data de adocao (t0) e triagem de elegibilidade pela API.

t0 por repositorio = data (committer) do commit mais antigo, no ramo padrao,
que toca o caminho de um SKILL.md com indicio de teste; o t0 do repositorio e
o minimo entre esses caminhos.

Limitacoes conhecidas desta triagem (resolvidas na extracao por clone, semana 2):
- `commits?path=` nao segue renomeacoes: se a skill foi movida, t0 = data da
  chegada ao caminho atual.
- as contagens de commits nas janelas incluem merges e bots.
"""
from __future__ import annotations

import datetime as dt


from .common import DATA, config, read_csv, write_csv
from .gh import GitHub, GitHubError, log
from .skills import candidate_repos

OUT = DATA / "adoption.csv"


def _iso(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _commit_info(c: dict) -> tuple[str, str, str]:
    return c["sha"], c["commit"]["committer"]["date"], c["commit"]["author"]["date"]


def run(gh: GitHub, all_skills: bool = False) -> None:
    cfg = config()
    win = dt.timedelta(days=cfg["windows"]["window_days"])
    grace = dt.timedelta(days=cfg["windows"]["grace_days"])
    min_commits = cfg["filters"]["min_commits_per_window"]
    now = dt.datetime.now(dt.timezone.utc)

    repos = candidate_repos()
    by_repo: dict[str, list[str]] = {}
    for s in read_csv(DATA / "skills.csv"):
        if all_skills or s["test_hint"] == "True":
            by_repo.setdefault(s["repo"], []).append(s["path"])
    log(f"{len(by_repo)} repositorios para extrair t0")

    rows = []
    for n, (repo, paths) in enumerate(sorted(by_repo.items()), 1):
        meta = repos[repo]
        branch = meta["default_branch"]
        base = f"/repos/{repo}/commits"
        row = {"repo": repo, "default_branch": branch, "n_test_skills": len(paths)}
        try:
            firsts = []
            for p in paths:
                c = gh.oldest(base, {"sha": branch, "path": p})
                if c:
                    firsts.append((*_commit_info(c), p))
            if not firsts:
                rows.append({**row, "status": "t0_not_found"})
                continue
            sha, t0s, t0_author, t0_path = min(firsts, key=lambda x: x[1])
            init = gh.oldest(base, {"sha": branch})
            t0 = _parse(t0s)
            pre = gh.count(base, {"sha": branch, "since": _iso(t0 - win), "until": _iso(t0)})
            post_start, post_end = t0 + grace, t0 + grace + win
            post = gh.count(base, {"sha": branch, "since": _iso(post_start), "until": _iso(post_end)})
        except GitHubError as e:
            rows.append({**row, "status": f"error_{e.status}"})
            log(f"{repo}: {e}")
            continue

        post_complete = post_end <= now
        t0_is_initial = init is not None and init["sha"] == sha
        row.update({
            "status": "ok",
            "t0": t0s,
            "t0_author_date": t0_author,
            "t0_sha": sha,
            "t0_path": t0_path,
            "repo_first_commit": init["commit"]["committer"]["date"] if init else "",
            "t0_is_initial_commit": t0_is_initial,
            "days_history_before_t0": (t0 - _parse(init["commit"]["committer"]["date"])).days if init else "",
            "commits_pre": pre,
            "commits_post": post,
            "post_window_end": _iso(post_end),
            "post_window_complete": post_complete,
            "is_archived": meta["is_archived"],
            "eligible_prescreen": (
                pre >= min_commits and post >= min_commits and post_complete
                and not t0_is_initial and meta["is_archived"] != "True"
            ),
        })
        rows.append(row)
        if n % 25 == 0:
            log(f"{n}/{len(by_repo)}")

    write_csv(OUT, rows, fields=FIELDS)
    log(f"gravado {OUT}")


FIELDS = [
    "repo", "status", "default_branch", "n_test_skills", "t0", "t0_author_date", "t0_sha",
    "t0_path", "repo_first_commit", "t0_is_initial_commit", "days_history_before_t0",
    "commits_pre", "commits_post", "post_window_end", "post_window_complete", "is_archived",
    "eligible_prescreen",
]
