#!/usr/bin/env python3
"""readme-badges - build one consistent, linked badge row.

Python 3.9+, standard library only. Reads `git remote get-url origin` to fill in
owner and repo, then emits only the badges the repository can actually back:
a CI badge when `.github/workflows/` has a workflow, a package badge when it has
a manifest, a licence badge when it has a LICENSE.

Every badge it emits points at live data and is wrapped in the link to the page
it reports on - the two rules that separate a status line from decoration.

    readme_badges.py                       # detect and print the row
    readme_badges.py --style for-the-badge
    readme_badges.py --only ci,license,version
    readme_badges.py --format html         # centred <p> block (default: markdown)
    readme_badges.py --list                # every badge it knows how to build
    readme_badges.py --check               # report badges in README.md it cannot back
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

SHIELDS = "https://img.shields.io"

# Badges deliberately absent: stars, forks, followers, "made with", visitor
# counters. They report on the reader's social graph or on nothing, not on
# whether the software works.
CATALOG: Dict[str, dict] = {
    "ci": {
        "label": "CI",
        "img": SHIELDS + "/github/actions/workflow/status/{owner}/{repo}/{workflow}?branch={branch}&style={style}&label=CI",
        "href": "https://github.com/{owner}/{repo}/actions/workflows/{workflow}",
        "alt": "CI status",
        "needs": "workflow",
    },
    "coverage": {
        "label": "Coverage",
        "img": SHIELDS + "/codecov/c/github/{owner}/{repo}?style={style}",
        "href": "https://codecov.io/gh/{owner}/{repo}",
        "alt": "Test coverage",
        "needs": "coverage",
    },
    "license": {
        "label": "License",
        "img": SHIELDS + "/github/license/{owner}/{repo}?style={style}",
        "href": "LICENSE",
        "alt": "License",
        "needs": "license",
    },
    "version": {
        "label": "Version",
        "img": SHIELDS + "/github/v/tag/{owner}/{repo}?style={style}&label=version",
        "href": "https://github.com/{owner}/{repo}/tags",
        "alt": "Latest tag",
        "needs": None,
    },
    "release": {
        "label": "Release",
        "img": SHIELDS + "/github/v/release/{owner}/{repo}?style={style}",
        "href": "https://github.com/{owner}/{repo}/releases/latest",
        "alt": "Latest release",
        "needs": None,
    },
    "last-commit": {
        "label": "Last commit",
        "img": SHIELDS + "/github/last-commit/{owner}/{repo}?style={style}",
        "href": "https://github.com/{owner}/{repo}/commits/{branch}",
        "alt": "Last commit",
        "needs": None,
    },
    "npm": {
        "label": "npm",
        "img": SHIELDS + "/npm/v/{pkg}?style={style}",
        "href": "https://www.npmjs.com/package/{pkg}",
        "alt": "npm version",
        "needs": "npm",
    },
    "npm-downloads": {
        "label": "npm downloads",
        "img": SHIELDS + "/npm/dm/{pkg}?style={style}",
        "href": "https://www.npmjs.com/package/{pkg}",
        "alt": "npm downloads per month",
        "needs": "npm",
    },
    "pypi": {
        "label": "PyPI",
        "img": SHIELDS + "/pypi/v/{pkg}?style={style}",
        "href": "https://pypi.org/project/{pkg}/",
        "alt": "PyPI version",
        "needs": "pypi",
    },
    "python-versions": {
        "label": "Python",
        "img": SHIELDS + "/pypi/pyversions/{pkg}?style={style}",
        "href": "https://pypi.org/project/{pkg}/",
        "alt": "Supported Python versions",
        "needs": "pypi",
    },
    "crates": {
        "label": "crates.io",
        "img": SHIELDS + "/crates/v/{pkg}?style={style}",
        "href": "https://crates.io/crates/{pkg}",
        "alt": "crates.io version",
        "needs": "cargo",
    },
    "go": {
        "label": "Go reference",
        "img": SHIELDS + "/badge/pkg.go.dev-reference-blue?style={style}",
        "href": "https://pkg.go.dev/github.com/{owner}/{repo}",
        "alt": "Go package reference",
        "needs": "go",
    },
    "docker": {
        "label": "Docker",
        "img": SHIELDS + "/docker/image-size/{owner}/{repo}?style={style}",
        "href": "https://hub.docker.com/r/{owner}/{repo}",
        "alt": "Docker image size",
        "needs": "docker",
    },
    "issues": {
        "label": "Open issues",
        "img": SHIELDS + "/github/issues/{owner}/{repo}?style={style}",
        "href": "https://github.com/{owner}/{repo}/issues",
        "alt": "Open issues",
        "needs": None,
    },
}

# Ordered defaults: status first, then provenance. Four is the ceiling.
DEFAULT_ORDER = ("ci", "npm", "pypi", "crates", "coverage", "license",
                 "version", "last-commit")

STYLES = ("flat", "flat-square", "plastic", "for-the-badge", "social")


# ---------------------------------------------------------------------------
# Repository detection
# ---------------------------------------------------------------------------


def _git(root: Path, *args: str) -> Optional[str]:
    try:
        out = subprocess.run(["git", "-C", str(root), *args],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def detect(root: Path) -> dict:
    info: dict = {"owner": None, "repo": None, "branch": "main",
                  "workflow": None, "pkg": None, "needs": set()}

    remote = _git(root, "remote", "get-url", "origin")
    if remote:
        m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", remote.strip())
        if m:
            info["owner"], info["repo"] = m.group(1), m.group(2)
    if not info["repo"]:
        info["repo"] = root.name
        info["owner"] = info["owner"] or "OWNER"

    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    head = _git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    info["branch"] = (head.split("/")[-1] if head else branch) or "main"

    wf_dir = root / ".github" / "workflows"
    if wf_dir.is_dir():
        workflows = sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")))
        preferred = [w for w in workflows if w.stem in ("ci", "test", "tests", "build", "main")]
        chosen = (preferred or workflows)
        if chosen:
            info["workflow"] = chosen[0].name
            info["needs"].add("workflow")

    if any((root / n).is_file() for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")):
        info["needs"].add("license")

    pkg_json = root / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if not data.get("private"):
                info["pkg"] = data.get("name") or info["repo"]
                info["needs"].add("npm")
        except (ValueError, OSError):
            pass

    for name in ("pyproject.toml", "setup.cfg", "setup.py"):
        p = root / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'^\s*name\s*=\s*["\']?([A-Za-z0-9_.-]+)', text, re.MULTILINE)
            info["pkg"] = info["pkg"] or (m.group(1) if m else info["repo"])
            info["needs"].add("pypi")
            break

    cargo = root / "Cargo.toml"
    if cargo.is_file():
        text = cargo.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
        info["pkg"] = info["pkg"] or (m.group(1) if m else info["repo"])
        info["needs"].add("cargo")

    if (root / "go.mod").is_file():
        info["needs"].add("go")
    if any((root / n).is_file() for n in ("Dockerfile", "docker-compose.yml",
                                          "compose.yaml", "compose.yml")):
        info["needs"].add("docker")
    if any((root / n).exists() for n in ("codecov.yml", ".codecov.yml")) or \
            re.search(r"codecov", " ".join(p.name for p in (wf_dir.glob("*")
                                                            if wf_dir.is_dir() else []))):
        info["needs"].add("coverage")

    return info


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def build(keys: Sequence[str], info: dict, style: str, fmt: str) -> str:
    fields = {"owner": info["owner"], "repo": info["repo"], "branch": info["branch"],
              "workflow": info["workflow"] or "ci.yml", "pkg": info["pkg"] or info["repo"],
              "style": style}
    rows: List[str] = []
    for key in keys:
        spec = CATALOG.get(key)
        if not spec:
            continue
        img = spec["img"].format(**fields)
        href = spec["href"].format(**fields)
        alt = spec["alt"]
        if fmt == "html":
            rows.append('  <a href="%s"><img alt="%s" src="%s"></a>' % (href, alt, img))
        else:
            rows.append("[![%s](%s)](%s)" % (alt, img, href))
    if not rows:
        return ""
    if fmt == "html":
        return '<p align="center">\n' + "\n".join(rows) + "\n</p>"
    return "\n".join(rows)


def choose(info: dict, limit: int) -> List[str]:
    out: List[str] = []
    for key in DEFAULT_ORDER:
        spec = CATALOG[key]
        need = spec["needs"]
        if need and need not in info["needs"]:
            continue
        out.append(key)
        if len(out) >= limit:
            break
    return out


def check(readme: Path, info: dict) -> int:
    if not readme.is_file():
        print("readme-badges: no %s to check" % readme, file=sys.stderr)
        return 2
    text = readme.read_text(encoding="utf-8", errors="replace")
    problems: List[str] = []
    for m in re.finditer(r"https?://img\.shields\.io/[^\s)\"'>]+", text):
        url = m.group(0)
        if "actions/workflow" in url and "workflow" not in info["needs"]:
            problems.append("CI badge but no workflow file: %s" % url)
        if "/npm/" in url and "npm" not in info["needs"]:
            problems.append("npm badge but no package.json: %s" % url)
        if "/pypi/" in url and "pypi" not in info["needs"]:
            problems.append("PyPI badge but no Python manifest: %s" % url)
        if "codecov" in url and "coverage" not in info["needs"]:
            problems.append("coverage badge but no codecov config: %s" % url)
    styles = set(re.findall(r"img\.shields\.io[^\s)\"'>]*?style=([a-z-]+)", text))
    plain = len(re.findall(r"img\.shields\.io", text)) - sum(
        len(re.findall(r"style=" + s, text)) for s in styles)
    if len(styles) > 1 or (styles and plain > 0):
        problems.append("mixed badge styles: %s" % ", ".join(sorted(styles) or ["default"]))
    if not problems:
        print("readme-badges: every badge in %s is backed by this repo." % readme.name)
        return 0
    for p in problems:
        print("  ! %s" % p)
    return 1


def _force_utf8_stdout() -> None:
    """Never let a README's own characters crash the report.

    A Windows console defaults to cp1252, and this tool quotes heading text back
    at the reader - so an emoji heading (which HYG005 exists to flag) would kill
    the run that was about to flag it. Reconfiguring to UTF-8 with replacement
    keeps the same output on every platform, which is the tool's whole claim.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    _force_utf8_stdout()
    ap = argparse.ArgumentParser(prog="readme-badges",
                                 description="Build one consistent, linked badge row.")
    ap.add_argument("--root", default=".", help="repository root (default: .)")
    ap.add_argument("--style", choices=STYLES, default="flat-square")
    ap.add_argument("--format", choices=("markdown", "html"), default="html")
    ap.add_argument("--only", default="", help="comma-separated badge keys")
    ap.add_argument("--limit", type=int, default=4, help="max badges (default: 4)")
    ap.add_argument("--list", action="store_true", help="print the catalog and exit")
    ap.add_argument("--check", action="store_true",
                    help="report badges in README.md this repo cannot back")
    ap.add_argument("--json", action="store_true", help="print detection as JSON")
    args = ap.parse_args(argv)

    if args.list:
        print("%-16s %-12s %s" % ("KEY", "NEEDS", "WHAT IT REPORTS"))
        for key, spec in CATALOG.items():
            print("%-16s %-12s %s" % (key, spec["needs"] or "-", spec["alt"]))
        return 0

    root = Path(args.root).expanduser().resolve()
    info = detect(root)

    if args.json:
        out = dict(info)
        out["needs"] = sorted(info["needs"])
        print(json.dumps(out, indent=2))
        return 0

    if args.check:
        return check(root / "README.md", info)

    keys = ([k.strip() for k in args.only.split(",") if k.strip()]
            if args.only else choose(info, args.limit))
    block = build(keys, info, args.style, args.format)
    if not block:
        print("readme-badges: nothing to emit", file=sys.stderr)
        return 1
    print(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
