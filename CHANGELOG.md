# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [semantic versioning](https://semver.org/spec/v2.0.0.html).

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
