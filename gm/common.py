from __future__ import annotations

import csv
import json
import os
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# --pilot (set by __main__) keeps pilot data apart from the definitive collection
PILOT = os.environ.get("GM_PILOT") == "1"
DATA = ROOT / "data" / "pilot" if PILOT else ROOT / "data"
RAW_DIR = DATA / "raw"
REPORTS = ROOT / "reports" / "pilot" if PILOT else ROOT / "reports"


def config() -> dict:
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def skills_root(path: str) -> str:
    """Folder that holds skill folders: '.claude/skills/foo/SKILL.md' -> '.claude/skills'."""
    parts = path.split("/")
    return "/".join(parts[:-2]) if len(parts) >= 3 else "(raiz)"


def parse_frontmatter(text: str) -> dict:
    """Small YAML-frontmatter reader for name/description (no external deps)."""
    if not text or not text.lstrip("\ufeff").startswith("---"):
        return {}
    body = text.lstrip("\ufeff")[3:]
    end = re.search(r"^---\s*$", body, re.M)
    if not end:
        return {}
    lines = body[: end.start()].splitlines()
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
        i += 1
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("|", ">", "|-", ">-", "|+", ">+") or val == "":
            block = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            val = " ".join(b for b in block if b)
        out[key] = val.strip().strip("'\"")
    return out
