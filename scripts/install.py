#!/usr/bin/env python3
"""install - wire awesome-github-readme into Claude Code, or into one project.

Python 3.9+, standard library only. Idempotent: safe to re-run, and every write
to a file it does not own is a merge with a dated backup beside it.

There are three ways in, and they do not conflict:

    install.py --marketplace     print the /plugin commands (the clean path)
    install.py --user            copy skills + hooks into ~/.claude directly
    install.py --project PATH    give one repository its own hooks and config

`--user` exists for people who do not want the plugin system in the loop; it
installs the same components to the same effect. `--project` is what puts a
rubric and a CI gate in a repository, so the standard travels with the code
rather than with whoever happens to be running Claude.

    install.py --project . --profile library --ci --git-hook
    install.py --uninstall --user
    install.py --status
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "awesome-github-readme"
MARKER = "awesome-github-readme"          # tags the hook entries we own

SKILLS = ("readme-init", "readme-audit", "readme-polish", "readme-demo", "readme-badges")

PROFILES = ("cli", "library", "service", "app", "docs", "minimal")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def say(msg: str, level: str = "") -> None:
    prefix = {"ok": "  ok   ", "add": "  +    ", "skip": "  -    ",
              "warn": "  !    ", "": "       "}[level]
    print(prefix + msg)


def backup(path: Path) -> Optional[Path]:
    if not path.is_file():
        return None
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = path.with_name("%s.bak.%s" % (path.name, stamp))
    shutil.copy2(path, dest)
    return dest


def read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except (ValueError, OSError):
        return {}


def write_json(path: Path, data: dict, dry: bool) -> None:
    text = json.dumps(data, indent=2) + "\n"
    if dry:
        say("would write %s" % path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(path, text)


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


def python_cmd() -> str:
    """The interpreter to put in a hook command, quoted for a shell."""
    exe = sys.executable or "python3"
    return '"%s"' % exe if " " in exe else exe


# ---------------------------------------------------------------------------
# Hook configuration
# ---------------------------------------------------------------------------


def hook_entries(script_ref: str) -> dict:
    """The three hook registrations, keyed by event.

    `script_ref` is either ${CLAUDE_PLUGIN_ROOT}/scripts/... for a plugin
    install, or an absolute path for a --user / --project install.
    """
    cmd = "%s %s" % (python_cmd(), script_ref)
    return {
        "PostToolUse": [{
            "matcher": "Write|Edit|MultiEdit|NotebookEdit",
            "hooks": [{"type": "command", "command": cmd, "timeout": 15}],
            "_source": MARKER,
        }],
        "PreToolUse": [{
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": cmd, "timeout": 15}],
            "_source": MARKER,
        }],
        "SessionStart": [{
            "hooks": [{"type": "command", "command": cmd, "timeout": 15}],
            "_source": MARKER,
        }],
    }


def merge_hooks(settings: dict, entries: dict) -> dict:
    """Replace our own entries, leave everyone else's alone."""
    hooks = settings.setdefault("hooks", {})
    for event, ours in entries.items():
        existing = [e for e in hooks.get(event, [])
                    if not (isinstance(e, dict) and e.get("_source") == MARKER)]
        hooks[event] = existing + ours
    return settings


def strip_hooks(settings: dict) -> dict:
    hooks = settings.get("hooks") or {}
    for event in list(hooks):
        kept = [e for e in hooks[event]
                if not (isinstance(e, dict) and e.get("_source") == MARKER)]
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if not hooks:
        settings.pop("hooks", None)
    return settings


# ---------------------------------------------------------------------------
# --marketplace
# ---------------------------------------------------------------------------


def do_marketplace() -> int:
    repo = PLUGIN_ROOT
    print("""
Install as a Claude Code plugin - the path that keeps updates working:

  From this clone:

    /plugin marketplace add %s
    /plugin install %s@%s

  From GitHub, once it is pushed:

    /plugin marketplace add martybytes/%s
    /plugin install %s@%s

  Then: /readme-audit, /readme-init, /readme-polish, /readme-demo, /readme-badges

The plugin registers its hooks itself; nothing needs to go into settings.json.
""" % (repo, PLUGIN_NAME, PLUGIN_NAME, PLUGIN_NAME, PLUGIN_NAME, PLUGIN_NAME))
    return 0


# ---------------------------------------------------------------------------
# --user
# ---------------------------------------------------------------------------


def claude_home() -> Path:
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(env).expanduser() if env else Path.home() / ".claude"


