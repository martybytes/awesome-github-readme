#!/usr/bin/env python3
"""readme-lint - score a README against the awesome-github-readme rubric.

Python 3.9+, standard library only. Runs identically on Windows, WSL, Linux and
macOS, which is the point: the same score in CI as on a laptop, with nothing to
install first.

    readme_lint.py                      # lint ./README.md, human report
    readme_lint.py path/to/README.md    # lint a specific file
    readme_lint.py --json               # one JSON record, for scripts and hooks
    readme_lint.py --strict             # exit 1 when any error-level rule fails
    readme_lint.py --profile library    # use a different required-section set
    readme_lint.py --rules              # dump the rubric itself and exit
    readme_lint.py --explain HERO001    # what one rule wants, and why

Exit codes: 0 clean or advisory, 1 a rule failed under --strict, 2 unreadable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set
from urllib.parse import unquote

__version__ = "1.0.0"

ERROR = "error"
WARN = "warn"
INFO = "info"

_LEVEL_ORDER = {ERROR: 0, WARN: 1, INFO: 2}
_LEVEL_MARK = {ERROR: "x", WARN: "!", INFO: "i"}


# ---------------------------------------------------------------------------
# Parsed document
# ---------------------------------------------------------------------------


@dataclass
class Heading:
    level: int
    text: str
    line: int
    html: bool = False

    @property
    def slug(self) -> str:
        return github_slug(self.text)


@dataclass
class Link:
    text: str
    target: str
    line: int
    html: bool = False


@dataclass
class Image:
    alt: Optional[str]
    src: str
    line: int
    html: bool = False


@dataclass
class Fence:
    lang: str
    start: int
    end: int


@dataclass
class Doc:
    path: Path
    root: Path
    raw: str
    lines: List[str]
    headings: List[Heading] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    fences: List[Fence] = field(default_factory=list)
    prose: str = ""
    prose_lines: List[str] = field(default_factory=list)
    front_matter_end: int = 0                 # last line of a leading YAML block
    setext_underlines: Set[int] = field(default_factory=set)

    def in_fence(self, line: int) -> bool:
        return any(f.start <= line <= f.end for f in self.fences)

    @property
    def h1s(self) -> List[Heading]:
        return [h for h in self.headings if h.level == 1]

    @property
    def h2s(self) -> List[Heading]:
        return [h for h in self.headings if h.level == 2]

    def head(self, n_lines: int = 60) -> str:
        return "\n".join(self.lines[:n_lines])

    def section(self, key: str) -> Optional[Heading]:
        for h in self.headings:
            if h.level >= 2 and section_key_of(h.text) == key:
                return h
        return None

    def section_body(self, h: Heading) -> str:
        idx = self.headings.index(h)
        start = h.line
        end = len(self.lines)
        for nxt in self.headings[idx + 1:]:
            if nxt.level <= h.level:
                end = nxt.line - 1
                break
        return "\n".join(self.lines[start:end])

    @property
    def section_keys(self) -> Dict[str, Heading]:
        out: Dict[str, Heading] = {}
        for h in self.headings:
            if h.level < 2:
                continue
            key = section_key_of(h.text)
            if key and key not in out:
                out[key] = h
        return out


# ---------------------------------------------------------------------------
# Slugs and section vocabulary
# ---------------------------------------------------------------------------

_SLUG_STRIP = re.compile(r"[^\w\- ]", re.UNICODE)
# Emphasis markers, but not an underscore inside a word: GitHub keeps
# `max_retries` as-is in the anchor.
_MD_INLINE = re.compile(r"(\*\*|\*|`|~~|(?<!\w)_+|_+(?!\w))")


def write_text_lf(path: Path, text: str) -> None:
    """Write with LF endings whatever the platform.

    `Path.write_text` translates "\n" to `os.linesep`, so on Windows every
    file this project generates would come out CRLF - including
    `.githooks/pre-commit`, a POSIX `sh` script whose CRLF shebang fails as
    `bad interpreter: /bin/sh^M`. .gitattributes governs what git checks out,
    not what Python writes, so the fix has to be here as well as there.
    """
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def github_slug(text: str) -> str:
    """GitHub's heading -> anchor rule: lowercase, drop punctuation, spaces to hyphens."""
    t = re.sub(r"<[^>]+>", "", text)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = _MD_INLINE.sub("", t)
    t = t.strip().lower()
    t = _SLUG_STRIP.sub("", t)
    return t.replace(" ", "-")


SECTION_VOCAB: Dict[str, Sequence[str]] = {
    "contents": ("contents", "table of contents", "toc", "on this page", "index"),
    "what": ("what it is", "about", "overview", "introduction", "intro", "why",
             "what is this", "the problem", "motivation", "summary"),
    "requirements": ("requirements", "prerequisites", "prereqs", "before you start",
                     "supported platforms", "compatibility", "system requirements"),
    "install": ("install", "installation", "installing", "setup", "set up",
                "get started", "getting started", "deploy", "deployment",
                "deploying"),
    "quickstart": ("quickstart", "quick start", "usage", "using it", "examples",
                   "example", "basic usage", "first run", "try it", "api"),
    "config": ("config", "configuration", "configuring", "settings", "options",
               "customization", "customizing", "environment"),
    "features": ("what you get", "features", "capabilities", "what's included",
                 "whats included", "highlights", "what it does", "the tour"),
    "architecture": ("architecture", "how it works", "design", "internals",
                     "under the hood", "how it is built"),
    "development": ("development", "developing", "contributing", "contribute",
                    "hacking", "building from source", "for contributors", "tests"),
    "layout": ("layout", "project structure", "repository layout", "repo layout",
               "structure", "file tree", "directory layout"),
    "faq": ("faq", "troubleshooting", "common problems", "known issues",
            "questions", "gotchas"),
    "security": ("security", "reporting a vulnerability", "threat model"),
    "changelog": ("changelog", "releases", "history", "release notes"),
    "license": ("license", "licence", "licensing", "copyright"),
    "demo": ("demo", "screenshots", "screenshot", "in action", "preview"),
    "acknowledgements": ("acknowledgements", "acknowledgments", "credits",
                         "thanks", "prior art", "related"),
}

_VOCAB_INDEX: Dict[str, str] = {}
for _key, _phrases in SECTION_VOCAB.items():
    for _phrase in _phrases:
        _VOCAB_INDEX[_phrase] = _key

_VOCAB_BY_LEN = sorted(_VOCAB_INDEX.items(), key=lambda kv: -len(kv[0]))


