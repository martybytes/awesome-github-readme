---
name: readme-polish
description: Rewrite an existing README to the awesome-github-readme pattern, preserving every fact already in it. Use when asked to improve, fix, rewrite, restructure, clean up or "make better" a README, or to apply the findings from a readme-audit.
---

# readme-polish

The facts in an existing README were written by someone who knew the project.
Your job is to restructure and sharpen, not to replace. **Every concrete fact in
the original survives into the new one** — a version number, a path, a caveat, a
flag, a platform note. If a fact does not fit the new structure, the structure
bends.

What you delete is filler: adjectives with nothing behind them, sentences that
would fit any project, and duplication.

## Toolkit

`$TOOLKIT` is `${CLAUDE_PLUGIN_ROOT}/scripts` (plugin install) or the `scripts/`
directory beside this `SKILL.md` (user install).

Docs are in `$TOOLKIT/../docs/` and templates in `$TOOLKIT/../templates/`.
The commands below say `python3`; where that is missing, as it often is on
Windows, use `python` or `py -3`.

## 1. Inventory before you touch anything

Read the whole file and write down, for yourself:

- Every **fact**: a command, a path, a version, a platform, a flag, a caveat, a
  known limitation, a name.
- Every **link**, in and out.
- Every **image**, and whether the file exists.
- The **claims** — the sentences asserting something about quality or speed.

The inventory is the contract. When you are done, walk it and confirm each fact
survived. This is the step that separates a polish from a rewrite that quietly
drops the one caveat that mattered.

## 2. Baseline

```sh
python3 $TOOLKIT/readme_lint.py README.md --no-colour --json > /tmp/readme-before.json
python3 $TOOLKIT/readme_lint.py README.md --no-colour
```

Note the score. You will quote both numbers at the end.

## 3. Restructure

Move the existing content into the block order in `$TOOLKIT/../docs/SPEC.md`.
Most READMEs already have most of the content and have it in the wrong order —
features before install, install before requirements, licence buried in the
middle.

Reordering alone usually moves the score twenty points and costs no writing.

At this stage: no new prose. Cut, paste, and fix the heading levels `MEC005`.

## 4. Rewrite in place, block by block

Now the sentences. In priority order, because each one gates the next:

1. **The tagline** `HERO002`. What it is, where it applies, what makes it
   different. Cover the title: does it still stand alone?
2. **The opening** `ORI001`. Two paragraphs: the problem in the reader's words,
   then what this does about it. If the original opened on the software, the
   problem paragraph is new writing — derive it from what the software fixes.
3. **The capability bullets** `ORI002`. Recast whatever list exists as four to
   six parallel bold verbs.
4. **The scope callout** `ORI003`. Almost never present. Build it from the
   caveats already scattered through the file — they are usually there, in
   parentheses, and collecting them into one honest paragraph is the single
   biggest trust gain available.
5. **The feature tour** `DEP002`. For each bullet, add the clause naming what it
   beats or what breaks without it. Where the original does not say, and you
   cannot tell from the source, leave the bullet short rather than invent a
   reason.
6. **Superlatives** `HYG003`. Replace each with the specific claim underneath it.
   Where there is no specific claim, delete the sentence — it was not carrying
   one.

Collapse the long parts into `<details>` `DEP001`, first one `open`.

## 5. The mechanical pass

```sh
python3 $TOOLKIT/readme_badges.py --check         # badges this repo cannot back
python3 $TOOLKIT/readme_badges.py --format html   # a clean, single-style row
python3 $TOOLKIT/readme_toc.py --write            # if 6+ H2s
```

Then by hand: alt text on every image `MEC003`, a language on every fence
`MEC004`, relative paths instead of absolute self-links `HYG007`, one bullet
marker `HYG004`, no `$ ` prompts in copyable blocks `MEC006`.

## 6. Verify

```sh
python3 $TOOLKIT/readme_lint.py README.md --no-colour
```

Then walk the inventory from step 1 and confirm every fact is still present.
This is not optional and it is the reason for step 1.

## 7. Report

```
readme-polish — <repo>

  74 → 93   (grade C → A)

Restructured
  <what moved where, in three lines>

Rewritten
  tagline:  "<old>"
         →  "<new>"
  opening:  now leads on <the problem>, was <what it led on>
  <n> feature bullets gained the clause naming what they beat

Added
  <what was not there: the scope callout, alt text, the Contents list>

Removed
  <what went, and why it was carrying nothing>

Needs you
  <anything you could not derive, marked {{...}} in the file>
```

Show the before and after of the tagline literally. It is the change the
maintainer will judge the rest by.

## Do not

- **Drop a caveat.** The parenthetical about a platform that half-works is the
  most valuable sentence in most READMEs, and the easiest to lose in a rewrite.
- **Invent a fact to fill a template block.** Delete the block instead.
- **Change the project's voice into a template's voice.** If the original is
  terse and funny, keep it terse and funny — the pattern is about structure and
  specificity, not about sounding like anyone in particular.
- **Chase the last five points.** A 93 that tells the truth beats a 100 assembled
  to satisfy rules. Put the rules you chose not to satisfy in
  `.awesome-readme.json` under `disable`, so the decision is visible.
