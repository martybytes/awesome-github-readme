#!/usr/bin/env python3
"""readme-toc - build or refresh a README's Contents list.

Python 3.9+, standard library only.

The list is written between two HTML comment markers so a rebuild is a diff of
the entries and nothing else:

    <!-- toc -->
    - [Install](#install)
    <!-- /toc -->

If the markers are absent, `--write` inserts them under an existing
`## Contents` heading, or creates that heading before the first content H2.

    readme_toc.py                     # print the list
    readme_toc.py --write             # update README.md in place
    readme_toc.py --check             # exit 1 if the file is out of date
    readme_toc.py --min-depth 2 --max-depth 3
    readme_toc.py --style nav         # a single centred `A - B - C` row
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readme_lint import Doc, Heading, github_slug, parse, find_root  # noqa: E402

BEGIN = "<!-- toc -->"
END = "<!-- /toc -->"

# Headings that describe the page rather than living on it.
SKIP_SLUGS = {"contents", "table-of-contents", "toc", "on-this-page", "index"}


def collect(doc: Doc, min_depth: int, max_depth: int,
            skip: Sequence[str] = ()) -> List[Tuple[int, str, str]]:
    """(depth, text, anchor) for each heading in range, with duplicates numbered."""
    seen: dict = {}
    out: List[Tuple[int, str, str]] = []
    for h in doc.headings:
        if h.html or h.level < min_depth or h.level > max_depth:
            continue
        slug = h.slug
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        anchor = slug if n == 0 else "%s-%d" % (slug, n)
        if slug in SKIP_SLUGS or slug in skip:
            continue
        text = re.sub(r"<[^>]+>", "", h.text).strip()
        out.append((h.level, text, anchor))
    return out


def render_list(entries, min_depth: int) -> str:
    lines = []
    for depth, text, anchor in entries:
        indent = "  " * (depth - min_depth)
        lines.append("%s- [%s](#%s)" % (indent, text, anchor))
    return "\n".join(lines)


def render_nav(entries, limit: int = 6) -> str:
    top = [e for e in entries if e[0] == min(x[0] for x in entries)][:limit]
    parts = ["<a href=\"#%s\">%s</a>" % (a, t) for _, t, a in top]
    return "<p align=\"center\">\n  " + " &middot;\n  ".join(parts) + "\n</p>"


def splice(raw: str, block: str) -> Tuple[str, bool]:
    """Replace the region between the markers. Returns (text, changed)."""
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
    new_region = "%s\n\n%s\n\n%s" % (BEGIN, block, END)
    if pattern.search(raw):
        out = pattern.sub(lambda _m: new_region, raw, count=1)
        return out, out != raw

    lines = raw.splitlines()
    # Under an existing Contents heading?
    for i, line in enumerate(lines):
        if re.match(r"^\s{0,3}#{2,3}\s+", line) and github_slug(
                re.sub(r"^\s{0,3}#+\s+", "", line)) in SKIP_SLUGS:
            j = i + 1
            while j < len(lines) and not re.match(r"^\s{0,3}#{1,6}\s+", lines[j]):
                j += 1
            body = lines[:i + 1] + ["", new_region, ""] + lines[j:]
            return "\n".join(body) + "\n", True

    # Otherwise: a new Contents heading before the second H2.
    h2s = [i for i, line in enumerate(lines) if re.match(r"^\s{0,3}##\s+", line)]
    at = h2s[1] if len(h2s) > 1 else (h2s[0] if h2s else len(lines))
    body = lines[:at] + ["## Contents", "", new_region, ""] + lines[at:]
    return "\n".join(body) + "\n", True


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
    ap = argparse.ArgumentParser(prog="readme-toc",
                                 description="Build or refresh a README's Contents list.")
    ap.add_argument("path", nargs="?", default="README.md")
    ap.add_argument("--write", action="store_true", help="update the file in place")
    ap.add_argument("--check", action="store_true", help="exit 1 if out of date")
    ap.add_argument("--min-depth", type=int, default=2)
    ap.add_argument("--max-depth", type=int, default=2)
    ap.add_argument("--style", choices=("list", "nav"), default="list")
    ap.add_argument("--skip", default="", help="comma-separated slugs to omit")
    args = ap.parse_args(argv)

    target = Path(args.path).expanduser()
    if target.is_dir():
        target = target / "README.md"
    if not target.is_file():
        print("readme-toc: cannot read %s" % target, file=sys.stderr)
        return 2

    root = find_root(target.resolve())
    doc = parse(target.resolve(), root)
    skip = [s.strip().lower() for s in args.skip.split(",") if s.strip()]
    entries = collect(doc, args.min_depth, args.max_depth, skip)

    if not entries:
        print("readme-toc: no headings between H%d and H%d"
              % (args.min_depth, args.max_depth), file=sys.stderr)
        return 0

    block = (render_nav(entries) if args.style == "nav"
             else render_list(entries, args.min_depth))

    if not (args.write or args.check):
        print(block)
        return 0

    new_text, changed = splice(doc.raw, block)
    if args.check:
        if changed:
            print("readme-toc: %s is out of date - run --write" % target, file=sys.stderr)
            return 1
        print("readme-toc: %s is current" % target)
        return 0

    if changed:
        target.write_text(new_text, encoding="utf-8")
        print("readme-toc: updated %s (%d entries)" % (target, len(entries)))
    else:
        print("readme-toc: %s already current" % target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
