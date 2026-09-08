---
name: readme-badges
description: Build or repair a README's badge row — three to five badges, one style, each linked and each backed by live data this repository can actually produce. Use when asked to add, fix, clean up or choose badges or shields for a README.
---

# readme-badges

A badge row is a status line, not decoration. Three questions decide whether a
badge belongs:

1. **Does it report live data?** A badge that renders the same thing forever is
   a coloured image.
2. **Can this repository back it?** A CI badge over a repo with no workflow is a
   broken claim on the first screen `TRU004`.
3. **Would a reader change their mind because of it?** "Build failing" changes a
   decision. "Made with love" does not.

## Toolkit

`$TOOLKIT` is `${CLAUDE_PLUGIN_ROOT}/scripts` (plugin install) or the `scripts/`
directory beside this `SKILL.md`.

## Build the row

```sh
python3 $TOOLKIT/readme_badges.py --json     # what this repo can back
python3 $TOOLKIT/readme_badges.py            # the row, centred HTML
```

The generator reads `git remote get-url origin` for owner and repo, then emits
only what the working tree supports — a CI badge when there is a workflow,
`npm`/`pypi`/`crates` when the matching manifest is there, a licence badge when
`LICENSE` exists. Nothing it emits is a guess, which is the whole point.

Options worth knowing:

```sh
--format markdown          # instead of the centred <p> block
--style flat               # flat-square is the default; pick one and keep it
--only ci,license,version  # override the detection
--limit 5                  # the ceiling, default 4
--list                     # the whole catalogue and what each one needs
```

## Repair an existing row

```sh
python3 $TOOLKIT/readme_badges.py --check
```

catches the three ways a row rots:

- a CI badge whose workflow was deleted or renamed,
- a package badge for a manifest that is gone,
- a style that drifted when somebody pasted a badge from another project.

Then read the row yourself for the things the checker cannot judge:

**Is every badge linked?** `HERO003`. A badge is a claim; the link is its
citation. An unlinked CI badge tells a reader the build failed and gives them
nowhere to find out why.

**Is every badge alt-texted?** `MEC003`. Five badges with no `alt` is five
instances of "image" in a row for anyone using a screen reader. The alt is the
badge's own claim: `alt="CI status"`, `alt="License: MIT"`.

**Are there more than five?** Past five they stop being read as individual facts
and become a texture. Keep the ones that would change a decision.

**Are any of them vanity?** `HYG002`.

## What to drop

| | Why |
|---|---|
| Stars, forks, watchers | Reports on your social graph, not the software. |
| "Made with ❤️ / coffee" | No data, and it discounts the badges beside it. |
| "PRs welcome" | Belongs in `CONTRIBUTING.md`, where it can say what a good PR looks like. |
| Visitor / hit counters | Third-party tracking on every reader, for a number only you see. |
| "Maintained: yes" | Hand-set, never updated, contradicted by `last-commit` the day it goes stale. |
| `for-the-badge` decorations | Style asserted, nothing measured. |

If one of these genuinely earns its place, exempt it explicitly rather than
silently:

```json
{ "allow_badges": ["forthebadge"] }
```

in `.awesome-readme.json`. The point is that the next person can see it was a
decision.

## What to consider adding

**`last-commit`** is the most honest badge available and the one most projects
avoid, because it is the one that tells a reader whether anything here is
maintained. That is a reason to include it.

**A static badge is legitimate** when it states a fact the repository really does
fix and that cannot be queried — a minimum runtime version, a platform set.
Link it to the file that proves it:

```markdown
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](pyproject.toml)
```

An unlinked static badge is an assertion. A linked one is a claim with a
citation.

## Place it

In the hero, between the tagline and the nav row, centred:

```html
<p align="center">
  <a href="https://github.com/OWNER/REPO/actions/workflows/ci.yml"><img alt="CI" src="…"></a>
  <a href="LICENSE"><img alt="License: MIT" src="…"></a>
  <a href="https://github.com/OWNER/REPO/tags"><img alt="Latest tag" src="…"></a>
</p>
```

Markdown headings ignore `align`; raw HTML honours it. That is why the hero is
HTML.

## Keep it honest

Add the check to whatever already runs on push — it costs nothing and catches
exactly the breakage nobody notices by reading:

```yaml
- run: python3 scripts/readme_badges.py --check
```

Full catalogue and reasoning: [badges.md](../../docs/badges.md).
