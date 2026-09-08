# Continuous integration

The linter is one dependency-free Python file that exits non-zero on demand, so
wiring it into a pipeline is a two-line job on any platform. The interesting
part is not the YAML — it is choosing a gate that people will not route around.

- [Exit codes](#exit-codes)
- [Choosing a gate](#choosing-a-gate)
- [GitHub Actions](#github-actions)
- [Pre-commit](#pre-commit)
- [Other platforms](#other-platforms)
- [The JSON contract](#the-json-contract)
- [Posting findings on a pull request](#posting-findings-on-a-pull-request)

## Exit codes

| Code | Means | When |
|---|---|---|
| `0` | ran, and did not fail a gate | always, unless a gate below trips |
| `1` | a gate failed | `--strict` with any `error` finding, or `--min-score N` under `N` |
| `2` | could not run | the file does not exist, or `--explain` named an unknown rule |

Without `--strict` or `--min-score`, the linter **always exits 0**. It reports
and gets out of the way; failing the build is something you opt into.

`readme_toc.py --check` and `readme_badges.py --check` exit `1` on drift and `0`
when current, with no flag needed — both are already checks rather than reports.

## Choosing a gate

Turning on `--strict` in an existing repository fails the first build and
teaches everyone to add `|| true`. Ratchet instead:

1. **Advisory.** Run the linter with no gate. The score appears in the log and
   nothing fails. Leave it a couple of weeks.
2. **A floor at today's score.** `--min-score 74` if you score 74. The build
   fails only if the README gets *worse*, which is the property that actually
   matters and the one nobody argues with.
3. **Raise the floor** as the score rises. Each bump is a commit, visible in
   history, agreed by whoever merges it.
4. **`--strict`** once error-level findings are all gone — dead links, missing
   licence, placeholder text. These are defects rather than opinions, so a gate
   on them stays uncontroversial.

Most repositories should stop at step 3. `--strict` is for repositories where a
broken README is a shipped defect — a template, a starter, a public SDK.

Put the choice in `.awesome-readme.json` so it is the repo's decision rather
than a flag someone typed once:

```json
{ "profile": "library", "min_score": 80, "strict": false }
```

Every entry point reads that same file, so the hook, the git hook and CI agree
without being told twice.

## GitHub Actions

`install.py --project . --ci` writes a working job. Both forms below are
equivalent apart from where the linter comes from.

**Vendored** — recommended. Commit `readme_lint.py` into your repo, and CI runs
a version you reviewed:

```yaml
name: readme

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: python tools/readme_lint.py README.md --no-colour --min-score 80
```

**Fetched** — no file to vendor, at the cost of trusting this repository at run
time. Pin a tag rather than `main`:

```yaml
      - name: Fetch readme-lint
        run: |
          mkdir -p .readme-tools
          curl -fsSL -o .readme-tools/readme_lint.py \
            https://raw.githubusercontent.com/martybytes/awesome-github-readme/v1.0.0/scripts/readme_lint.py
      - run: python .readme-tools/readme_lint.py README.md --no-colour --min-score 80
```

See [SECURITY.md § Supply chain](../SECURITY.md#supply-chain) for the trade-off.

Notes that matter:

- **`permissions: contents: read`.** The job needs nothing else. The default
  token is far broader.
- **`pull_request`, not `pull_request_target`.** The latter runs with your
  secrets against a fork's code.
- **`--no-colour`** keeps ANSI escapes out of the log. The linter also honours
  `NO_COLOR` and disables colour automatically when stdout is not a terminal.
- **`timeout-minutes`** if you lint READMEs from strangers.

Add the drift checks as separate steps so a failure names itself:

```yaml
      - run: python tools/readme_toc.py --check
      - run: python tools/readme_badges.py --check
```

## Pre-commit

**The generated git hook.** `install.py --project . --git-hook` writes
`.githooks/pre-commit`, which is advisory unless the repo set `"strict": true`.
It does nothing until someone opts in:

```sh
git config core.hooksPath .githooks
```

That step is deliberate — cloning a repository should not let it run code in
your git.

**The `pre-commit` framework**, if you already use it:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: readme-lint
        name: readme-lint
        entry: python tools/readme_lint.py
        language: system
        files: ^README\.md$
        pass_filenames: true
```

Add `args: [--min-score, '80']` once you are past the advisory stage.

## Other platforms

Nothing here is GitHub-specific; the linter needs a Python and a checkout.

**GitLab CI:**

```yaml
readme:
  image: python:3-slim
  script:
    - python tools/readme_lint.py README.md --no-colour --min-score 80
```

**Azure Pipelines:**

```yaml
- task: UsePythonVersion@0
  inputs: { versionSpec: '3.x' }
- script: python tools/readme_lint.py README.md --no-colour --min-score 80
```

**Make, as the local equivalent of the gate:**

```make
.PHONY: readme
readme:
	python3 tools/readme_lint.py README.md --min-score 80
	python3 tools/readme_toc.py --check
	python3 tools/readme_badges.py --check
```

A `make readme` that matches CI exactly is worth more than any of the YAML
above, because it is the thing people run before pushing.

## The JSON contract

`--json` emits one object. It is the interface for anything you build on top:

```json
{
  "version": "1.0.0",
  "path": "README.md",
  "profile": "cli",
  "score": 74,
  "grade": "C",
  "counts": { "error": 1, "warn": 3, "info": 5 },
  "categories": {
    "hero": { "earned": 22, "possible": 34 }
  },
  "passed": ["HERO001", "MEC003"],
  "findings": [
    {
      "rule": "MEC001",
      "level": "error",
      "message": "Dead relative link: docs/setup.md",
      "line": 42,
      "fix": "Fix the path or create the file."
    }
  ]
}
```

`--json` exits 0 regardless of findings unless you also pass a gate flag, so a
script can read the record and decide for itself.

Useful one-liners:

```sh
# the score alone, for a badge or a dashboard
python3 tools/readme_lint.py --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["score"])'

# every error, as "file:line: message"
python3 tools/readme_lint.py --json \
  | python3 -c 'import json,sys; [print("README.md:%d: %s" % (f["line"], f["message"])) for f in json.load(sys.stdin)["findings"] if f["level"]=="error"]'

# score every README in a monorepo
find . -name README.md -not -path '*/node_modules/*' \
  -exec python3 tools/readme_lint.py {} --json \; \
  | python3 -c 'import json,sys; [print("%3d  %s" % (r["score"], r["path"])) for r in map(json.loads, sys.stdin)]'
```

The `"file:line: message"` form is what GitHub, most editors and most log
scrapers already know how to parse.

## Posting findings on a pull request

The linter deliberately has no `--comment` flag: posting to a PR needs a token,
and a linter that wants a token is a linter with a much larger blast radius.
Compose it instead, from a job that already has the permission it needs:

```yaml
  comment:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.x' }
      - id: lint
        run: |
          python tools/readme_lint.py README.md --no-colour > report.txt || true
          echo "score=$(python tools/readme_lint.py --json \
            | python -c 'import json,sys; print(json.load(sys.stdin)["score"])')" >> "$GITHUB_OUTPUT"
      - run: gh pr comment "$PR" --body-file report.txt
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR: ${{ github.event.number }}
```

Keep this in a separate job from the gate. The gate should stay on
`contents: read`; only the job that comments needs `pull-requests: write`.

To annotate lines in the diff instead, emit the `file:line: message` form above
and let your existing problem matcher pick it up.
