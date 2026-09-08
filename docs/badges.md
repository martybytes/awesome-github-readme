# Badges

A badge row is a status line, not decoration. Three questions decide whether a
badge belongs:

1. **Does it report live data?** A badge that renders the same thing forever is
   a coloured image.
2. **Can this repository back it?** A CI badge over a repo with no workflow is a
   broken claim on the first screen `TRU004`.
3. **Would a reader change their mind because of it?** "Build failing" changes a
   decision. "Made with love" does not.

Three to five badges, one `style=`, each wrapped in the link to the page it
reports on `HERO003`. Past five they stop being read as individual facts and
start being read as a texture.

## Build the row

```sh
python3 scripts/readme_badges.py                    # detect and print
python3 scripts/readme_badges.py --style flat       # any shields style
python3 scripts/readme_badges.py --format markdown  # instead of centred HTML
python3 scripts/readme_badges.py --only ci,license,version
python3 scripts/readme_badges.py --list             # the whole catalogue
python3 scripts/readme_badges.py --check            # badges this repo cannot back
```

It reads `git remote get-url origin` for owner and repo, then emits only what
the working tree supports: a CI badge when `.github/workflows/` has a workflow,
`npm`/`pypi`/`crates` when the matching manifest is there, a licence badge when
`LICENSE` exists. Nothing it emits is a guess.

## The catalogue

| Key | Reports | Needs in the repo |
|---|---|---|
| `ci` | whether the default branch builds | a workflow file |
| `coverage` | line coverage on the default branch | codecov config |
| `license` | the licence, from the repo's own metadata | a `LICENSE` file |
| `version` | the newest git tag | — |
| `release` | the newest GitHub release | — |
| `last-commit` | how long since the last commit | — |
| `npm` / `npm-downloads` | published version, downloads per month | `package.json`, not private |
| `pypi` / `python-versions` | published version, supported interpreters | a Python manifest |
| `crates` | published version | `Cargo.toml` |
| `go` | pkg.go.dev reference | `go.mod` |
| `docker` | image size | a Dockerfile or compose file |
| `issues` | open issue count | — |

`last-commit` deserves a note: it is the most honest badge available and the one
most projects avoid, because it is the one that tells a reader whether anything
here is maintained. That is a reason to include it, not to leave it out.

## Not in the catalogue, on purpose `HYG002`

| | Why |
|---|---|
| Stars, forks, watchers, followers | Reports on your social graph, not the software. A reader deciding whether it solves their problem learns nothing. |
| "Made with ❤️ / coffee / JavaScript" | No data. Marks the row as copied from a template, which discounts the badges beside it. |
| "PRs welcome", "Contributions welcome" | Belongs in `CONTRIBUTING.md`, where it can say what a good PR looks like. |
| Visitor / hit counters | Third-party tracking on every reader, for a number only you care about. |
| `awesome` / `for-the-badge` decorations | Style asserted, nothing measured. |
| "Maintained: yes" | Hand-set, never updated, and contradicted by `last-commit` the moment it goes stale. |

The vanity rule takes an escape hatch — `allow_badges` in `.awesome-readme.json`
exempts URL substrings — for the case where one of these genuinely earns its
place. Using it is fine; using it without a reason in the commit message is how
a template creeps back in.

## Styles

`flat-square` reads cleanest at small sizes and is this pattern's default.
`flat` is the shields.io default. `for-the-badge` shouts and is very hard to
scan in a row of four. `social` mimics GitHub's own buttons and belongs on the
star/fork badges this pattern does not use.

Whichever you pick, **pick one** `HERO003`. Mixed styles in a single row is the
most visible sign that a README was assembled rather than written, because the
badges are the first thing the eye lands on and mismatched heights are obvious
before any text is read.

## Custom badges

A static badge is legitimate when it reports a fact the repository really does
fix, and cannot be queried:

```markdown
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](pyproject.toml)
```

Link it to the file that proves it. An unlinked static badge is an assertion; a
linked one is a claim with a citation.

## Keeping the row honest

```sh
python3 scripts/readme_badges.py --check
```

catches the three ways a row rots: a CI badge whose workflow was deleted, a
package badge for a manifest that was removed, and a style that drifted when
somebody pasted a badge from another project. Run it in the same CI job as the
linter — it costs nothing and it is exactly the kind of breakage nobody notices
by reading.
