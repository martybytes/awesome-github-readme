---
name: readme-init
description: Write a README from scratch for a project that has none, or has a stub. Reads the repository to answer most of the questions itself, then asks only what the code cannot tell it. Use when asked to create, write, generate or scaffold a README, or when a repository has no README.
---

# readme-init

Most of a good README is already in the repository. Read it out rather than
asking for it — the questions worth a maintainer's attention are the three or
four the code genuinely cannot answer.

## Toolkit

`$TOOLKIT` is `${CLAUDE_PLUGIN_ROOT}/scripts` (plugin install) or the `scripts/`
directory beside this `SKILL.md` (user install).

## 1. Read the repository first

Do this before asking anything.

```sh
python3 $TOOLKIT/readme_badges.py --json     # owner, repo, branch, manifests, workflow
```

Then find, from the tree itself:

| Question | Where the answer is |
|---|---|
| What kind of project is this? | entry points, manifests, a Dockerfile, whether it is mostly Markdown |
| What is it called, and by whom? | the manifest, `git remote get-url origin` |
| What does it do? | the entry point's `--help`, the main module's docstring, the public API surface |
| How do you install it? | the manifest, an install script, a Dockerfile, the CI workflow's setup steps |
| How do you run the tests? | the CI workflow — it is the authoritative list, because it is the one that is enforced |
| What are the commands? | the argument parser, the command table, the subcommand registry |
| What platforms? | the CI matrix |
| What is the licence? | `LICENSE` |
| What already exists to link to? | `CONTRIBUTING.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `docs/` |

The CI workflow deserves the emphasis: it is the only description of the project
that is executed, so it is the only one that cannot be stale.

## 2. Ask only what is left

Usually three questions. Ask them together, once.

1. **Who is this for, and what do they do instead today?** This is the opening
   paragraph, and nothing in the repository contains it.
2. **What is the one design decision you would defend?** This is the "how it
   works" section and the sentence that separates the project from its
   alternatives. Ask for the thing that took an argument to settle.
3. **What is it deliberately not for, and what does it take over?** This is the
   `> [!NOTE]` scope callout — the highest-trust paragraph in the document, and
   the one nobody volunteers unprompted.

If the maintainer is not there to ask, write the draft with those three marked
`{{...}}` and say plainly in your summary that they are the three you could not
derive and the three that matter most.

## 3. Pick a profile and a template

| Signal in the repository | Profile | Template |
|---|---|---|
| a console entry point, a subcommand table | `cli` | `templates/README.cli.md` |
| a published package, no entry point | `library` | `templates/README.library.md` |
| Dockerfile, compose file, chart, a port | `service` | `templates/README.service.md` |
| a GUI, a bundle, a release with installers | `app` | `templates/README.app.md` |
| mostly Markdown | `docs` | `templates/README.docs.md` |
| under ~200 lines of source, one thing | `minimal` | `templates/README.minimal.md` |

Templates are in `$TOOLKIT/../templates/`. Copy one, fill every `{{...}}`, and
delete any block the project genuinely does not have — an empty section is worse
than a missing one, because it implies the answer exists somewhere.

## 4. Write it

Follow [SPEC.md](../../docs/SPEC.md) block by block and
[voice.md](../../docs/voice.md) for the sentences. The four that decide whether
the rest gets read:

**The tagline.** One sentence carrying three things: what it is, where it
applies, and the constraint that makes it different. Test it by covering the
title — it has to stand alone, because in search results it does.

**The opening paragraph.** The problem, in the reader's language, before any
mention of your software. A reader without the problem should be able to stop
there.

**The capability bullets.** Four to six, each opening with a bold verb, in
parallel — *Installs, Configures, Remembers, Updates, Diagnoses, Documents*. A
bullet you cannot open with a verb is usually an adjective in disguise.

**The scope callout.** What it is not for, what it takes over, and the escape
hatch. Write this one even if you have to mark it `{{...}}` for the maintainer.

Then generate the mechanical parts:

```sh
python3 $TOOLKIT/readme_badges.py --format html    # only badges this repo can back
python3 $TOOLKIT/readme_toc.py --write             # a Contents list, if 6+ H2s
```

## 5. The visual

Every finished README needs one `HERO005`, and a placeholder is not one. Do not
fabricate a screenshot or an ASCII mock-up.

- **CLI**: copy `templates/demo.tape` to `docs/demo.tape`, adapt the four
  commands to real read-only ones, and tell the maintainer to run
  `vhs docs/demo.tape`. Commit the tape whether or not the GIF gets recorded —
  the script is what keeps the asset honest later.
- **Service or library**: a Mermaid diagram, which you can write now, and which
  renders natively on GitHub.
- **App**: ask for two screenshots, light and dark, and wire up the `<picture>`
  block.

[visuals.md](../../docs/visuals.md) has the details.

## 6. Check it, then commit the standard

```sh
python3 $TOOLKIT/readme_lint.py README.md --no-colour
```

Target 90+, and read the remaining findings rather than chasing them — a rule
you decided not to satisfy belongs in `.awesome-readme.json` under `disable`,
where the next person can see the decision.

Offer to write that config, so the profile travels with the repository:

```sh
python3 $TOOLKIT/install.py --project . --profile <profile>
```

## Do not

- **Invent facts.** No benchmark you have not run, no platform you have not seen
  in the CI matrix, no feature you have not found in the source. A README is a
  set of claims; a fabricated one is discovered on first use.
- **Ship placeholders silently.** `HYG001` fails on them, and rightly. If you
  leave `{{...}}`, name every one in your summary.
- **Write a section because the template has it.** Delete what the project does
  not have.
- **Reach for adjectives.** If a sentence would fit any competitor's README
  unchanged, it is not carrying information. See [voice.md](../../docs/voice.md).
