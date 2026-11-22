#!/usr/bin/env python3
import html
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "profile.config.json").read_text())
OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "mizuhitochizu")
TOKEN = os.getenv("GITHUB_TOKEN", "")


def escape(value):
    return html.escape(str(value), quote=True)


def github_repositories():
    params = urlencode({"sort": "pushed", "direction": "desc", "per_page": 100})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-generator"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = Request(f"https://api.github.com/users/{OWNER}/repos?{params}", headers=headers)
    with urlopen(request, timeout=20) as response:
        repos = json.load(response)

    excluded = {OWNER, "mizuhitochizu.github.io"}
    featured = set(CONFIG.get("featured", []))

    def rank(repo):
        name = repo["name"]
        return (name in featured, repo.get("pushed_at") or repo.get("created_at") or "")

    repos = [
        repo for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("private")
        and repo["name"] not in excluded
    ]
    repos.sort(key=rank, reverse=True)
    return repos[:CONFIG.get("project_count", 4)]


def project_card(repo, x, y, width):
    name = escape(repo["name"])
    description = escape(repo.get("description") or "A public project repository")
    if len(description) > 58:
        description = description[:55] + "..."
    language = escape(repo.get("language") or "Project")
    url = escape(repo["html_url"])

    return f'''<a href="{url}" target="_blank">
      <g class="card" transform="translate({x} {y})">
        <rect width="{width}" height="118" rx="12" fill="#0D1117" stroke="#30363D"/>
        <rect x="0" y="0" width="4" height="118" rx="2" fill="{CONFIG['accent']}"/>
        <text x="20" y="38" fill="#F0F6FC" font-size="18" font-weight="650">{name}</text>
        <text x="20" y="68" fill="#8B949E" font-size="12">{description}</text>
        <circle cx="23" cy="94" r="4" fill="{CONFIG['accent_alt']}"/>
        <text x="34" y="99" fill="#8B949E" font-size="12">{language}</text>
        <text x="{width - 20}" y="99" fill="#58A6FF" font-size="12" text-anchor="end">VIEW →</text>
      </g>
    </a>'''


def build_banner(repos):
    accent = escape(CONFIG["accent"])
    accent_alt = escape(CONFIG["accent_alt"])
    tagline = escape(CONFIG["tagline"])
    focuses = CONFIG["focuses"]

    cards = []
    if repos:
        cards.append('''<g transform="translate(58 220)"><text fill="#8B949E" font-size="12" letter-spacing="3">RECENT PROJECTS</text></g>''')
        card_width = 250
        for index, repo in enumerate(repos):
            x = 58 + (index % 4) * 274
            y = 246
            cards.append(project_card(repo, x, y, card_width))

    focus_items = "".join(
        f'<text class="focus f{i}" x="58" y="178" fill="#8B949E" font-size="17">{escape(item)}</text>'
        for i, item in enumerate(focuses[:5])
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="390" viewBox="0 0 1200 390" role="img" aria-labelledby="title desc">
  <title id="title">mizuhitochizu profile</title>
  <desc id="desc">A concise animated profile banner and live list of public projects.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#090B10"/><stop offset="1" stop-color="#111827"/>
    </linearGradient>
    <linearGradient id="signal" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{accent_alt}"/>
    </linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  <style>
    .card {{ transition: transform .18s ease, filter .18s ease; }}
    a:hover .card {{ transform: translateY(-4px); filter: brightness(1.08); }}
    .focus {{ opacity: 0; }}
    {"".join(f".f{i} {{ animation: focus{i} 20s infinite; }}" for i in range(len(focuses[:5]))) }
    {"".join(f"@keyframes focus{i} {{ {i*20}% {{ opacity: 0; transform: translateY(4px); }} {i*20+2}% {{ opacity: 1; transform: translateY(0); }} {i*20+18}% {{ opacity: 1; }} {i*20+20}% {{ opacity: 0; }} }}" for i in range(len(focuses[:5]))) }
  </style>

  <rect width="1200" height="390" rx="20" fill="url(#bg)"/>
  <circle cx="1060" cy="58" r="170" fill="{accent_alt}" opacity="0.055" filter="url(#soft)"/>
  <circle cx="1128" cy="308" r="120" fill="{accent}" opacity="0.04" filter="url(#soft)"/>

  <g transform="translate(58 58)">
    <rect width="54" height="4" rx="2" fill="url(#signal)"/>
    <text x="0" y="58" fill="#F0F6FC" font-family="Inter,Segoe UI,sans-serif" font-size="52" font-weight="700" letter-spacing="-2">mizuhitochizu</text>
  </g>

  <text x="58" y="142" fill="#C9D1D9" font-size="17">{tagline}</text>
  {focus_items}
  {"".join(cards)}

  <circle cx="1124" cy="190" r="5" fill="{accent}"><animate attributeName="opacity" values="1;.25;1" dur="2.8s" repeatCount="indefinite"/></circle>
  <text x="1140" y="194" fill="#6E7681" font-size="12" text-anchor="end">UPDATED</text>
</svg>'''

    (ROOT / "profile-banner.svg").write_text(svg)


def build_readme(repos):
    project_links = ""
    if repos:
        items = []
        for repo in repos:
            name = escape(repo["name"])
            url = escape(repo["html_url"])
            description = escape(repo.get("description") or "")
            suffix = f" — {description}" if description else ""
            items.append(f"<a href=\"{url}\"><b>{name}</b></a>{suffix}")
        project_links = "\n\n".join(f"<br>" + item for item in items)

    readme = f'''<div align="center">

<img src="./profile-banner.svg" width="100%" alt="mizuhitochizu profile banner" />

<a href="https://github.com/mizuhitochizu?tab=repositories"><img src="https://img.shields.io/badge/Repositories-0D1117?style=flat-square&logo=github&logoColor=F0F6FC" alt="Repositories" /></a>
<a href="https://github.com/mizuhitochizu?tab=followers"><img src="https://img.shields.io/badge/Follow-0D1117?style=flat-square&logo=github&logoColor=58A6FF" alt="Follow on GitHub" /></a>

</div>

## Recent public work

{project_links or "Project links are generated automatically from public repositories."}
'''
    (ROOT / "README.md").write_text(readme)


repos = github_repositories()
build_banner(repos)
build_readme(repos)
