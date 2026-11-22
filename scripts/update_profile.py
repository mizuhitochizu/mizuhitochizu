#!/usr/bin/env python3
import html
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "mizuhitochizu")
TOKEN = os.getenv("GITHUB_TOKEN", "")
CONFIG = json.loads((ROOT / "profile.config.json").read_text())


def escape(value):
    return html.escape(str(value), quote=True)


def public_repositories():
    params = urlencode({"sort": "pushed", "direction": "desc", "per_page": 100})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-generator"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urlopen(Request(f"https://api.github.com/users/{OWNER}/repos?{params}", headers=headers), timeout=20) as response:
        repos = json.load(response)
    repos = [r for r in repos if not r.get("fork") and not r.get("archived") and not r.get("private") and r["name"] != OWNER]
    repos.sort(key=lambda r: r.get("pushed_at") or r.get("created_at") or "", reverse=True)
    return repos[:CONFIG.get("project_count", 4)]


def build_readme(repos):
    project_links = "No public projects to display." if not repos else "\n\n".join(
        f'<a href="{escape(r["html_url"])}"><b>{escape(r["name"])}</b></a> — {escape(r.get("description") or "Public repository")}'
        for r in repos
    )
    readme = '''<div align="center">

<img src="./profile-banner.svg" width="100%" alt="mizuhitochizu profile banner" />

<a href="https://github.com/mizuhitochizu?tab=repositories"><img src="https://img.shields.io/badge/Repositories-0D1117?style=flat-square&logo=github&logoColor=F0F6FC" alt="Repositories" /></a>
<a href="https://github.com/mizuhitochizu?tab=followers"><img src="https://img.shields.io/badge/Follow-0D1117?style=flat-square&logo=github&logoColor=58A6FF" alt="Follow on GitHub" /></a>

</div>

## Languages tried

Python · JavaScript · Swift · HTML · CSS · Shell · SQL

## Coding partners

Gemini, ChatGPT, and Claude — depending on the problem, all three sometimes get an assignment.

## Recent public work

''' + project_links
    (ROOT / "README.md").write_text(readme)


build_readme(public_repositories())
