"""Minimal GitHub REST/GraphQL client (stdlib only) with rate-limit handling."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
USER_AGENT = "cps820-msr-study"


class GitHubError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, file=sys.stderr, flush=True)


def _dotenv_token() -> str | None:
    """GITHUB_TOKEN from the project's .env (git-ignored), if present."""
    env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(env):
        return None
    for line in open(env):
        k, _, v = line.strip().partition("=")
        if k.strip() in ("GITHUB_TOKEN", "GH_TOKEN") and v.strip():
            return v.strip().strip("'\"")
    return None


class GitHub:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or _dotenv_token()
        if not self.token:
            raise SystemExit(
                "Defina GITHUB_TOKEN (fine-grained, somente leitura de repositorios publicos).\n"
                "  export GITHUB_TOKEN=github_pat_..."
            )

    # ------------------------------------------------------------------ core
    def _send(self, method: str, url: str, body: dict | None = None, raw: bool = False):
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(10):
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("User-Agent", USER_AGENT)
            if not url.startswith(RAW):
                if self.token:
                    req.add_header("Authorization", f"Bearer {self.token}")
                req.add_header("Accept", "application/vnd.github+json")
                req.add_header("X-GitHub-Api-Version", "2022-11-28")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    payload = resp.read()
                    self._respect_remaining(resp.headers)
                    if raw:
                        return payload.decode("utf-8", errors="replace"), resp.headers
                    return (json.loads(payload) if payload else None), resp.headers
            except urllib.error.HTTPError as e:
                text = e.read().decode("utf-8", errors="replace")
                if e.code in (403, 429) and self._is_rate_limited(e.headers, text):
                    self._sleep_for_limit(e.headers, attempt)
                    continue
                if e.code in (500, 502, 503, 504):
                    time.sleep(min(2 ** attempt, 60))
                    continue
                raise GitHubError(e.code, text) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                log(f"erro de rede ({e}); tentando de novo")
                time.sleep(min(2 ** attempt, 60))
        raise GitHubError(0, f"desisti apos varias tentativas: {url}")

    @staticmethod
    def _is_rate_limited(headers, text: str) -> bool:
        return (
            headers.get("Retry-After") is not None
            or headers.get("X-RateLimit-Remaining") == "0"
            or "rate limit" in text.lower()
        )

    @staticmethod
    def _sleep_for_limit(headers, attempt: int) -> None:
        if headers.get("Retry-After"):
            wait = int(headers["Retry-After"]) + 1
        elif headers.get("X-RateLimit-Remaining") == "0" and headers.get("X-RateLimit-Reset"):
            wait = max(int(headers["X-RateLimit-Reset"]) - time.time(), 0) + 2
        else:  # secondary rate limit without hints
            wait = 60 * (attempt + 1)
        log(f"limite de taxa; aguardando {wait:.0f}s")
        time.sleep(wait)

    @staticmethod
    def _respect_remaining(headers) -> None:
        """Proactively wait when the current bucket is exhausted."""
        if headers.get("X-RateLimit-Remaining") == "0" and headers.get("X-RateLimit-Reset"):
            wait = max(int(headers["X-RateLimit-Reset"]) - time.time(), 0) + 2
            log(f"cota esgotada ({headers.get('X-RateLimit-Resource')}); aguardando {wait:.0f}s")
            time.sleep(wait)

    # --------------------------------------------------------------- helpers
    def get(self, path: str, params: dict | None = None):
        url = path if path.startswith("http") else API + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        return self._send("GET", url)

    def graphql(self, query: str):
        data, _ = self._send("POST", API + "/graphql", {"query": query})
        return data

    def raw_file(self, repo: str, ref: str, path: str) -> str | None:
        url = f"{RAW}/{repo}/{urllib.parse.quote(ref)}/{urllib.parse.quote(path)}"
        try:
            text, _ = self._send("GET", url, raw=True)
            return text
        except GitHubError as e:
            if e.status == 404:
                return None
            raise

    def last_page(self, headers) -> int:
        """Page number of rel="last" in the Link header (1 if no pagination)."""
        link = headers.get("Link") or ""
        m = re.search(r'[?&]page=(\d+)[^>]*>;\s*rel="last"', link)
        return int(m.group(1)) if m else 1

    def count(self, path: str, params: dict) -> int:
        """Count list items cheaply with per_page=1 and the Link header."""
        try:
            data, headers = self.get(path, {**params, "per_page": 1})
        except GitHubError as e:
            if e.status == 409:  # empty repository
                return 0
            raise
        if not data:
            return 0
        return self.last_page(headers)

    def oldest(self, path: str, params: dict):
        """Last element of a newest-first paginated list (e.g. commits)."""
        data, headers = self.get(path, {**params, "per_page": 100})
        last = self.last_page(headers)
        if last > 1:
            data, _ = self.get(path, {**params, "per_page": 100, "page": last})
        return data[-1] if data else None
