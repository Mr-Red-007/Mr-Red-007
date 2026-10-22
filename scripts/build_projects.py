#!/usr/bin/env python3
"""Rebuild the project showcase (assets/projects.svg) and the README project block.

Runs in GitHub Actions. Reads public, non-fork, non-archived repos from the
GitHub API, so a new public repo appears on the next scheduled run.
"""
import html
import json
import math
import os
import re
import textwrap
import urllib.request

USER = "Mr-Red-007"
README = "README.md"
SVG_OUT = "assets/projects.svg"
MAX_CARDS = 12
CARD_W, CARD_H, GAP, PAD = 400, 132, 20, 20
ACCENTS = ["#ff2a6d", "#ff8a00", "#00e5ff", "#2ee59d", "#a86bff", "#ffd166"]


def fetch_repos():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-builder"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/users/{USER}/repos?sort=updated&per_page=100"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
        repos = json.load(resp)
    return [r for r in repos if not r["fork"] and not r["archived"] and r["name"] != USER]


def card(i, repo):
    col, row = i % 2, i // 2
    x = PAD + col * (CARD_W + GAP)
    y = PAD + row * (CARD_H + GAP)
    accent = ACCENTS[i % len(ACCENTS)]

    full = textwrap.wrap(repo.get("description") or "No description yet.", width=56)
    lines = full[:2]
    if len(full) > 2:
        lines[1] = lines[1].rstrip() + "…"
    d1 = html.escape(lines[0]) if lines else ""
    d2 = html.escape(lines[1]) if len(lines) > 1 else ""

    name = html.escape(repo["name"])
    lang = html.escape(repo.get("language") or "Misc")
    stars = repo.get("stargazers_count", 0)

    return f'''<g transform="translate({x},{y})"><g class="card" style="animation-delay:{i * 0.15:.2f}s">
  <rect width="{CARD_W}" height="{CARD_H}" rx="14" fill="#0c0c12" stroke="{accent}" stroke-opacity="0.45"/>
  <rect width="5" height="{CARD_H}" rx="2" fill="{accent}"/>
  <text x="24" y="38" class="name" fill="{accent}">{name}</text>
  <text x="24" y="64" class="desc">{d1}</text>
  <text x="24" y="84" class="desc">{d2}</text>
  <text x="24" y="{CARD_H - 18}" class="meta">● {lang}    ★ {stars}</text>
</g></g>'''


def build_svg(repos):
    if not repos:
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="860" height="90" viewBox="0 0 860 90">'
                '<rect width="860" height="90" rx="16" fill="#07070b"/>'
                '<text x="430" y="52" text-anchor="middle" fill="#7d8196" '
                'font-family="monospace" font-size="16">No public projects yet</text></svg>')

    rows = math.ceil(len(repos) / 2)
    width = PAD * 2 + 2 * CARD_W + GAP
    height = PAD * 2 + rows * CARD_H + (rows - 1) * GAP
    cards = "\n".join(card(i, r) for i, r in enumerate(repos))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  text {{ font-family: 'Fira Code', Consolas, 'Courier New', monospace; }}
  .name {{ font-size: 18px; font-weight: 700; }}
  .desc {{ font-size: 13px; fill: #c9cbd6; }}
  .meta {{ font-size: 12px; fill: #7d8196; }}
  .card {{ animation: rise .7s ease both; }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
</style>
<rect width="{width}" height="{height}" rx="16" fill="#07070b"/>
{cards}
</svg>'''


def link_row(repos):
    return " · ".join(f"[**{r['name']}**]({r['html_url']})" for r in repos) or "No public projects yet."


def update_readme(repos):
    block = ("<!-- PROJECTS:START -->\n"
             '<p align="center">\n'
             f'  <img src="./{SVG_OUT}" alt="Project showcase" width="860" />\n'
             "</p>\n\n"
             f'<p align="center">{link_row(repos)}</p>\n'
             "<!-- PROJECTS:END -->")
    text = open(README, encoding="utf-8").read()
    new, count = re.subn(r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->",
                         lambda m: block, text, flags=re.S)
    if count == 0:
        raise SystemExit("PROJECTS markers not found in README.md")
    open(README, "w", encoding="utf-8").write(new)


def main():
    repos = fetch_repos()[:MAX_CARDS]
    os.makedirs(os.path.dirname(SVG_OUT), exist_ok=True)
    with open(SVG_OUT, "w", encoding="utf-8") as f:
        f.write(build_svg(repos))
    update_readme(repos)
    print(f"Built {len(repos)} project card(s)")


if __name__ == "__main__":
    main()
