#!/usr/bin/env python3
"""readme-hook - the advisory guard behind awesome-github-readme.

One script, three events, driven by the `hook_event_name` in the JSON on stdin:

  PostToolUse  (Write|Edit|MultiEdit)  a README was just edited -> lint it and
                                       hand the findings back as context.
  PreToolUse   (Bash)                  a `git commit` is about to run -> lint the
                                       repo README. Advisory unless the project
                                       opted into `"strict": true`.
  SessionStart                         report the score once, if the project
                                       opted into `"session_summary": true`.

Advisory is the default everywhere. The hook writes context, never a veto,
until a repository explicitly asks for a gate - because a README linter that
blocks a commit on somebody else's machine is a linter people uninstall.

Exit code is always 0 except under `strict`, where a PreToolUse with
error-level findings returns a deny decision (still exit 0; the decision does
the blocking, so the reason text reaches the model intact).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from readme_lint import (Config, ERROR, WARN, find_root, parse, run)  # noqa: E402
except Exception:                                   # never break the session
    sys.exit(0)

README_NAMES = ("readme.md", "readme.markdown", "readme.rst", "readme")
MAX_FINDINGS = 8

# `git commit` but not `git commit --help`, and not a commit inside a longer
# read-only pipeline such as `git log --format=... commit`.
_COMMIT_RE = re.compile(r"(^|[;&|]\s*)git\s+(?:-[^\s]+\s+|--\S+\s+)*commit\b")


def emit(event: str, context: str = "", decision: str = "",
         reason: str = "", system: str = "") -> None:
    payload = {"hookEventName": event}
    if context:
        payload["additionalContext"] = context
    if decision:
        payload["permissionDecision"] = decision
        payload["permissionDecisionReason"] = reason
    if system:
        payload["systemMessage"] = system
    print(json.dumps({"hookSpecificOutput": payload}))
    sys.exit(0)


def quiet() -> None:
    sys.exit(0)


def enabled() -> bool:
    return os.environ.get("AWESOME_README_HOOKS", "1").lower() not in (
        "0", "off", "false", "no")


def find_readme(root: Path) -> Optional[Path]:
    for entry in sorted(root.iterdir()) if root.is_dir() else []:
        if entry.is_file() and entry.name.lower() in README_NAMES:
            return entry
    p = root / "README.md"
    return p if p.is_file() else None


def is_readme(path: str) -> bool:
    return Path(path).name.lower() in README_NAMES


def summarise(report, cfg, limit: int = MAX_FINDINGS) -> str:
    blocking = [f for f in report.findings if f.level in (ERROR, WARN)]
    head = "readme-lint: %d/100 (grade %s, profile %s) for %s" % (
        report.score, report.grade, report.profile, Path(report.path).name)
    if not blocking:
        infos = len(report.findings)
        tail = " %d optional suggestion(s)." % infos if infos else " Nothing to fix."
        return head + " -" + tail

    lines: List[str] = [head, ""]
    for f in blocking[:limit]:
        loc = ":%d" % f.line if f.line else ""
        lines.append("  [%s] %s%s  %s" % (f.level, f.rule, loc, f.message))
        if f.fix:
            lines.append("        fix: %s" % f.fix)
    extra = len(blocking) - limit
    if extra > 0:
        lines.append("  ... and %d more; run readme_lint.py for the full report." % extra)
    lines.append("")
    lines.append("Advisory only. Fix these when you touch the README next, or run "
                 "the /readme-polish skill. Do not stop the current task for them.")
    return "\n".join(lines)


def lint(path: Path, profile_override: Optional[str] = None):
    root = find_root(path.resolve())
    cfg = Config.load(root, profile=profile_override)
    doc = parse(path.resolve(), root)
    return run(doc, cfg), cfg


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def on_post_tool_use(data: dict) -> None:
    tool_input = data.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("path") or ""
    if not target or not is_readme(target):
        quiet()
    p = Path(target)
    if not p.is_file():
        quiet()
    try:
        report, cfg = lint(p)
    except Exception:
        quiet()
    if report.score >= 95 and not any(f.level == ERROR for f in report.findings):
        quiet()
    emit("PostToolUse", context=summarise(report, cfg))


def on_pre_tool_use(data: dict) -> None:
    if (data.get("tool_name") or "") != "Bash":
        quiet()
    command = ((data.get("tool_input") or {}).get("command") or "")
    if not _COMMIT_RE.search(command) or "--help" in command:
        quiet()

    cwd = Path(data.get("cwd") or ".")
    root = find_root(cwd.resolve())
    readme = find_readme(root)
    if readme is None:
        emit("PreToolUse", context=(
            "readme-lint: this repository has no README. A repo without one is "
            "the first thing a visitor cannot recover from - offer to create it "
            "with the /readme-init skill after the commit."))
    try:
        report, cfg = lint(readme)
    except Exception:
        quiet()

    errors = [f for f in report.findings if f.level == ERROR]
    if cfg.strict and errors:
        detail = "\n".join("  %s%s  %s" % (f.rule, ":%d" % f.line if f.line else "",
                                           f.message) for f in errors[:MAX_FINDINGS])
        emit("PreToolUse", decision="deny", reason=(
            "readme-lint is in strict mode for this repository and %s has %d "
            "error-level finding(s):\n%s\n\nFix these, or set \"strict\": false in "
            ".awesome-readme.json, then commit again."
            % (readme.name, len(errors), detail)))

    if report.score >= 90 and not errors:
        quiet()
    emit("PreToolUse", context=summarise(report, cfg))


def on_session_start(data: dict) -> None:
    cwd = Path(data.get("cwd") or ".")
    root = find_root(cwd.resolve())
    readme = find_readme(root)
    if readme is None:
        quiet()
    try:
        report, cfg = lint(readme)
    except Exception:
        quiet()
    if not getattr(cfg, "session_summary", False):
        quiet()
    emit("SessionStart", context=summarise(report, cfg, limit=4))


HANDLERS = {
    "PostToolUse": on_post_tool_use,
    "PreToolUse": on_pre_tool_use,
    "SessionStart": on_session_start,
}


def main() -> int:
    if not enabled():
        return 0
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return 0
    handler = HANDLERS.get(data.get("hook_event_name") or "")
    if handler is None:
        return 0
    try:
        handler(data)
    except SystemExit:
        raise
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
