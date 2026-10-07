---
name: readme-audit
description: Score and review a README against the awesome-github-readme rubric — the mechanical checks a linter can make, plus the judgement calls it cannot. Use when asked to audit, review, grade, critique or "look at" a README, when asked whether a README is good, or before publishing a repository.
---

# readme-audit

Two passes. The linter finds every defect that has a rule; you find the ones
that need a reader. Report both as one prioritised list, because a maintainer
wants to know what to fix first, not which tool found it.

## Toolkit

Resolve this once. `$TOOLKIT` below is whichever of these exists:

Docs are in `$TOOLKIT/../docs/` and templates in `$TOOLKIT/../templates/`.
The commands below say `python3`; where that is missing, as it often is on
Windows, use `python` or `py -3`.

- plugin install — `${CLAUDE_PLUGIN_ROOT}/scripts`
- user install — the `scripts/` directory beside this `SKILL.md`

## Pass 1 — the mechanical check

```sh
python3 $TOOLKIT/readme_lint.py README.md --no-colour
python3 $TOOLKIT/readme_badges.py --check
```

If the repository has an `.awesome-readme.json`, the linter has already picked
up its profile and disabled rules. If it does not, look at the repository before
accepting the `cli` default — a package manifest with no entry point means
`library`, a Dockerfile and a compose file mean `service`, a repository that is
mostly Markdown means `docs`. Re-run with `--profile` when the default is wrong,
and say in the report which profile you scored against.

Do not paste the raw linter output into your report. It is input.

## Pass 2 — the judgement calls

Read the README yourself. The linter cannot evaluate any of this:

**The tagline.** Cover the title and read only the tagline. Can you say what
this is, who it is for, and how it differs from the obvious alternative? If not,
that is finding number one regardless of the score.

**The opening.** Does the first paragraph describe a problem the reader already
has, in their words — or does it describe the software? The second is the most
common defect in a well-scored README, and the linter cannot see it.

**Falsifiability.** Take each headline claim. Could a reader check it? "Handles
large files" is not checkable. "Streams, so a 4 GB input uses 12 MB of RAM" is.
Quote the worst two or three offenders verbatim; a quote lands where a category
does not.

**Rationale.** For each feature bullet, is there a clause saying what it beats or
what breaks without it? `DEP002` counts the hinges (`because`, `unlike`, `so
that`, `rather than`); you judge whether the reasons given are real ones.

**Honesty.** Does the README say what the project is *not* for, what it takes
over on the reader's machine, and where it is weak? A README with no admitted
limitation reads as marketing, and the reader discounts everything else in it.

**The first-command test.** Follow the install section literally, as someone who
has never seen the project. Where do you have to guess? Every guess is a defect,
and it is usually an unstated prerequisite or a step that assumes a directory
you were never told to create.

**Currency.** Does it document commands, flags or files that still exist? Spot
check three: grep the source for the entry point, check that a named config file
is in the tree, check that a linked document exists. Documentation drift is
invisible to a linter that only resolves links.

## Report

Lead with the score, then the findings ranked by how much each one costs a
reader — not by severity level, and not by rule id.

```
readme-audit — <repo>

  74/100 (grade C, profile cli)
  hero 22/34 · orientation 25/31 · onboarding 28/32 · mechanics 27/31 …

Fix first
  1. <finding> — <why it costs a reader something>
     <the concrete change, or the replacement sentence>
  2. …

Worth doing
  4. …

Optional
  <one line each>

What is already right
  <two or three, specifically — this is not padding, it stops a rewrite
   destroying the parts that work>
```

Rules for the report:

- **Rewrite, do not describe.** "The tagline is vague" is a complaint. Offering
  the replacement sentence is a fix. Do this for the tagline, the opening
  paragraph, and the two worst feature bullets, every time.
- **Quote what you criticise.** One line of the original beside your version.
- **Say what it costs.** Each finding names the reader who gives up because of
  it: the evaluator who cannot tell what this is, the adopter who cannot get it
  running, the contributor who cannot run the tests.
- **Cap it at ten findings.** A list of thirty is a list nobody starts.
- **Name what works.** Rewrites go wrong when the good parts were not identified
  first.

## After the report

Offer, in one line, to apply the fixes with `/readme-polish`. Do not start
rewriting the file as part of an audit — an audit that silently edits is one the
maintainer cannot check.

## Reference

- `$TOOLKIT/../docs/SPEC.md` — the pattern, block by block
- `$TOOLKIT/../docs/voice.md` — the prose rules pass 2 applies
- `$TOOLKIT/../docs/rubric.md` — every rule, its weight and its reason
- `python3 $TOOLKIT/readme_lint.py --explain <RULE>` — one rule's reasoning
