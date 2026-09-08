# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `SECURITY.md` — the full threat model: what the scripts read, the single
  `git` subprocess, what the installer writes, running on untrusted input, the
  supply-chain trade-off in the generated CI job, and a hardening checklist.
- `docs/ci.md` — exit codes, how to ratchet a gate rather than turning on
  `--strict` and teaching everyone `|| true`, recipes for Actions, GitLab,
  Azure, Make and `pre-commit`, the `--json` contract, and a PR-comment job that
  keeps the gate on `contents: read`.
- README sections for continuous integration, security and troubleshooting.

### Fixed

- **Superlinear parsing on hostile input.** Unbounded `[^\]]*` in the link and
  reference regexes rescanned to the end of the input from every `[`: 50,000
  unclosed brackets took 8.7 s, which is a denial of service for a linter that
  runs on pull requests from strangers. Bounding the character classes makes it
  0.18 s.
- **`MEC001` stat storm.** Link targets are now deduplicated before the
  filesystem call, so a README naming the same missing file 20,000 times costs
  one `exists()` rather than 20,000.
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

[1.0.0]: https://github.com/martybytes/awesome-github-readme/releases/tag/v1.0.0
