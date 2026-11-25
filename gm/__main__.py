"""python -m gm <etapa> [--pilot]

Etapas (na ordem):
  count      total de resultados por consulta (1 requisicao cada; mede a busca)
  discover   busca de codigo -> data/raw/skill_files.jsonl
  metadata   GraphQL -> data/repos.csv
  skills     conteudo dos SKILL.md + triagem -> data/skills.csv, data/skills/
  adoption   t0 e commits por janela -> data/adoption.csv  (--all: todas as skills)
  report     funil + M1-M3 preliminares -> reports/
  all        discover, metadata, skills, adoption, report

--pilot: discover coleta so 1 pagina por faixa de tamanho (config.toml) e todas
as etapas leem/gravam em data/pilot/ e reports/pilot/.
"""
import os
import sys

if "--pilot" in sys.argv:  # must be set before gm.common is imported
    os.environ["GM_PILOT"] = "1"

from . import adoption, discover, metadata, report, skills  # noqa: E402
from .gh import GitHub  # noqa: E402


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pilot = "--pilot" in sys.argv
    if not args or "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return
    step = args[0]
    if step == "report":
        report.run()
        return
    gh = GitHub()
    run_discover = discover.pilot if pilot else discover.run
    if step == "count":
        discover.count_only(gh)
    elif step == "discover":
        run_discover(gh)
    elif step == "metadata":
        metadata.run(gh)
    elif step == "skills":
        skills.run(gh)
    elif step == "adoption":
        adoption.run(gh, all_skills="--all" in sys.argv)
    elif step == "all":
        run_discover(gh)
        metadata.run(gh)
        skills.run(gh)
        adoption.run(gh)
        report.run()
    else:
        raise SystemExit(f"etapa desconhecida: {step}\n{__doc__}")


main()