def section_key_of(heading_text: str) -> Optional[str]:
    """Map a heading's text onto a canonical section key, or None."""
    t = re.sub(r"<[^>]+>", "", heading_text)
    t = _MD_INLINE.sub("", t).strip().lower()
    t = re.sub(r"[^a-z0-9 ']+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return None
    if t in _VOCAB_INDEX:
        return _VOCAB_INDEX[t]
    for phrase, key in _VOCAB_BY_LEN:
        if t.startswith(phrase + " "):
            return key
    words = set(t.split())
    for phrase, key in _VOCAB_BY_LEN:
        if " " not in phrase and phrase in words:
            return key
    return None


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_RE_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*([A-Za-z0-9_+#.-]*)")
_RE_ATX = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
_RE_HTML_H = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
# The {0,N} bounds are load-bearing, not cosmetic. Unbounded `[^\]]*` rescans to
# the end of the input from every `[`, so a README containing a run of unclosed
# brackets costs O(n^2) - 50k of them took 8.7s before these bounds, which is a
# denial of service for a linter that runs on pull requests from strangers.
# Nobody writes link text 500 characters long, so the bound costs nothing real.
_LINK_TEXT = r"[^\]]{0,500}"
_RE_MD_IMG = re.compile(r"!\[(" + _LINK_TEXT + r")\]\(\s*<?([^)>\s]{1,2000})>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
_RE_MD_LINK = re.compile(r"(?<!!)\[(" + _LINK_TEXT + r")\]\(\s*<?([^)>\s]{1,2000})>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
_RE_REF_DEF = re.compile(r"^\s{0,3}\[([^\]]{1,500})\]:\s*(\S+)")
_RE_REF_USE = re.compile(r"(?<!!)\[([^\]]{1,500})\]\[([^\]]{0,500})\]")
_RE_HTML_IMG = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
_RE_HTML_A = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_RE_ATTR = re.compile(r"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*[\"']([^\"']*)[\"']")


def _attrs(blob: str) -> Dict[str, str]:
    return {k.lower(): v for k, v in _RE_ATTR.findall(blob)}


def parse(path: Path, root: Path) -> Doc:
    # utf-8-sig: a BOM left on line 1 would hide the H1 from every rule.
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = raw.splitlines()
    doc = Doc(path=path, root=root, raw=raw, lines=lines)

    # YAML front matter is metadata, not content; GitHub renders it as a table.
    if lines and lines[0].strip() == "---":
        for j in range(1, min(len(lines), 200)):
            if lines[j].strip() in ("---", "..."):
                doc.front_matter_end = j + 1
                break

    # Fences first: everything else must know what to skip.
    fence_open: Optional[tuple] = None
    for i, line in enumerate(lines, start=1):
        m = _RE_FENCE.match(line)
        if not m:
            continue
        marker, lang = m.group(1), m.group(2)
        if fence_open is None:
            fence_open = (marker[0], len(marker), lang, i)
        elif marker[0] == fence_open[0] and len(marker) >= fence_open[1]:
            doc.fences.append(Fence(lang=fence_open[2], start=fence_open[3], end=i))
            fence_open = None
    if fence_open is not None:
        doc.fences.append(Fence(lang=fence_open[2], start=fence_open[3], end=len(lines)))

    prose_lines: List[str] = []
    for i, line in enumerate(lines, start=1):
        hidden = doc.in_fence(i) or i <= doc.front_matter_end
        prose_lines.append("" if hidden else line)
    doc.prose_lines = prose_lines
    doc.prose = "\n".join(prose_lines)

    # ATX headings
    for i, line in enumerate(lines, start=1):
        if doc.in_fence(i) or i <= doc.front_matter_end:
            continue
        m = _RE_ATX.match(line)
        if m:
            doc.headings.append(Heading(len(m.group(1)), m.group(2).strip(), i))
            continue
        # Setext: text on the previous line underlined with === or ---
        if i > 1 and re.match(r"^\s{0,3}(=+|-{2,})\s*$", line) and lines[i - 2].strip():
            prev = lines[i - 2]
            if not _RE_ATX.match(prev) and not doc.in_fence(i - 1) and prev.strip() != "":
                lvl = 1 if line.strip().startswith("=") else 2
                doc.headings.append(Heading(lvl, prev.strip(), i - 1))
                doc.setext_underlines.add(i)

    # HTML headings (centered hero titles live here)
    for m in _RE_HTML_H.finditer(doc.prose):
        line = doc.prose.count("\n", 0, m.start()) + 1
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        doc.headings.append(Heading(int(m.group(1)), text, line, html=True))

    doc.headings.sort(key=lambda h: (h.line, h.level))

    # Reference definitions
    refs: Dict[str, str] = {}
    for i, line in enumerate(prose_lines, start=1):
        m = _RE_REF_DEF.match(line)
        if m:
            refs[m.group(1).lower()] = m.group(2)

    def line_of(offset: int) -> int:
        return doc.prose.count("\n", 0, offset) + 1

    for m in _RE_MD_IMG.finditer(doc.prose):
        doc.images.append(Image(alt=m.group(1), src=m.group(2), line=line_of(m.start())))
    for m in _RE_MD_LINK.finditer(doc.prose):
        doc.links.append(Link(text=m.group(1), target=m.group(2), line=line_of(m.start())))
    for m in _RE_REF_USE.finditer(doc.prose):
        key = (m.group(2) or m.group(1)).lower()
        if key in refs:
            doc.links.append(Link(text=m.group(1), target=refs[key], line=line_of(m.start())))
    for m in _RE_HTML_IMG.finditer(doc.prose):
        a = _attrs(m.group(1))
        doc.images.append(Image(alt=a.get("alt"), src=a.get("src", ""),
                                line=line_of(m.start()), html=True))
    for m in _RE_HTML_A.finditer(doc.prose):
        a = _attrs(m.group(1))
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        doc.links.append(Link(text=text, target=a.get("href", ""),
                              line=line_of(m.start()), html=True))

    # Reference-style definitions are also link targets worth resolving.
    for name, target in refs.items():
        doc.links.append(Link(text=name, target=target, line=0))

    return doc


# ---------------------------------------------------------------------------
# Rule registry
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    rule: str
    level: str
    message: str
    line: int = 0
    fix: str = ""

    def as_dict(self) -> dict:
        return {"rule": self.rule, "level": self.level, "message": self.message,
                "line": self.line, "fix": self.fix}


@dataclass
class Rule:
    id: str
    category: str
    weight: int
    title: str
    why: str
    check: Callable[[Doc, "Config"], List[Finding]]
    profiles: Optional[Sequence[str]] = None   # None = all profiles

    def applies(self, profile: str) -> bool:
        return self.profiles is None or profile in self.profiles


RULES: List[Rule] = []

CATEGORIES = {
    "hero": "Hero - what a stranger sees in the first screenful",
    "orientation": "Orientation - what it is, who it is for, what it is not",
    "onboarding": "Onboarding - the path from zero to a working thing",
    "depth": "Depth - the reasons behind the features",
    "trust": "Trust - contribution, provenance, licence",
    "mechanics": "Mechanics - links, anchors, alt text, fences",
    "hygiene": "Hygiene - the things that make a README look assembled",
}

PROFILES = ("cli", "library", "service", "app", "docs", "minimal")


def rule(rid: str, category: str, weight: int, title: str, why: str,
         profiles: Optional[Sequence[str]] = None):
    def deco(fn: Callable[[Doc, "Config"], List[Finding]]) -> Callable:
        RULES.append(Rule(rid, category, weight, title, why, fn, profiles))
        return fn
    return deco


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_NAMES = (".awesome-readme.json", ".readme-rubric.json")

# Required sections per profile. Anything not listed is advisory, not scored
# as an error.
PROFILE_SECTIONS: Dict[str, Sequence[str]] = {
    "cli": ("what", "install", "quickstart", "config", "development", "license"),
    "library": ("what", "install", "quickstart", "development", "license"),
    "service": ("what", "requirements", "install", "config", "architecture", "license"),
    "app": ("what", "install", "quickstart", "license"),
    "docs": ("what", "contents", "development", "license"),
    "minimal": ("what", "install", "license"),
}


@dataclass
class Config:
    profile: str = "cli"
    strict: bool = False
    disable: Sequence[str] = ()
    require: Sequence[str] = ()
    allow_badges: Sequence[str] = ()
    min_score: int = 0
    check_links: bool = True
    session_summary: bool = False
    root: Path = field(default_factory=Path.cwd)

    @property
    def required_sections(self) -> Sequence[str]:
        base = list(PROFILE_SECTIONS.get(self.profile, PROFILE_SECTIONS["cli"]))
        for extra in self.require:
            if extra not in base:
                base.append(extra)
        return base

    @classmethod
    def load(cls, root: Path, **overrides) -> "Config":
        data: dict = {}
        for name in CONFIG_NAMES:
            p = root / name
            if p.is_file():
                try:
                    data = json.loads(p.read_text(encoding="utf-8-sig"))
                except (ValueError, OSError):
                    data = {}
                break
        cfg = cls(root=root)
        for key in ("profile", "strict", "disable", "require", "allow_badges",
                    "min_score", "check_links", "session_summary"):
            if key in data:
                setattr(cfg, key, data[key])
        for key, val in overrides.items():
            if val is not None:
                setattr(cfg, key, val)
        return cfg


# ---------------------------------------------------------------------------
# Helpers used by rules
# ---------------------------------------------------------------------------

BADGE_HOSTS = ("shields.io", "badgen.net", "badge.fury.io", "codecov.io",
               "coveralls.io", "circleci.com", "travis-ci", "app.netlify.com",
               "snyk.io", "deps.dev", "pkg.go.dev", "crates.io", "img.shields.io")

# Badge URLs encode spaces as %20 or _, so the separator class has to cover both.
_S = r"[-_ ]|%20"
VANITY_PATTERNS = (
    r"made(?:%s)with(?:%s)love" % (_S, _S),
    r"built(?:%s)with(?:%s)love" % (_S, _S),
    r"(?:made|built)(?:%s)with(?:%s)(?:heart|coffee|%%E2%%9D%%A4)" % (_S, _S),
    r"PRs?(?:%s)welcome" % _S,
    r"contributions(?:%s)welcome" % _S,
    r"awesome-+(?:badge-*)?brightgreen",
    r"hits\.", r"visitor", r"profile(?:%s)views" % _S,
    r"forthebadge", r"powered(?:%s)by" % _S,
    r"open(?:%s)source(?:%s)love" % (_S, _S),
    r"100%%25", r"uses(?:%s)badges" % _S, r"gluten(?:%s)free" % _S,
    r"badge/say-thanks", r"maintained-yes",
)

PLACEHOLDER_PATTERNS = (
    r"\bTODO\b", r"\bFIXME\b", r"\bTBD\b", r"lorem ipsum", r"\bXXX\b",
    r"your-project-name", r"YOUR_?USERNAME", r"<your[- ]", r"\[insert ",
    r"coming soon", r"under construction", r"project[-_ ]title",
    r"\bREPLACE_ME\b", r"example\.com/your",
    r"(?<![$\w])\{\{[^{}\n]*\}\}",        # template slots, not ${{ }} expressions
)

SUPERLATIVES = (
    "blazingly fast", "blazing fast", "lightning fast", "world-class",
    "cutting-edge", "state-of-the-art", "revolutionary", "game-changing",
    "next-generation", "ultimate", "seamlessly", "effortlessly", "robust and",
    "powerful and flexible", "one-stop", "best-in-class", "supercharge",
    "unleash", "simply the best",
)

_LEAD_VERBS = re.compile(
    r"^\s*[-*+]\s+\*\*([A-Z][a-z]+(?:s|es)?)\b", re.MULTILINE)


def is_badge(img: Image) -> bool:
    src = (img.src or "").lower()
    if re.search(r"/actions/workflows/[^/]+/badge\.svg", src):
        return True  # GitHub's native Actions badge; renders for private repos
    return any(h in src for h in BADGE_HOSTS)


def hero_line_count(doc: Doc) -> int:
    end = len(doc.lines)
    for h in doc.headings:
        if h.level == 2:
            end = h.line - 1
            break
    return min(end, 80)


def resolve_relative(doc: Doc, target: str) -> Optional[Path]:
    """Resolve a relative link, or None if it is not a path inside this repo.

    Confined to the repository root on purpose, and it is a correctness rule
    before it is a safety one: GitHub serves relative links from the repository,
    so `../../elsewhere` is already broken for every reader. Not walking out
    also means a README written by a stranger cannot make CI stat arbitrary
    paths on the runner and report back which ones exist.
    """
    t = target.split("#", 1)[0].split("?", 1)[0]
    if not t:
        return None
    # Decoded before the confinement check below, so %2e%2e is caught too.
    t = unquote(t).replace("\\", "/")
    try:
        if t.startswith("/"):
            resolved = (doc.root / t.lstrip("/")).resolve()
        else:
            resolved = (doc.path.parent / t).resolve()
        root = doc.root.resolve()
    except (OSError, ValueError, RuntimeError):
        return None
    if resolved != root and root not in resolved.parents:
        return None
    return resolved


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target)) or target.startswith("//")


# ---------------------------------------------------------------------------
# Rules: hero
# ---------------------------------------------------------------------------


@rule("HERO001", "hero", 6, "Exactly one H1 title",
      "GitHub renders the repo name above the README; a second H1 competes with "
      "it and breaks the outline that assistive tech and the sidebar TOC build.")
def _hero_title(doc: Doc, cfg: Config) -> List[Finding]:
    h1s = doc.h1s
    if not h1s:
        return [Finding("HERO001", ERROR, "No H1 title.",
                        fix="Add `# project-name` or a centered <h1 align=\"center\">.")]
    if len(h1s) > 1:
        return [Finding("HERO001", WARN,
                        "%d H1 headings; the rest of the document should use H2."
                        % len(h1s), line=h1s[1].line,
                        fix="Demote every H1 after the first to `##`.")]
    if h1s[0].line > 12:
        return [Finding("HERO001", WARN, "The H1 is %d lines down." % h1s[0].line,
                        line=h1s[0].line, fix="Move the title to the top.")]
    return []


@rule("HERO002", "hero", 8, "A one-sentence tagline directly under the title",
      "The tagline is the only thing that appears in search results and social "
      "cards. It must say what the thing is and who it is for without the title.")
def _hero_tagline(doc: Doc, cfg: Config) -> List[Finding]:
    if not doc.h1s:
        return []
    start = doc.h1s[0].line
    window = doc.lines[start:start + 14]
    for i, line in enumerate(window):
        stripped = re.sub(r"<[^>]+>", "", line).strip()
        stripped = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", stripped).strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("#"):
            break
        words = len(stripped.split())
        if words < 6:
            continue
        if words > 45:
            return [Finding("HERO002", WARN,
                            "The tagline runs %d words." % words,
                            line=start + i + 1,
                            fix="Cut it to one sentence, under 30 words.")]
        return []
    return [Finding("HERO002", ERROR, "No tagline under the title.",
                    line=start,
                    fix="Add one sentence saying what this is and who it is for.")]


@rule("HERO003", "hero", 6, "Three to five live badges, one style",
      "Badges are a status line, not decoration. Each one must resolve to live "
      "data; a wall of them buries the two that matter.")
def _hero_badges(doc: Doc, cfg: Config) -> List[Finding]:
    hero = hero_line_count(doc)
    badges = [i for i in doc.images if is_badge(i) and i.line <= hero]
    out: List[Finding] = []
    if not badges:
        return [Finding("HERO003", WARN, "No status badges in the hero.",
                        fix="Add CI, licence and version badges from one provider.")]
    if len(badges) > 7:
        out.append(Finding("HERO003", WARN,
                           "%d badges in the hero." % len(badges),
                           line=badges[0].line,
                           fix="Keep the three or four that carry live status."))
    styles = set()
    for b in badges:
        m = re.search(r"style=([a-z-]+)", b.src)
        styles.add(m.group(1) if m else "default")
    if len(styles) > 1:
        out.append(Finding("HERO003", WARN,
                           "Mixed badge styles: %s." % ", ".join(sorted(styles)),
                           line=badges[0].line,
                           fix="Pick one `style=` and use it on every badge."))
    unlinked = 0
    for b in badges:
        near = "\n".join(doc.lines[max(0, b.line - 3):b.line + 2])
        if "<a " not in near and "](" not in near.replace("![", ""):
            unlinked += 1
    if unlinked:
        out.append(Finding("HERO003", INFO,
                           "%d badge(s) are not wrapped in a link." % unlinked,
                           line=badges[0].line,
                           fix="Link each badge to the page it reports on."))
    return out


@rule("HERO004", "hero", 4, "A navigation row of in-page or sibling-doc links",
      "A reader who arrived for one thing should reach it without scrolling; the "
      "nav row is also what tells them the deeper docs exist.")
def _hero_nav(doc: Doc, cfg: Config) -> List[Finding]:
    hero = hero_line_count(doc)
    nav_lines: Dict[int, int] = {}
    for link in doc.links:
        if 0 < link.line <= hero:
            nav_lines[link.line] = nav_lines.get(link.line, 0) + 1
    dense = [n for n, count in nav_lines.items() if count >= 3]
    block = 0
    for line_no, count in nav_lines.items():
        window = sum(nav_lines.get(line_no + d, 0) for d in range(-2, 3))
        block = max(block, window)
    if dense or block >= 3:
        return []
    return [Finding("HERO004", INFO, "No navigation row in the hero.",
                    fix="Add a centered row: Install - Usage - Docs - Changelog.")]


@rule("HERO005", "hero", 8, "Visual proof above the fold",
      "A terminal recording, screenshot or diagram answers 'what does this "
      "actually do' faster than any paragraph, and proves the thing runs.")
def _hero_visual(doc: Doc, cfg: Config) -> List[Finding]:
    hero = hero_line_count(doc)
    visuals = [i for i in doc.images if not is_badge(i) and i.line <= hero]
    mermaid = any(f.lang.lower() == "mermaid" and f.start <= hero for f in doc.fences)
    if visuals or mermaid:
        return []
    return [Finding("HERO005", WARN, "No screenshot, GIF or diagram in the hero.",
                    fix="Record a demo (see templates/demo.tape) or add a diagram.")]


@rule("HERO006", "hero", 2, "A rule separating the hero from the body",
      "The hero is a different kind of content from the prose under it; a `---` "
      "is the cheapest way to say so.")
def _hero_rule(doc: Doc, cfg: Config) -> List[Finding]:
    hero = hero_line_count(doc)
    for i, line in enumerate(doc.lines[:hero], start=1):
        if (re.match(r"^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$", line) and not doc.in_fence(i)
                and i > doc.front_matter_end and i not in doc.setext_underlines):
            if i > 4:
                return []
    return [Finding("HERO006", INFO, "No horizontal rule closing the hero.",
                    fix="Add `---` between the hero block and the first H2.")]


# ---------------------------------------------------------------------------
# Rules: orientation
# ---------------------------------------------------------------------------


@rule("ORI001", "orientation", 8, "A 'what it is' section that opens on the problem",
      "Feature lists only mean something to a reader who already has the "
      "problem. Naming the problem first is what turns a stranger into a user.")
def _ori_what(doc: Doc, cfg: Config) -> List[Finding]:
    h = doc.section("what")
    if not h:
        return [Finding("ORI001", ERROR, "No 'What it is' / 'About' section.",
                        fix="Add an H2 that names the problem, then the solution.")]
    body = doc.section_body(h)
    words = len(re.sub(r"```.*?```", "", body, flags=re.DOTALL).split())
    if words < 40:
        return [Finding("ORI001", WARN,
                        "'%s' is %d words - too short to set up the problem."
                        % (h.text, words), line=h.line,
                        fix="Two short paragraphs: the pain, then what this does.")]
    return []


@rule("ORI002", "orientation", 6, "Verb-led capability bullets in parallel form",
      "'Installs / Configures / Updates / Diagnoses' scans in two seconds and "
      "forces each bullet to claim one concrete thing the software does.")
def _ori_verbs(doc: Doc, cfg: Config) -> List[Finding]:
    verbs = _LEAD_VERBS.findall(doc.prose)
    if len(verbs) >= 3:
        return []
    bullets = len(re.findall(r"^\s*[-*+]\s+", doc.prose, re.MULTILINE))
    if bullets < 3:
        return [Finding("ORI002", INFO, "No capability bullet list found.",
                        fix="Add 4-6 bullets, each opening with a bold verb.")]
    return [Finding("ORI002", INFO,
                    "Capability bullets do not open with parallel bold verbs.",
                    fix="Rewrite as **Installs** ... **Configures** ... **Updates** ...")]


@rule("ORI003", "orientation", 6, "An honest scope callout",
      "Saying what the project is not, and what it will take over on a user's "
      "machine, buys more trust than any feature bullet - and prevents the "
      "issue that starts 'this overwrote my config'.")
def _ori_scope(doc: Doc, cfg: Config) -> List[Finding]:
    if re.search(r">\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", doc.prose):
        return []
    return [Finding("ORI003", WARN, "No GitHub alert callout anywhere.",
                    fix="Add `> [!NOTE]` stating the scope, the limits and what "
                        "the project takes ownership of.")]


@rule("ORI004", "orientation", 3, "A table of contents once the page is long",
      "Past roughly six H2s the reader cannot see the shape of the page; the "
      "sidebar outline is one click away and easy to miss.")
def _ori_toc(doc: Doc, cfg: Config) -> List[Finding]:
    if len(doc.h2s) < 6 and len(doc.lines) < 200:
        return []
    if doc.section("contents"):
        return []
    anchors = [link for link in doc.links if link.target.startswith("#")]
    if len(anchors) >= max(4, len(doc.h2s) // 2):
        return []
    return [Finding("ORI004", INFO,
                    "%d H2 sections and no Contents list." % len(doc.h2s),
                    fix="Run `readme_toc.py --write` to insert one.")]


# ---------------------------------------------------------------------------
# Rules: onboarding
# ---------------------------------------------------------------------------


@rule("ONB001", "onboarding", 9, "An install section with a copy-pasteable command",
      "The single most common reason a reader leaves is that they could not "
      "find the one line that installs the thing.")
def _onb_install(doc: Doc, cfg: Config) -> List[Finding]:
    h = doc.section("install")
    if not h:
        return [Finding("ONB001", ERROR, "No Install / Getting started section.",
                        fix="Add an H2 with one fenced command per platform.")]
    body = doc.section_body(h)
    if "```" not in body:
        return [Finding("ONB001", ERROR,
                        "'%s' has no fenced code block." % h.text, line=h.line,
                        fix="Put the install command in a fenced block so it "
                            "gets a copy button.")]
    return []


@rule("ONB002", "onboarding", 7, "A quickstart that shows real commands and output",
      "Install proves it is on the machine. Quickstart proves it does something. "
      "They are different questions and need separate answers.")
def _onb_quickstart(doc: Doc, cfg: Config) -> List[Finding]:
    h = doc.section("quickstart")
    if not h:
        return [Finding("ONB002", WARN, "No Quickstart / Usage section.",
                        fix="Add an H2 with an annotated block of the first "
                            "commands a new user runs.")]
    body = doc.section_body(h)
    if "```" not in body:
        return [Finding("ONB002", WARN,
                        "'%s' has no fenced example." % h.text, line=h.line,
                        fix="Show the commands, with `#` comments explaining each.")]
    return []


@rule("ONB003", "onboarding", 5, "Requirements stated before the install command",
      "A reader whose platform is not supported should learn that in the "
      "requirements table, not from a failing installer.")
def _onb_requirements(doc: Doc, cfg: Config) -> List[Finding]:
    req = doc.section("requirements")
    inst = doc.section("install")
    if not req:
        if inst and re.search(r"\b(requires?|needs?|prerequisite)\b",
                              doc.section_body(inst), re.IGNORECASE):
            return []
        return [Finding("ONB003", INFO, "No Requirements / Prerequisites section.",
                        fix="Add a table: platform, what you need first, what the "
                            "installer adds.")]
    if inst and req.line > inst.line:
        return [Finding("ONB003", INFO,
                        "Requirements come after Install.", line=req.line,
                        fix="Move Requirements above Install.")]
    return []


@rule("ONB004", "onboarding", 4, "A way to verify the install worked",
      "'It printed a lot of text' is not success. A named check command turns "
      "a support thread into a one-line answer.")
def _onb_verify(doc: Doc, cfg: Config) -> List[Finding]:
    if re.search(r"\b(doctor|--version|verify|health ?check|status|--check|"
                 r"smoke test|self-test|selftest)\b", doc.prose, re.IGNORECASE):
        return []
    return [Finding("ONB004", INFO, "No verification step after install.",
                    fix="Add a `--version` or `doctor` command that proves the "
                        "install landed.")]


@rule("ONB005", "onboarding", 3, "A non-interactive path for scripts and CI",
      "Anything with a prompt eventually has to run unattended. Documenting the "
      "environment variables or flags that skip the prompts is what makes that "
      "possible without reading the source.",
      profiles=("cli", "service"))
def _onb_scripted(doc: Doc, cfg: Config) -> List[Finding]:
    if re.search(r"(non[- ]?interactive|unattended|headless|--yes|-y\b|"
                 r"ASSUME_YES|CI=1|scripted|silent install)",
                 doc.prose, re.IGNORECASE):
        return []
    return [Finding("ONB005", INFO, "No unattended / scripted install path.",
                    fix="Document the env vars or flags that answer every prompt.")]


@rule("ONB006", "onboarding", 4, "A configuration section with one-shot examples",
      "A menu screenshot tells a reader nothing they can paste. One-line "
      "examples of the settings people actually change do.",
      profiles=("cli", "service", "app", "library"))
def _onb_config(doc: Doc, cfg: Config) -> List[Finding]:
    h = doc.section("config")
    if not h:
        return [Finding("ONB006", INFO, "No Configuration section.",
                        fix="Add an H2 showing the three settings people change "
                            "most, as pasteable commands or a config snippet.")]
    if "```" not in doc.section_body(h) and "|" not in doc.section_body(h):
        return [Finding("ONB006", INFO,
                        "'%s' has neither an example nor a settings table."
                        % h.text, line=h.line,
                        fix="Show the commands or tabulate the keys.")]
    return []


# ---------------------------------------------------------------------------
# Rules: depth
# ---------------------------------------------------------------------------


@rule("DEP001", "depth", 6, "A feature tour that stays collapsed by default",
      "<details> lets one README serve the reader who wants three lines and the "
      "one who wants forty, without either scrolling past the other's content.")
def _dep_details(doc: Doc, cfg: Config) -> List[Finding]:
    count = len(re.findall(r"<details\b", doc.prose, re.IGNORECASE))
    if count == 0:
        if len(doc.lines) > 150:
            return [Finding("DEP001", INFO,
                            "%d lines and no <details> sections." % len(doc.lines),
                            fix="Collapse the feature tour and the per-platform "
                                "install blocks into <details>.")]
        return []
    if not re.search(r"<details\s+open", doc.prose, re.IGNORECASE):
        return [Finding("DEP001", INFO,
                        "Every <details> is collapsed; none is open.",
                        fix="Open the first one so the reader sees the pattern.")]
    return []


@rule("DEP002", "depth", 7, "Feature bullets that carry their reason",
      "'Sorts by newest child mtime, unlike ls -lt which buries it' is a reason "
      "to adopt. 'Fast sorting' is not. The rationale is the feature.")
def _dep_rationale(doc: Doc, cfg: Config) -> List[Finding]:
    markers = re.findall(
        r"\b(because|so that|which is what|unlike|otherwise|without which|"
        r"rather than|instead of|the reason|which means|so a |so the )",
        doc.prose, re.IGNORECASE)
    body_words = max(1, len(doc.prose.split()))
    density = len(markers) / (body_words / 500.0)
    if density >= 1.5:
        return []
    return [Finding("DEP002", WARN,
                    "Few rationale markers (%d in %d words)."
                    % (len(markers), body_words),
                    fix="For each headline feature add the clause that says what "
                        "it beats, or what breaks without it.")]


@rule("DEP003", "depth", 5, "An architecture summary that links to the long version",
      "Most readers want thirty seconds of how-it-works and a door to the rest. "
      "Putting the whole design in the README closes that door for everyone else.",
      profiles=("cli", "service", "library", "docs"))
def _dep_arch(doc: Doc, cfg: Config) -> List[Finding]:
    h = doc.section("architecture")
    if not h:
        return [Finding("DEP003", INFO, "No architecture / how-it-works section.",
                        fix="Add 'Architecture in 30 seconds' with a link to "
                            "ARCHITECTURE.md.")]
    body = doc.section_body(h)
    words = len(body.split())
    has_link = bool(re.search(r"\]\([^)]+\.md", body)) or "```mermaid" in body
    if words > 400 and not has_link:
        return [Finding("DEP003", INFO,
                        "The architecture section runs %d words with no link out."
                        % words, line=h.line,
                        fix="Summarise here, move the detail to ARCHITECTURE.md.")]
    return []


@rule("DEP004", "depth", 4, "An annotated layout tree",
      "One annotated tree replaces a dozen 'where does X live' questions and is "
      "the fastest orientation a first-time contributor can get.",
      profiles=("cli", "service", "library", "docs"))
def _dep_layout(doc: Doc, cfg: Config) -> List[Finding]:
    if doc.section("layout"):
        return []
    if re.search(r"[├└│]──", doc.raw):
        return []
    return [Finding("DEP004", INFO, "No repository layout tree.",
                    fix="Add a fenced tree with one comment per top-level entry.")]


@rule("DEP005", "depth", 3, "Paths: where the thing installs itself",
      "Software that writes outside its own directory owes the reader a table "
      "of exactly where.",
      profiles=("cli", "service", "app"))
def _dep_paths(doc: Doc, cfg: Config) -> List[Finding]:
    if re.search(r"(~/\.|\$HOME|%APPDATA%|%LOCALAPPDATA%|XDG_CONFIG_HOME|"
                 r"/etc/|/usr/local|AppData)", doc.prose):
        return []
    return [Finding("DEP005", INFO, "No paths documented.",
                    fix="Say where the config, cache and data land per platform.")]


# ---------------------------------------------------------------------------
# Rules: trust
# ---------------------------------------------------------------------------


@rule("TRU001", "trust", 6, "A development section with the exact gate commands",
      "A contributor should be able to reproduce CI locally by copying four "
      "lines. Prose about 'running the tests' is not that.")
def _tru_dev(doc: Doc, cfg: Config) -> List[Finding]:
    h = doc.section("development")
    if not h:
        return [Finding("TRU001", WARN, "No Development / Contributing section.",
                        fix="List the lint, type-check, format and test commands "
                            "CI runs, verbatim.")]
    if "```" not in doc.section_body(h):
        return [Finding("TRU001", INFO,
                        "'%s' has no commands." % h.text, line=h.line,
                        fix="Paste the exact commands, not a description of them.")]
    return []


@rule("TRU002", "trust", 4, "A licence section or link",
      "Without a stated licence the default is 'all rights reserved', which "
      "means nobody may legally use it.")
def _tru_license(doc: Doc, cfg: Config) -> List[Finding]:
    if doc.section("license"):
        return []
    if re.search(r"\b(MIT|Apache-?2|GPL|BSD|MPL|Unlicense|AGPL|ISC)\b", doc.prose):
        return [Finding("TRU002", INFO, "A licence is named but has no section.",
                        fix="Add a `## License` heading linking to LICENSE.")]
    return [Finding("TRU002", ERROR, "No licence stated.",
                    fix="Add `## License` with a link to the LICENSE file.")]


@rule("TRU003", "trust", 3, "Links out to the deeper documents",
      "CHANGELOG, ARCHITECTURE and the decision log are what let a reader "
      "check whether the project is maintained and why it is shaped this way.")
def _tru_docs(doc: Doc, cfg: Config) -> List[Finding]:
    targets = " ".join(link.target.lower() for link in doc.links)
    wanted = ("changelog", "contributing", "architecture", "decisions",
              "security", "docs/", "license")
    hits = sum(1 for w in wanted if w in targets)
    if hits >= 2:
        return []
    return [Finding("TRU003", INFO, "Few links to sibling documents.",
                    fix="Link CHANGELOG.md, CONTRIBUTING.md and the design notes.")]


@rule("TRU004", "trust", 3, "A CI badge backed by a workflow that exists",
      "A CI badge is a claim about the repository. If no workflow file backs "
      "it, it is a broken claim on the first screen.")
def _tru_ci(doc: Doc, cfg: Config) -> List[Finding]:
    ci_badges = [i for i in doc.images
                 if is_badge(i) and re.search(r"(workflow|actions|build|ci)", i.src, re.I)]
    wf_dir = doc.root / ".github" / "workflows"
    has_wf = wf_dir.is_dir() and any(wf_dir.glob("*.y*ml"))
    if ci_badges and not has_wf:
        return [Finding("TRU004", WARN,
                        "CI badge present but .github/workflows has no workflow.",
                        line=ci_badges[0].line,
                        fix="Add the workflow, or drop the badge.")]
    if has_wf and not ci_badges:
        return [Finding("TRU004", INFO, "Workflows exist but no CI badge.",
                        fix="Add the Actions status badge for the main workflow.")]
    return []


# ---------------------------------------------------------------------------
# Rules: mechanics
# ---------------------------------------------------------------------------


@rule("MEC001", "mechanics", 8, "Every relative link resolves to a file that exists",
      "A dead relative link is the most common README defect and the easiest to "
      "catch. It is also the one that most reliably makes a project look stale.")
def _mec_relative(doc: Doc, cfg: Config) -> List[Finding]:
    if not cfg.check_links:
        return []
    out: List[Finding] = []
    seen = set()
    for link in doc.links + [Link(i.alt or "", i.src, i.line) for i in doc.images]:
        t = link.target
        if not t or is_external(t) or t.startswith("#") or t.startswith("mailto:"):
            continue
        # Deduplicate BEFORE touching the filesystem: a README that references
        # the same path a thousand times should cost one stat, not a thousand.
        if t in seen:
            continue
        seen.add(t)
        p = resolve_relative(doc, t)
        if p is None:
            # Resolved outside the repository. GitHub serves relative links from
            # the repo, so this is already broken for every reader.
            out.append(Finding(
                "MEC001", ERROR,
                "Link points outside the repository: %s" % t, line=link.line,
                fix="GitHub cannot serve it. Use a path inside the repo, or an "
                    "absolute URL."))
            continue
        try:
            if p.exists():
                continue
        except OSError:
            # A path too long or otherwise unopenable for this OS is not a
            # finding worth reporting - it is not a link anyone typed.
            continue
        out.append(Finding("MEC001", ERROR, "Dead relative link: %s" % t,
                           line=link.line, fix="Fix the path or create the file."))
    return out


@rule("MEC002", "mechanics", 6, "Every in-page anchor matches a real heading",
      "Anchor links rot silently: rename a heading and the Contents entry still "
      "renders, still looks fine, and lands the reader at the top of the page.")
def _mec_anchors(doc: Doc, cfg: Config) -> List[Finding]:
    slugs: Dict[str, int] = {}
    valid = set()
    for h in doc.headings:
        s = h.slug
        n = slugs.get(s, 0)
        valid.add(s if n == 0 else "%s-%d" % (s, n))
        slugs[s] = n + 1
    for m in re.finditer(r'(?:id|name)\s*=\s*["\']([^"\']+)["\']', doc.prose):
        valid.add(m.group(1).lower())
    out: List[Finding] = []
    seen = set()
    for link in doc.links:
        if not link.target.startswith("#"):
            continue
        anchor = link.target[1:].lower()
        if not anchor or anchor in valid or anchor in seen:
            continue
        seen.add(anchor)
        out.append(Finding("MEC002", ERROR,
                           "Anchor #%s matches no heading." % anchor,
                           line=link.line,
                           fix="Use the slug of an existing heading."))
    return out


@rule("MEC003", "mechanics", 5, "Every image has alt text",
      "Alt text is what a screen reader announces and what renders when the "
      "asset 404s - which for a hero GIF is exactly when it matters.")
def _mec_alt(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    for img in doc.images:
        if img.alt is None or not img.alt.strip():
            label = img.src[:70] or "(no src)"
            out.append(Finding("MEC003", WARN, "Image without alt text: %s" % label,
                               line=img.line,
                               fix="Describe what the image shows, not that it is "
                                   "an image."))
    return out


@rule("MEC004", "mechanics", 4, "Every fenced block declares its language",
      "The language tag drives syntax highlighting and, on GitHub, whether the "
      "block gets a copy button that does not swallow the prompt character.")
def _mec_fence_lang(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    for f in doc.fences:
        if not f.lang:
            out.append(Finding("MEC004", WARN, "Fenced block with no language.",
                               line=f.start,
                               fix="Tag it: ```sh, ```powershell, ```json, ```text."))
    return out[:8]


@rule("MEC005", "mechanics", 3, "Heading levels do not skip",
      "H2 to H4 breaks the document outline that the sidebar and screen readers "
      "build from it.")
def _mec_heading_order(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    prev = 0
    for h in doc.headings:
        if prev and h.level > prev + 1:
            out.append(Finding("MEC005", WARN,
                               "H%d follows H%d: '%s'" % (h.level, prev, h.text[:40]),
                               line=h.line, fix="Use H%d." % (prev + 1)))
        prev = h.level
    return out[:5]


@rule("MEC006", "mechanics", 3, "Shell blocks are pasteable",
      "A `$` prompt in front of every command means a reader who uses the copy "
      "button pastes a script that does not run.")
def _mec_prompt_chars(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    for f in doc.fences:
        # `console` is excluded: it is the tag that says "prompts are shown".
        if f.lang.lower() not in ("sh", "bash", "zsh", "shell", ""):
            continue
        body = doc.lines[f.start:f.end - 1]
        cmds = [b for b in body if b.strip()]
        dollars = [b for b in cmds if b.lstrip().startswith("$ ")]
        if cmds and len(dollars) == len(cmds) and len(cmds) > 1:
            out.append(Finding("MEC006", INFO,
                               "Every line in this block is prefixed with `$ `.",
                               line=f.start,
                               fix="Drop the prompt, or tag the block ```console."))
    return out[:4]


@rule("MEC007", "mechanics", 2, "Bare URLs are linked",
      "A bare URL in prose cannot say where it goes, and wraps badly on narrow "
      "screens.")
def _mec_bare_urls(doc: Doc, cfg: Config) -> List[Finding]:
    linked = {link.target for link in doc.links}
    out = []
    for i, line in enumerate(doc.prose_lines, start=1):
        if line.lstrip().startswith(("[", "|")) or "](" in line or "href=" in line:
            continue
        line = re.sub(r"`[^`]*`", "", line)  # a URL in a code span is literal
        for m in re.finditer(r"(?<![(<\"'\w])https?://[^\s)>\"'\],]+", line):
            url = m.group(0)
            if url in linked:
                continue
            out.append(Finding("MEC007", INFO, "Bare URL: %s" % url[:60], line=i,
                               fix="Wrap it: [what it is](%s)" % url))
    return out[:4]


# ---------------------------------------------------------------------------
# Rules: hygiene
# ---------------------------------------------------------------------------


@rule("HYG001", "hygiene", 6, "No placeholder text left in",
      "TODO, lorem ipsum and `your-project-name` say the README was generated "
      "and never read - which is what the reader will assume about the code.")
def _hyg_placeholder(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    for i, line in enumerate(doc.prose_lines, start=1):
        for pat in PLACEHOLDER_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                out.append(Finding("HYG001", ERROR,
                                   "Placeholder text: %r" % m.group(0), line=i,
                                   fix="Replace it or delete the line."))
                break
    return out[:8]


@rule("HYG002", "hygiene", 4, "No vanity badges",
      "'Made with love' and 'PRs welcome' carry no data. They dilute the badges "
      "that do and mark the row as copied from a template.")
def _hyg_vanity(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    for img in doc.images:
        if not is_badge(img):
            continue
        if any(a in img.src for a in cfg.allow_badges):
            continue
        for pat in VANITY_PATTERNS:
            if re.search(pat, img.src, re.IGNORECASE):
                out.append(Finding("HYG002", WARN,
                                   "Vanity badge: %s" % img.src[:70], line=img.line,
                                   fix="Remove it; keep the badges backed by data."))
                break
    return out[:6]


@rule("HYG003", "hygiene", 4, "Claims are specific, not superlative",
      "'Blazingly fast' is unfalsifiable and therefore worthless. A number, a "
      "comparison or a named alternative is worth a paragraph of adjectives.")
def _hyg_superlatives(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    lowered = doc.prose.lower()
    for word in SUPERLATIVES:
        idx = lowered.find(word)
        if idx >= 0:
            line = doc.prose.count("\n", 0, idx) + 1
            out.append(Finding("HYG003", WARN, "Unfalsifiable claim: %r" % word,
                               line=line,
                               fix="Replace with a number, a benchmark or the "
                                   "alternative it beats."))
    return out[:6]


@rule("HYG004", "hygiene", 2, "One bullet marker throughout",
      "Mixed `-` and `*` markers are invisible on GitHub and loud in every diff "
      "and every other Markdown renderer.")
def _hyg_markers(doc: Doc, cfg: Config) -> List[Finding]:
    markers = set()
    for line in doc.prose_lines:
        m = re.match(r"^\s{0,3}([-*+])\s+\S", line)
        if m:
            markers.add(m.group(1))
    if len(markers) > 1:
        return [Finding("HYG004", INFO,
                        "Mixed bullet markers: %s" % " ".join(sorted(markers)),
                        fix="Normalise to `-`.")]
    return []


@rule("HYG005", "hygiene", 3, "Headings are words, not emoji",
      "Emoji in headings change the generated anchor, break every link to it, "
      "and render as tofu in half the terminals that show Markdown.")
def _hyg_emoji_headings(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    emoji = re.compile("[\U0001F000-\U0001FAFF☀-➿️⬀-⯿]")
    for h in doc.headings:
        if emoji.search(h.text):
            out.append(Finding("HYG005", INFO,
                               "Emoji in heading: %s" % h.text[:40], line=h.line,
                               fix="Move it into the body, or drop it."))
    return out[:5]


@rule("HYG006", "hygiene", 3, "The page stays inside a readable length",
      "Past roughly 500 lines the README has become the manual, and the reader "
      "who needed the first screen has to scroll through the rest.")
def _hyg_length(doc: Doc, cfg: Config) -> List[Finding]:
    n = len(doc.lines)
    if n > 700:
        return [Finding("HYG006", WARN, "%d lines." % n,
                        fix="Move reference material into docs/ and link to it.")]
    if n < 25:
        return [Finding("HYG006", WARN, "%d lines - too thin to orient anyone." % n,
                        fix="Cover what it is, install, usage and licence at least.")]
    return []


@rule("HYG007", "hygiene", 2, "Absolute self-links use relative paths",
      "A hard-coded https://github.com/owner/repo/blob/main/... link breaks on "
      "every fork, every branch and every mirror. Relative links do not.")
def _hyg_selflinks(doc: Doc, cfg: Config) -> List[Finding]:
    out = []
    seen = set()
    for link in doc.links:
        m = re.match(r"https?://github\.com/[^/]+/[^/]+/(?:blob|tree)/[^/]+/(.+)",
                     link.target)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(Finding("HYG007", INFO,
                               "Absolute self-link: %s" % link.target[:70],
                               line=link.line,
                               fix="Use the relative path `%s`." % m.group(1)))
    return out[:5]


# ---------------------------------------------------------------------------
# Section requirements (profile-driven)
# ---------------------------------------------------------------------------


@rule("SEC001", "orientation", 8, "Every section this profile requires is present",
      "The profile encodes what a reader of this kind of project comes looking "
      "for. A missing section is a question the README refuses to answer.")
def _sec_required(doc: Doc, cfg: Config) -> List[Finding]:
    present = doc.section_keys
    out = []
    for key in cfg.required_sections:
        if key not in present:
            example = SECTION_VOCAB.get(key, (key,))[0].title()
            out.append(Finding("SEC001", ERROR,
                               "Profile '%s' requires a '%s' section." % (cfg.profile, key),
                               fix="Add `## %s`." % example))
    return out


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


@dataclass
class Report:
    path: str
    profile: str
    score: int
    grade: str
    findings: List[Finding]
    passed: List[str]
    weights: Dict[str, Dict[str, int]]

    def as_dict(self) -> dict:
        return {
            "version": __version__,
            "path": self.path,
            "profile": self.profile,
            "score": self.score,
            "grade": self.grade,
            "counts": {
                "error": sum(1 for f in self.findings if f.level == ERROR),
                "warn": sum(1 for f in self.findings if f.level == WARN),
                "info": sum(1 for f in self.findings if f.level == INFO),
            },
            "categories": self.weights,
            "passed": self.passed,
            "findings": [f.as_dict() for f in self.findings],
        }


def grade_of(score: int) -> str:
    for cutoff, label in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= cutoff:
            return label
    return "F"


def run(doc: Doc, cfg: Config) -> Report:
    findings: List[Finding] = []
    passed: List[str] = []
    weights: Dict[str, Dict[str, int]] = {}

    for r in RULES:
        if r.id in cfg.disable or not r.applies(cfg.profile):
            continue
        bucket = weights.setdefault(r.category, {"earned": 0, "possible": 0})
        bucket["possible"] += r.weight
        try:
            got = r.check(doc, cfg) or []
        except Exception as exc:                      # a rule must never fail the run
            got = [Finding(r.id, INFO, "rule crashed: %s" % exc)]
        blocking = [f for f in got if f.level in (ERROR, WARN)]
        if not got:
            bucket["earned"] += r.weight
            passed.append(r.id)
        elif not blocking:
            bucket["earned"] += int(round(r.weight * 0.6))
        findings.extend(got)

    possible = sum(b["possible"] for b in weights.values()) or 1
    earned = sum(b["earned"] for b in weights.values())
    score = int(round(100.0 * earned / possible))

    findings.sort(key=lambda f: (_LEVEL_ORDER[f.level], f.rule, f.line))
    return Report(str(doc.path), cfg.profile, score, grade_of(score),
                  findings, passed, weights)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _colour(enabled: bool):
    if not enabled:
        return lambda s, _c: s
    codes = {"red": "31", "yellow": "33", "blue": "36", "green": "32",
             "dim": "2", "bold": "1"}
    return lambda s, c: "\033[%sm%s\033[0m" % (codes.get(c, "0"), s)


def render(report: Report, cfg: Config, colour: bool = True) -> str:
    C = _colour(colour)
    out: List[str] = []
    bar_width = 28
    filled = int(round(report.score / 100.0 * bar_width))
    bar = "#" * filled + "." * (bar_width - filled)
    tone = "green" if report.score >= 85 else "yellow" if report.score >= 65 else "red"

    out.append("")
    out.append("  %s  %s" % (C("readme-lint", "bold"), C(report.path, "dim")))
    out.append("  %s  %s  %s"
               % (C(bar, tone), C("%d/100" % report.score, "bold"),
                  C("grade %s - profile %s" % (report.grade, report.profile), "dim")))
    out.append("")

    for cat, label in CATEGORIES.items():
        b = report.weights.get(cat)
        if not b:
            continue
        out.append("  %-12s %3d/%-3d  %s"
                   % (cat, b["earned"], b["possible"], C(label, "dim")))
    out.append("")

    if not report.findings:
        out.append("  %s Nothing to fix." % C("ok", "green"))
        out.append("")
        return "\n".join(out)

    by_level: Dict[str, List[Finding]] = {ERROR: [], WARN: [], INFO: []}
    for f in report.findings:
        by_level[f.level].append(f)

    for level, tone in ((ERROR, "red"), (WARN, "yellow"), (INFO, "blue")):
        group = by_level[level]
        if not group:
            continue
        out.append("  %s" % C("%s (%d)" % (level.upper(), len(group)), tone))
        for f in group:
            loc = C(":%d" % f.line, "dim") if f.line else ""
            out.append("    %s %s%s  %s"
                       % (C(_LEVEL_MARK[level], tone), C(f.rule, "dim"), loc, f.message))
            if f.fix:
                out.append("        %s %s" % (C("->", "dim"), C(f.fix, "dim")))
        out.append("")

    out.append("  %s" % C("readme_lint.py --explain <RULE>  for the reasoning", "dim"))
    out.append("")
    return "\n".join(out)


RUBRIC_HEADER = """\
<!-- Generated by: python3 scripts/readme_lint.py --rules > docs/rubric.md -->
<!-- Do not edit by hand; edit the rule definitions in scripts/readme_lint.py. -->
"""

RUBRIC_FOOTER = """
## Levels

| Level | Effect on the score | Effect on `--strict` |
|---|---|---|
| `error` | the rule's full weight is lost | exit 1 |
| `warn` | the rule's full weight is lost | — |
| `info` | 40% of the rule's weight is lost | — |

A rule that produces only `info` findings still earns most of its weight, which
is why a good README lands in the nineties rather than at 100. The last few
points are suggestions, not defects.

## Turning a rule off

```json
{ "disable": ["HERO005", "DEP004"] }
```

in `.awesome-readme.json`. Disabled rules leave the denominator, so switching
off a rule you fail raises the score. That is the reason the list lives in a
committed file, where the next person can see the decision.

`readme_lint.py --explain <RULE>` prints the reasoning behind any single rule."""


def render_rules() -> str:
    out = [RUBRIC_HEADER, "# readme-lint rubric (v%s)" % __version__, ""]
    total = sum(r.weight for r in RULES)
    out.append("%d rules, %d weighted points." % (len(RULES), total))
    out.append("")
    for cat, label in CATEGORIES.items():
        rules = [r for r in RULES if r.category == cat]
        if not rules:
            continue
        out.append("## %s" % label)
        out.append("")
        out.append("| Rule | Weight | Profiles | Wants |")
        out.append("|---|---|---|---|")
        for r in sorted(rules, key=lambda x: x.id):
            prof = "all" if r.profiles is None else ", ".join(r.profiles)
            out.append("| `%s` | %d | %s | %s |" % (r.id, r.weight, prof, r.title))
        out.append("")
    out.append(RUBRIC_FOOTER)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


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


def find_root(start: Path) -> Path:
    cur = start if start.is_dir() else start.parent
    for candidate in [cur, *cur.parents]:
        if (candidate / ".git").exists():
            return candidate
        if any((candidate / n).is_file() for n in CONFIG_NAMES):
            return candidate
    return cur


def main(argv: Optional[Sequence[str]] = None) -> int:
    _force_utf8_stdout()
    ap = argparse.ArgumentParser(
        prog="readme-lint",
        description="Score a README against the awesome-github-readme rubric.")
    ap.add_argument("path", nargs="?", default=None,
                    help="README file or a directory holding one (default: ./README.md)")
    ap.add_argument("--profile", choices=PROFILES, default=None)
    ap.add_argument("--json", action="store_true", help="one JSON record on stdout")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when any error-level rule fails")
    ap.add_argument("--min-score", type=int, default=None,
                    help="exit 1 below this score")
    ap.add_argument("--disable", default="", help="comma-separated rule ids to skip")
    ap.add_argument("--no-links", action="store_true",
                    help="skip relative-link existence checks")
    ap.add_argument("--no-colour", "--no-color", dest="no_colour", action="store_true")
    ap.add_argument("--rules", action="store_true", help="print the rubric and exit")
    ap.add_argument("--explain", metavar="RULE", help="explain one rule and exit")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)

    if args.rules:
        print(render_rules())
        return 0

    if args.explain:
        rid = args.explain.upper()
        for r in RULES:
            if r.id == rid:
                print("\n%s  [%s, weight %d]\n" % (r.id, r.category, r.weight))
                print("  %s\n" % r.title)
                for line in _wrap(r.why, 74):
                    print("  %s" % line)
                print("")
                return 0
        print("No such rule: %s" % rid, file=sys.stderr)
        return 2

    target = Path(args.path).expanduser() if args.path else Path("README.md")
    if target.is_dir():
        for name in ("README.md", "readme.md", "README.markdown", "README.rst"):
            if (target / name).is_file():
                target = target / name
                break
    if not target.is_file():
        print("readme-lint: cannot read %s" % target, file=sys.stderr)
        return 2

    root = find_root(target.resolve())
    cfg = Config.load(
        root,
        profile=args.profile,
        strict=True if args.strict else None,
        check_links=False if args.no_links else None,
    )
    if args.disable:
        cfg.disable = list(cfg.disable) + [d.strip().upper()
                                           for d in args.disable.split(",") if d.strip()]
    if args.min_score is not None:
        cfg.min_score = args.min_score

    doc = parse(target.resolve(), root)
    report = run(doc, cfg)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        colour = (not args.no_colour) and sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
        sys.stdout.write(render(report, cfg, colour))

    has_error = any(f.level == ERROR for f in report.findings)
    if cfg.strict and has_error:
        return 1
    if cfg.min_score and report.score < cfg.min_score:
        return 1
    return 0


def _wrap(text: str, width: int) -> List[str]:
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main())