def do_user(dry: bool, link: bool) -> int:
    home = claude_home()
    skills_dir = home / "skills"
    say("target %s" % home)

    for name in SKILLS:
        src = PLUGIN_ROOT / "skills" / name
        if not src.is_dir():
            say("missing source skill %s" % name, "warn")
            continue
        dest = skills_dir / name
        if dry:
            say("would install skill %s" % name, "add")
            continue
        if dest.is_symlink() or dest.exists():
            if dest.is_symlink():
                dest.unlink()
            else:
                shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # A plugin skill reaches the toolkit through ${CLAUDE_PLUGIN_ROOT}, which
        # is not set for a ~/.claude skill. Every install shape therefore has to
        # end with a `scripts/` beside the SKILL.md, or the skill's own
        # instructions point at nothing.
        if link:
            try:
                dest.mkdir(parents=True)
                # Link the parts, not the directory: a linked skill directory
                # would have no scripts/ of its own, and the repo has none to
                # link to at that path.
                for entry in src.iterdir():
                    (dest / entry.name).symlink_to(
                        entry, target_is_directory=entry.is_dir())
                (dest / "scripts").symlink_to(PLUGIN_ROOT / "scripts",
                                              target_is_directory=True)
                say("linked skill %s" % name, "add")
                continue
            except OSError:
                say("symlink unavailable (needs Developer Mode on Windows), "
                    "copying %s" % name, "warn")
                if dest.exists():
                    shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(src, dest)
        shutil.copytree(PLUGIN_ROOT / "scripts", dest / "scripts",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        say("installed skill %s" % name, "add")

    agents_src = PLUGIN_ROOT / "agents"
    if agents_src.is_dir():
        for md in agents_src.glob("*.md"):
            dest = home / "agents" / md.name
            if dry:
                say("would install agent %s" % md.stem, "add")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md, dest)
            say("installed agent %s" % md.stem, "add")

    settings_path = home / "settings.json"
    settings = read_json(settings_path)
    hook_script = str(PLUGIN_ROOT / "scripts" / "readme_hook.py")
    if " " in hook_script:
        hook_script = '"%s"' % hook_script
    merged = merge_hooks(settings, hook_entries(hook_script))
    if not dry:
        b = backup(settings_path)
        if b:
            say("backed up settings.json -> %s" % b.name, "ok")
    write_json(settings_path, merged, dry)
    say("registered PostToolUse, PreToolUse and SessionStart hooks", "add")

    print("")
    say("Done. Start a new session, then run /readme-audit in any repository.")
    say("Set AWESOME_README_HOOKS=0 in the environment to silence the hooks.")
    return 0


# ---------------------------------------------------------------------------
# --project
# ---------------------------------------------------------------------------

GITHOOK = """#!/bin/sh
# awesome-github-readme: advisory README check before a commit.
# Never blocks unless .awesome-readme.json sets "strict": true.
set -e
README=$(ls README.md readme.md README.markdown 2>/dev/null | head -n 1) || exit 0
[ -n "$README" ] || exit 0
LINT="%s"
[ -f "$LINT" ] || exit 0
if grep -q '"strict"[[:space:]]*:[[:space:]]*true' .awesome-readme.json 2>/dev/null; then
  exec python3 "$LINT" "$README" --strict
fi
python3 "$LINT" "$README" || true
exit 0
"""

WORKFLOW = """name: readme

on:
  push:
    branches: [%(branch)s]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Fetch readme-lint
        run: |
          mkdir -p .readme-tools
          curl -fsSL -o .readme-tools/readme_lint.py \\
            https://raw.githubusercontent.com/martybytes/awesome-github-readme/main/scripts/readme_lint.py
      - name: Lint README
        run: python .readme-tools/readme_lint.py README.md --no-colour --min-score %(min_score)d
"""


def do_project(root: Path, profile: str, strict: bool, min_score: int,
               ci: bool, git_hook: bool, dry: bool) -> int:
    root = root.expanduser().resolve()
    if not root.is_dir():
        say("no such directory: %s" % root, "warn")
        return 2
    say("target %s" % root)

    # 1. The rubric config - the thing that makes the standard travel with the repo.
    cfg_path = root / ".awesome-readme.json"
    cfg = read_json(cfg_path)
    cfg.setdefault("$schema",
                   "https://raw.githubusercontent.com/martybytes/"
                   "awesome-github-readme/main/schema/awesome-readme.schema.json")
    cfg["profile"] = profile
    cfg["strict"] = strict
    if min_score:
        cfg["min_score"] = min_score
    cfg.setdefault("disable", [])
    cfg.setdefault("require", [])
    cfg.setdefault("allow_badges", [])
    write_json(cfg_path, cfg, dry)
    say("%s (profile %s, strict %s)" % (cfg_path.name, profile, str(strict).lower()), "add")

    # 2. Project-local hooks, so the check follows the repo not the machine.
    settings_path = root / ".claude" / "settings.json"
    settings = read_json(settings_path)
    hook_script = str(PLUGIN_ROOT / "scripts" / "readme_hook.py")
    if " " in hook_script:
        hook_script = '"%s"' % hook_script
    merged = merge_hooks(settings, hook_entries(hook_script))
    if not dry:
        b = backup(settings_path)
        if b:
            say("backed up .claude/settings.json -> %s" % b.name, "ok")
    write_json(settings_path, merged, dry)
    say(".claude/settings.json hooks registered", "add")

    # 3. Optional git pre-commit.
    if git_hook:
        hooks_dir = root / ".githooks"
        target = hooks_dir / "pre-commit"
        lint_path = str(PLUGIN_ROOT / "scripts" / "readme_lint.py")
        if dry:
            say("would write %s" % target, "add")
        else:
            hooks_dir.mkdir(parents=True, exist_ok=True)
            if target.is_file() and MARKER not in target.read_text(
                    encoding="utf-8", errors="replace"):
                say("%s exists and is not ours - left alone" % target, "warn")
            else:
                write_text_lf(target, GITHOOK % lint_path)
                target.chmod(target.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP)
                say(".githooks/pre-commit written", "add")
                say("enable it: git config core.hooksPath .githooks")

    # 4. Optional CI job.
    if ci:
        wf = root / ".github" / "workflows" / "readme.yml"
        branch = "main"
        head = root / ".git" / "HEAD"
        if head.is_file():
            text = head.read_text(encoding="utf-8", errors="replace").strip()
            if text.startswith("ref:"):
                branch = text.rsplit("/", 1)[-1]
        body = WORKFLOW % {"branch": branch, "min_score": min_score or 70}
        if dry:
            say("would write %s" % wf, "add")
        elif wf.is_file():
            say("%s exists - left alone" % wf.name, "skip")
        else:
            wf.parent.mkdir(parents=True, exist_ok=True)
            write_text_lf(wf, body)
            say(".github/workflows/readme.yml written", "add")

    print("")
    say("Done. Run: python3 %s %s"
        % (PLUGIN_ROOT / "scripts" / "readme_lint.py", root / "README.md"))
    return 0


