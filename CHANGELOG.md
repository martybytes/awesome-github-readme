# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-10-07

### Added

- `SECURITY.md` — the full threat model: what the scripts read, the `git`
  subprocesses, what the installer writes, running on untrusted input, the
  supply-chain trade-off in the generated CI job, and a hardening checklist.
- `docs/ci.md` — exit codes, how to ratchet a gate rather than turning on
  `--strict` and teaching everyone `|| true`, recipes for Actions, GitLab,
  Azure, Make and `pre-commit`, the `--json` contract, and a PR-comment job that
  keeps the gate on `contents: read`.
- README sections for continuous integration, security and troubleshooting.
- `.gitattributes` pinning LF in the working tree, marking the image fixtures
  binary and flagging `docs/rubric.md` as generated.
- `scripts/run_hook.sh` — the plugin's hooks start through it, and it picks
  whichever of `python3`, `python` or `py` actually runs.
- `HYG001` flags unfilled `{{...}}` template slots (not `${{ }}` expressions).
- `## Deploy` counts as the install section, which the service template uses.

### Changed

- `--user` installs copy `docs/` and `templates/` beside each skill, as well as
  `scripts/`, so the skills' references resolve outside a plugin install.
- `--project` re-runs keep the repository's `profile` and `strict` unless the
  flags are passed again.
- The `--ci` workflow takes its floor from `min_score` in
  `.awesome-readme.json` instead of a hard-coded `--min-score`, and runs with
  `contents: read` and a five-minute timeout.
- `docs/rubric.md` is generated in full, including the levels and
  disabling sections, and CI checks it for exact equality.
- `MEC006` no longer flags ```` ```console ```` blocks, which is the tag its fix
  recommends.
- The hook no longer lints `README.rst` or a bare `README` as Markdown.
- CI, the `--ci` workflow and the documented recipes use `actions/checkout@v7`
  and `actions/setup-python@v7`, which run on Node 24; the v4/v5 pair ran on
  the deprecated Node 20.

### Fixed

- **The install instructions named the wrong marketplace.** The marketplace is
  `martybytes`, so the command is `/plugin install awesome-github-readme@martybytes`,
  in both the README and `install.py --marketplace`.
- **Hooks did not start on many Windows machines.** The plugin called
  `python3`, which is often missing or the Store stub there, and `--user` /
  `--project` wrote unquoted backslash paths that Git Bash mangles.
- **The hook garbled non-ASCII paths on Windows**, by decoding stdin with the
  locale code page instead of UTF-8.
- **`git commit` detection** missed `git -C dir commit`, `git -c k=v commit` and
  a commit on a later line, matched `git commit-tree`, and skipped any commit
  whose message mentioned `--help`.
- **Anchors with underscores.** `github_slug` stripped `_` inside words, so a
  correct `#max_retries` link was reported dead and `readme_toc.py` wrote a
  broken one.
- **A UTF-8 BOM hid the H1**, and made `.awesome-readme.json` unreadable.
- **YAML front matter** was parsed as a setext heading.
- **Percent-encoded relative links** such as `My%20File.md` were reported dead.
- **`readme_toc.py --write`** rewrote TOC markers shown inside a code fence, and
  numbered duplicate anchors without counting headings outside `--max-depth`.
- **`--uninstall --user`** left the `readme-reviewer` agent behind.
- **GitHub's native Actions badge** (`/actions/workflows/<file>/badge.svg`) was
  not counted as a badge, and `MEC007` flagged URLs inside code spans.
- **The `--ci` workflow** truncated a branch name such as `feature/x` to `x`, as
  did the badge generator for the remote's default branch.
- **The licence badge** always linked to `LICENSE`, even when the file is
  `LICENSE.md` or `COPYING`.
- **The schema rejected `HERO00x` ids** in `disable`, including its own example.
- **`docs/SPEC.md`** had twelve dead contents links and a nested fence that
  closed early.
- **Docs corrections:** disabled rules leave the denominator (the README said
  they stayed in), the monorepo one-liner in `docs/ci.md` could not parse
  multi-line `--json`, and several counts and commands were wrong.

- **Superlinear parsing on hostile input.** Unbounded `[^\]]*` in the link and
  reference regexes rescanned to the end of the input from every `[`: 50,000
  unclosed brackets took 8.7 s, which is a denial of service for a linter that
  runs on pull requests from strangers. Bounding the character classes makes it
  0.18 s.
- **`MEC001` stat storm.** Link targets are now deduplicated before the
  filesystem call, so a README naming the same missing file 20,000 times costs
  one `exists()` rather than 20,000.
- **Generated files came out CRLF on Windows.** `Path.write_text` translates to
  `os.linesep`, so `install.py` wrote `.githooks/pre-commit` with a CRLF
  shebang, which fails under `sh` as `bad interpreter: /bin/sh^M`.
  `.gitattributes` governs what git checks out, not what Python writes, so a
  fresh clone looked clean while the installer still produced a broken hook.
  Every generation site now writes LF explicitly.
- **Link resolution escaped the repository.** `../../../etc/passwd` was resolved
  and probed; it is now reported as a finding instead. Correct as well as safe —
  GitHub serves relative links from the repository, so such a link is broken for
  every reader anyway.

## [1.0.0] - 2026-09-08

First release. Extracted from the
[terminal-stack](https://github.com/martybytes/terminal-stack) README, which is
the reference implementation and scores 98 against the rubric it produced.

### Added

- `readme_lint.py` — 40 rules across seven categories, six profiles, `--json`,
  `--strict`, `--min-score`, `--rules` and `--explain`. Python 3.9+, standard
  library only.
- `readme_badges.py` — badge row generator and `--check` verifier that emits
  only badges the repository can back.
- `readme_toc.py` — marker-delimited Contents list with `--write` and `--check`.
- `readme_hook.py` — advisory `PostToolUse`, `PreToolUse` and `SessionStart`
  hooks, with a per-repository strict mode.
- `install.py` — plugin, `~/.claude` and per-project install paths, plus
  `--status`, `--uninstall` and `--dry-run`.
- Five skills: `readme-init`, `readme-audit`, `readme-polish`, `readme-demo`,
  `readme-badges`.
- The `readme-reviewer` subagent, with no write tools.
- The written pattern: `docs/SPEC.md`, `docs/voice.md`, `docs/badges.md`,
  `docs/visuals.md`, `docs/antipatterns.md`, and the generated `docs/rubric.md`.
- Six profile templates and a commented `demo.tape`.
- JSON Schema for `.awesome-readme.json`.

[Unreleased]: https://github.com/martybytes/awesome-github-readme/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/martybytes/awesome-github-readme/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/martybytes/awesome-github-readme/releases/tag/v1.0.0
