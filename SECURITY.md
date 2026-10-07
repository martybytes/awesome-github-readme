# Security

This project runs on your machine on every file edit and before every commit,
and its generated CI job runs on pull requests from strangers. That earns you a
straight account of what it does, rather than a promise that it is safe.

- [What it can and cannot do](#what-it-can-and-cannot-do)
- [The hooks](#the-hooks)
- [What the installer writes](#what-the-installer-writes)
- [Running it on untrusted input](#running-it-on-untrusted-input)
- [Supply chain](#supply-chain)
- [Hardening checklist](#hardening-checklist)
- [Reporting a vulnerability](#reporting-a-vulnerability)

## What it can and cannot do

**No network access, at all.** No script in `scripts/` imports `urllib`, `http`,
`socket`, `requests`, `ssl`, `smtplib` or any other network module. Nothing is
uploaded, no telemetry is collected, and no badge URL is ever fetched —
`readme_badges.py --check` compares badge URLs against the working tree, it does
not request them. You can confirm this in one command:

```sh
grep -rE '^\s*(import|from)\s+(urllib|http|socket|requests|ssl|smtplib)' scripts/
```

**One subprocess, and it is `git`.** `readme_badges.py` runs
`git -C <root> remote get-url origin` and two `symbolic-ref` reads to fill in
the owner, repo and branch. It is passed as an argument list with a 10-second
timeout — never a shell string — so a repository name cannot inject a command. No
other script starts a process.

**What it reads:**

| File | Which script | Why |
|---|---|---|
| the README you point it at | all | the thing being linted |
| `.awesome-readme.json` | all | the profile and disabled rules |
| `package.json`, `pyproject.toml`, `setup.cfg`, `setup.py`, `Cargo.toml` | `readme_badges.py` | the package name for a package badge |
| `.github/workflows/*.y*ml` | `readme_badges.py` | filenames only, to pick a CI badge |

That is the complete list. Relative links named in the README are checked with a
`Path.exists()` call and never opened.

**Link resolution is confined to the repository.** A link resolving outside the
repo root is reported as a finding rather than probed, so a README written by
someone else cannot make your CI runner stat arbitrary paths and report back
which ones exist. This is also just correct: GitHub serves relative links from
the repository, so `../../elsewhere` is broken for every reader anyway.

**What it writes:** nothing, except `readme_toc.py --write` (which rewrites the
README you named) and `install.py` (see below). The linter and the hook never
write to disk.

## The hooks

Three registrations, all of which do the same thing — lint a README and return
text. None of them can read your source, your environment or your conversation.

| Event | Fires on | Does |
|---|---|---|
| `PostToolUse` | `Write`, `Edit`, `MultiEdit` | if the edited file is a README, lint it and return the findings as context. Silent above 95 with no errors |
| `PreToolUse` | `Bash` | if the command is a `git commit`, lint the repo README. Advisory unless the repo set `"strict": true` |
| `SessionStart` | session start | nothing, unless the repo set `"session_summary": true` |

They receive the hook event JSON on stdin and emit one JSON object on stdout.
The only field they populate is `additionalContext` — plus
`permissionDecision: "deny"` in strict mode, which is the one case where this
project can stop an action, and only for a repository that asked for it in a
file it committed.

Every hook is wrapped so that an unexpected failure exits 0 silently. A README
linter that breaks your session because of its own bug is worse than no linter.

**Kill switch**, no uninstall needed:

```sh
export AWESOME_README_HOOKS=0
```

## What the installer writes

`install.py` is the only component that writes outside its own directory.

**`--user`:**

| Path | What happens |
|---|---|
| `~/.claude/skills/readme-*/` | five skill directories, copied or symlinked |
| `~/.claude/agents/readme-reviewer.md` | copied |
| `~/.claude/settings.json` | **merged**, after a dated backup beside it |

The merge only ever replaces entries tagged `"_source": "awesome-github-readme"`.
Hooks you or another tool added are preserved, and `--uninstall --user` removes
exactly the tagged entries and leaves the rest.

**`--project PATH`** writes `.awesome-readme.json`, `.claude/settings.json`
(same tagged merge), and — only when asked — `.githooks/pre-commit` and
`.github/workflows/readme.yml`. It refuses to overwrite a `pre-commit` it did
not write, and never overwrites an existing workflow.

Preview any of it with `--dry-run`, which writes nothing.

Note that `.githooks/pre-commit` does nothing until someone runs
`git config core.hooksPath .githooks`. That is deliberate: a repository should
not be able to make your git run code just because you cloned it.

## Running it on untrusted input

The generated CI job lints the README from the pull request, which on a public
repo means input written by a stranger. Two things follow.

**Cost is bounded.** The link-matching character classes are capped
(`[^\]]{0,500}`), because unbounded ones rescan to the end of the input from
every `[` — 50,000 unclosed brackets cost 8.7 seconds before that bound and 0.18
seconds after. Link existence checks are deduplicated by target, so a README
naming the same missing file 20,000 times costs one filesystem call. Both are
pinned by tests in `tests/test_lint.py::test_pathological_input_stays_fast`.

The honest residual: a README with 50,000 *genuine* distinct links still takes
about 3 seconds, because that is real linear work. If that matters to you, run
the job with a step timeout.

**Nothing in a README is executed or fetched.** It is parsed with regular
expressions and reported on. Code fences are excluded from prose-level rules but
never run, and no URL in the document is requested.

**Findings quote the README back at you.** If you publish lint output —
in a PR comment, say — you are publishing fragments of that README. That is
normally the point, but it is worth knowing before you pipe `--json` into
something public.

## Supply chain

`install.py --project . --ci` generates a workflow that fetches the linter at run
time:

```yaml
- run: curl -fsSL -o .readme-tools/readme_lint.py
    https://raw.githubusercontent.com/martybytes/awesome-github-readme/main/scripts/readme_lint.py
```

**This trusts `main` of this repository at the moment your job runs.** It is
convenient and it is a real supply-chain dependency. Two better options:

1. **Vendor it.** `readme_lint.py` is one file with no dependencies. Copy it
   into your repo and commit it; then your CI runs a version you reviewed and
   `git log` shows every change to it.
2. **Pin a tag.** Replace `main` in the URL with a tag, so an upstream change
   cannot alter your gate without a commit on your side.

The repository ships no dependencies to install, which is a deliberate
security property and not only a convenience one: there is no lockfile to
audit, no transitive package to be compromised, and nothing that `pip install`
can substitute.

The Actions this project's own CI uses are pinned by major version
(`actions/checkout@v7`, `actions/setup-python@v7`). Pin them by commit SHA if
your threat model calls for it.

## Hardening checklist

For a repository that cares:

- [ ] Vendor `readme_lint.py` rather than curling it, or pin the URL to a tag.
- [ ] Pin third-party Actions by SHA.
- [ ] Give the README job `permissions: contents: read` — it needs nothing else.
- [ ] Use `pull_request`, not `pull_request_target`, so a fork's code never runs
      with your secrets.
- [ ] Add a step `timeout-minutes` if you lint READMEs from strangers.
- [ ] Review `.claude/settings.json` in repositories you clone before running an
      agent in them — that applies to any project-local hook, not just this one.

## Reporting a vulnerability

Open a [private security advisory](https://github.com/martybytes/awesome-github-readme/security/advisories/new).
Please do not open a public issue for anything exploitable.

Include what an attacker controls (a README, a repository name, a config file),
what they achieve, and a minimal reproduction. Expect an initial response within
a week.

**In scope:** command or path injection, anything that reads or writes outside
the documented set, a hook that can be made to block or alter an action it
should not, and denial of service from a crafted README that is materially worse
than the bounds documented above.

**Out of scope:** the linter disagreeing with you about your README, and the
`curl`-based CI workflow, which is documented above as a trust decision you make
knowingly.