# ---------------------------------------------------------------------------
# --uninstall / --status
# ---------------------------------------------------------------------------


def do_uninstall(user: bool, project: Optional[Path], dry: bool) -> int:
    if user:
        home = claude_home()
        for name in SKILLS:
            dest = home / "skills" / name
            if dest.is_symlink() or dest.exists():
                if dry:
                    say("would remove skill %s" % name, "skip")
                elif dest.is_symlink():
                    dest.unlink()
                    say("removed skill link %s" % name, "skip")
                else:
                    shutil.rmtree(dest)
                    say("removed skill %s" % name, "skip")
        sp = home / "settings.json"
        if sp.is_file():
            if not dry:
                backup(sp)
            write_json(sp, strip_hooks(read_json(sp)), dry)
            say("removed hooks from settings.json", "skip")
    if project:
        sp = project.expanduser().resolve() / ".claude" / "settings.json"
        if sp.is_file():
            if not dry:
                backup(sp)
            write_json(sp, strip_hooks(read_json(sp)), dry)
            say("removed hooks from %s" % sp, "skip")
    say("The .awesome-readme.json rubric is left in place; delete it by hand "
        "if you want the repo to forget its profile.")
    return 0


def do_status() -> int:
    home = claude_home()
    say("plugin root   %s" % PLUGIN_ROOT)
    say("claude home   %s" % home)
    installed = [n for n in SKILLS if (home / "skills" / n).exists()]
    say("skills        %s" % (", ".join(installed) if installed else "none in ~/.claude"))
    settings = read_json(home / "settings.json")
    events = [e for e, entries in (settings.get("hooks") or {}).items()
              if any(isinstance(x, dict) and x.get("_source") == MARKER for x in entries)]
    say("user hooks    %s" % (", ".join(events) if events else "not registered"))
    cwd_cfg = Path.cwd() / ".awesome-readme.json"
    if cwd_cfg.is_file():
        cfg = read_json(cwd_cfg)
        say("this repo     profile=%s strict=%s"
            % (cfg.get("profile", "cli"), cfg.get("strict", False)))
    else:
        say("this repo     no .awesome-readme.json (defaults to profile cli, advisory)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="install",
        description="Wire awesome-github-readme into Claude Code, or into one project.")
    ap.add_argument("--marketplace", action="store_true",
                    help="print the /plugin install commands and exit")
    ap.add_argument("--user", action="store_true",
                    help="install skills and hooks into ~/.claude")
    ap.add_argument("--link", action="store_true",
                    help="with --user, symlink the skills instead of copying")
    ap.add_argument("--project", metavar="PATH",
                    help="give one repository its own rubric, hooks and CI job")
    ap.add_argument("--profile", choices=PROFILES, default="cli")
    ap.add_argument("--strict", action="store_true",
                    help="with --project, make the commit gate blocking")
    ap.add_argument("--min-score", type=int, default=0,
                    help="with --project, the score CI requires")
    ap.add_argument("--ci", action="store_true",
                    help="with --project, add .github/workflows/readme.yml")
    ap.add_argument("--git-hook", action="store_true",
                    help="with --project, add .githooks/pre-commit")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.status:
        return do_status()
    if args.marketplace:
        return do_marketplace()
    if args.uninstall:
        return do_uninstall(args.user, Path(args.project) if args.project else None,
                            args.dry_run)
    if not (args.user or args.project):
        ap.print_help()
        print("")
        say("Nothing to do. Pick --marketplace, --user or --project PATH.")
        return 0

    rc = 0
    if args.user:
        rc |= do_user(args.dry_run, args.link)
    if args.project:
        rc |= do_project(Path(args.project), args.profile, args.strict,
                         args.min_score, args.ci, args.git_hook, args.dry_run)
    return rc


if __name__ == "__main__":
    sys.exit(main())
