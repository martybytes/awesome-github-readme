# The README pattern

This is the specification the skills, the linter and the templates all
implement. It is written as a sequence of blocks in the order a reader meets
them, because that is the only order that matters — a README is read top to
bottom, once, by someone deciding whether to keep reading.

Every rule here earns its place by answering a question a real reader has. Where
a rule has a machine check, its id is in the margin (`HERO002`); run
`readme_lint.py --explain HERO002` for the reasoning in one paragraph.

- [The reader you are writing for](#the-reader-you-are-writing-for)
- [Block 1: the hero](#block-1-the-hero)
- [Block 2: what it is](#block-2-what-it-is)
- [Block 3: the scope callout](#block-3-the-scope-callout)
- [Block 4: contents](#block-4-contents)
- [Block 5: requirements](#block-5-requirements)
- [Block 6: install](#block-6-install)
- [Block 7: quickstart](#block-7-quickstart)
- [Block 8: configuring](#block-8-configuring)
- [Block 9: the feature tour](#block-9-the-feature-tour)
- [Block 10: architecture in 30 seconds](#block-10-architecture-in-30-seconds)
- [Block 11: development](#block-11-development)
- [Block 12: layout](#block-12-layout)
- [Block 13: license](#block-13-license)
- [Profiles](#profiles)
- [What this pattern deliberately omits](#what-this-pattern-deliberately-omits)

---

## The reader you are writing for

Three people open a README, and they arrive in this order:

1. **The evaluator**, thirty seconds in, deciding whether this solves their
   problem. They read the tagline, look at the picture, and scan the bold words.
   They never scroll past the first screen unless something earns it.
2. **The adopter**, five minutes in, trying to get it running. They want one
   command, then a second command that proves the first worked.
3. **The contributor**, an hour in, trying to change something. They want the
   layout, the test commands and the design rationale.

A README that serves only the evaluator is a landing page. One that serves only
the contributor is a design doc nobody found. The structure below serves all
three by putting each one's content in the order they arrive, and collapsing the
later readers' content so it does not cost the earlier ones a scroll.

**The governing test for every sentence: could a competitor's README contain
this sentence unchanged?** If yes, it is filler. "Fast, modern and flexible"
passes for anything. "Sorts directories by the newest mtime among their
*immediate* children, unlike `ls -lt`" could not appear anywhere else.

---

## Block 1: the hero

The first screenful, before any `##`. Five elements, in this order:

```markdown
<h1 align="center">project-name</h1>

<p align="center">
  <em>One sentence: what it is, for whom, and the constraint that makes it
  different.</em>
</p>

<p align="center">
  <a href="…/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/…"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/…"></a>
  <a href="…/tags"><img alt="Latest tag" src="https://img.shields.io/…"></a>
</p>

<p align="center">
  <a href="#install">Install</a> &middot;
  <a href="#quickstart">Quickstart</a> &middot;
  <a href="ARCHITECTURE.md">Architecture</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img alt="the tool listing its subcommands, then reporting every check passing"
       src="docs/demo.gif" width="760">
</p>

---
```

### The title `HERO001`

One H1. GitHub already prints the repository name above the README; a second H1
further down competes with it and breaks the outline the sidebar and screen
readers build. Centre it with `<h1 align="center">` when the hero is centred —
GitHub strips `align` from Markdown headings but honours it on raw HTML.

### The tagline `HERO002`

One sentence, under 30 words, directly under the title. It is the only text that
appears in GitHub search results, in social cards and in the repository sidebar,
so it has to work with no other context.

It must contain three things:

| | terminal-stack's tagline |
|---|---|
| **what it is** | "One terminal setup — WezTerm, tmux, Starship, zsh and PowerShell" |
| **where it applies** | "deployed to Windows, WSL, native Linux and macOS" |
| **the constraint that makes it different** | "from a single repo. Each platform gets the parts that make sense on it." |

Delete the adjectives and the sentence still says all three. That is the test.

### The badge row `HERO003` `HYG002` `TRU004`

Three to five, one style, each linked to the page it reports on, each backed by
live data. A CI badge over a repository with no workflow is a broken claim on
the first screen.

`readme_badges.py` builds the row from what the repository can actually back;
[badges.md](badges.md) has the catalogue and the reasoning about which ones
carry information.

### The nav row `HERO004`

Four to six links. Half of them point into the page (`#install`), half point at
the sibling documents the reader does not yet know exist (`ARCHITECTURE.md`,
`CHANGELOG.md`). This row is how the deeper documentation gets discovered at
all — a link at the bottom of a 500-line README is a link nobody follows.

### The visual `HERO005`

A terminal recording, a screenshot, or a diagram — above the fold, with real
alt text `MEC003`.

This is the single highest-leverage element in a README, because it answers
"what does this actually do" in the time it takes to render. A recording also
proves the software runs, which no amount of prose does.

[visuals.md](visuals.md) covers recording one with VHS, keeping it reproducible,
and the theme-aware `<picture>` trick for diagrams. The rule that matters:
**the recording must be reproducible from a script committed in the repository**,
or it will never be re-recorded and will drift into a lie.

### The rule `HERO006`

A `---` between the hero and the first `##`. The hero is centred HTML; the body
is left-aligned prose. The rule tells the reader the register just changed.

---

## Block 2: what it is `ORI001`

Two short paragraphs and a bullet list. The paragraphs open on **the problem**,
not the software:

> Setting up a terminal takes an afternoon. Setting up **four** of them — a
> Windows box, the Ubuntu inside it, a Linux server, a Mac — and keeping them the
> same takes forever, and they drift anyway.

Nobody has "wants a dotfiles manager" as a felt need. Everybody who has four
machines has *that*. Name the problem in the reader's language, then say what
this does about it. A reader who does not have the problem should be able to
stop here, which is a service to them and to your issue tracker.

Then the capability bullets `ORI002` — verb-led, bold, parallel:

```markdown
- **Installs** a full terminal in one command per machine — …
- **Configures** everything from one source of truth, so …
- **Remembers** your choices — leader key, theme, tools, voice — and keeps them across updates.
- **Updates** with `tstack update`, and **undoes** it with `tstack rollback`.
- **Diagnoses** itself with `tstack doctor` — the same checks on every platform …
- **Documents** itself: `doc` is a searchable knowledge base of runbooks, in your terminal.
```

Four to six of them. The parallel verb does two jobs: it scans in about two
seconds, and it forces each bullet to claim one concrete thing the software
*does* rather than one adjective it *is*. A bullet you cannot open with a verb
is usually not a capability.

---

## Block 3: the scope callout `ORI003`

A GitHub alert, immediately after the capability bullets:

```markdown
> [!NOTE]
> This is a personal stack, published because the cross-platform mechanism is
> genuinely reusable. It is opinionated: it expects a fairly clean home
> directory, and it will manage `~/.zshrc` and your PowerShell `$PROFILE`
> outright — keep your own additions in `~/.zshrc.local`, which it never
> touches. [INSTALL.md](INSTALL.md) has a step-by-step path if you want to
> inspect each change before applying it.
```

This is the highest-trust paragraph in the document, and almost no README has
one. It says three things a reader cannot get anywhere else:

- **What this is not for.** "A personal stack" resets expectations about support
  and stability more honestly than any stability badge.
- **What it takes over.** Anything that writes outside its own directory owes
  the reader a sentence naming exactly what. This is the paragraph that prevents
  the issue titled "this overwrote my config".
- **The escape hatch.** Having named the risk, name the way around it.

Use `[!NOTE]` for scope, `[!WARNING]` for data loss, `[!IMPORTANT]` for a step
people skip and then file an issue about. The five types are `NOTE`, `TIP`,
`IMPORTANT`, `WARNING`, `CAUTION`; more than two or three alerts in a document
and none of them reads as special any more.

---

## Block 4: contents `ORI004`

Once the page has six or more `##` sections, a Contents list. GitHub's sidebar
outline exists but is one click away and most readers never open it.

Keep it to H2s only. A Contents list that mirrors every H3 is a second document
to maintain and drifts within a month; `readme_toc.py --check` in CI keeps the
H2 version honest for free.

---

## Block 5: requirements `ONB003`

A table, before the install command, one row per supported variant:

```markdown
| Platform | You need first | The installer adds |
|---|---|---|
| **Windows 11** | winget (App Installer); PowerShell 7+ recommended | winget packages, `$PROFILE`, Nerd Font, Starship |
| **WSL2 Ubuntu** | WSL2 with Ubuntu (run the Windows step first) | apt packages, oh-my-zsh, chezmoi, Starship |
| **macOS** | an admin account | brew formulae and casks, oh-my-zsh, chezmoi, Starship |
```

Three columns, and the third is the one people omit. "What you need first" tells
a reader whether to continue. "What the installer adds" tells them what they are
consenting to — the same trust move as the scope callout, applied to their disk.

The rows are the axis your project actually varies along: platforms for a CLI,
runtime versions for a library, deployment targets for a service. One row per
thing a reader might be, and the reader picks their row and ignores the rest.

State what is optional, and what it costs to skip:

> Docker is **optional**. It is only needed for the memory, compression, voice
> and browser stacks under `services/`; everything else works without it.

---

## Block 6: install `ONB001`

One fenced, copy-pasteable command per variant, each in its own `<details>`.

```markdown
<details open>
<summary><b>macOS</b> (Apple Silicon or Intel)</summary>

```sh
curl -fsSL https://raw.githubusercontent.com/owner/repo/main/install-mac.sh | bash
```

Two System Settings toggles free `Ctrl+Space` before the keybindings work;
[INSTALL.md § Reopen](INSTALL.md#4-reopen) walks through them.
</details>
```

Rules:

- **One command.** If it takes three, they belong in a script that the one
  command runs.
- **The first `<details>` is `open`** `DEP001`, so the reader sees the shape
  without clicking, and knows the others hold the same thing for their platform.
- **Say the command is idempotent, if it is.** "Safe to re-run" removes the main
  reason people hesitate.
- **Fence everything** — GitHub puts a copy button on fenced blocks, and a
  reader who copies an install command from prose gets the surrounding text.
- **No `$` prompt prefixes** `MEC006`. The copy button takes them too.

Number the steps if there is more than one — *1. Run the one-liner, 2. Answer
the wizard, 3. Verify* — because a numbered list is a promise about how many
steps there are.

### Verify `ONB004`

End install with the command that proves it worked:

```sh
tstack doctor
```

> Read-only, and exits non-zero if anything is wrong. Each failing check names
> the command that fixes it.

"It printed a lot of text" is not success. A named check turns a support thread
into a one-line answer, and gives you somewhere to put every "did you…" question
you would otherwise answer by hand.

### The unattended path `ONB005`

Anything with a prompt eventually has to run in CI, in a Dockerfile, or across
fifty machines. Document the environment variables or flags that answer every
question, in one place, even if the list is long — the alternative is a reader
in your source tree looking for them.

---

## Block 7: quickstart `ONB002`

Install proves it is on the machine. Quickstart proves it does something. Two
different questions; do not answer them in one section.

One fenced block, annotated, comments aligned:

```sh
tstack                 # every subcommand, with platform gaps marked
tstack --version       # clone path, branch, commit
tstack doctor          # diagnose the install; --json for one record per check
tstack config          # interactive settings menu
tstack update          # pull the latest stack and re-apply
tstack rollback        # undo that update
```

The aligned `#` column is what makes this scannable as a table while staying
pasteable as a script. It is worth the manual alignment.

Choose the commands a real user runs **in the order they meet them**, not the
ones that show off. Then say anything about them that a reader would otherwise
have to discover:

> `tstack` and `doc` are shell functions the stack installs into `~/.zshrc`, so
> they exist only after an install.

For a library, this block is the smallest complete program — imports included,
runnable by paste, no `...` elisions.

---

## Block 8: configuring `ONB006`

Lead with the one command that fronts everything, then one-shot examples of the
settings people actually change:

```sh
tstack config theme follow      # dark / light / follow the OS
tstack config leader ctrl-a     # the WezTerm leader key
tstack config tts on            # voice notifications
tstack config show              # everything currently saved
```

Then a table for the rest of the surface, one line each, with the promise that
`-h` exists on all of them. Documenting every flag in the README is what turns a
README into a man page nobody reads; documenting the *front door* plus a table
of what is behind it is what people need.

State where settings persist and what survives an upgrade `DEP005`:

```markdown
| | Clone | Settings |
|---|---|---|
| **Windows + WSL** | `%LOCALAPPDATA%\project\` | mirrored to `config.json` |
| **Linux / macOS** | `~/.local/share/project` | `~/.config/project/config.toml` |
```

---

## Block 9: the feature tour `DEP001` `DEP002`

The section that would make the README too long, made collapsible. `<details>`
groups by theme, first one `open`:

```markdown
<details open>
<summary><b>Navigation</b></summary>

- **`lsr`** ranks directories by the newest mtime among their *immediate*
  children, so a project you edited inside all day sorts first — unlike
  `ls -lt`, which sorts by the directory's own mtime and buries it.
</details>
```

Every bullet has three parts, and the third is the one that matters:

1. **The name**, in bold or code, so it is greppable.
2. **What it does**, in one clause.
3. **The reason** — what it beats, or what breaks without it.

Compare:

| | |
|---|---|
| ✗ | **`lsr`** — a better `ls`. |
| ✗ | **`lsr`** — blazingly fast directory listing with smart sorting. |
| ✓ | **`lsr`** ranks directories by the newest mtime among their *immediate* children, so a project you edited inside all day sorts first — **unlike `ls -lt`, which sorts by the directory's own mtime and buries it.** |

Only the third gives a reader a reason to change what they type tomorrow. The
rationale *is* the feature; the rest is a name.

Rationale usually arrives on one of a small set of hinges — `because`,
`so that`, `unlike`, `otherwise`, `rather than`, `without which`, `which is what
catches`. `DEP002` counts them; a feature tour with none is a list of nouns.

Where a design choice has a cost, say so in the same breath:

> Because `--add` appends, the include resolves **last** and its settings win —
> so put a setting of your own *below* that line if you want yours to.

---

## Block 10: architecture in 30 seconds `DEP003`

Three paragraphs, then a link out.

Most readers want to know roughly how it works and whether the approach is sane.
A handful want the whole design. Putting the whole design in the README serves
the second group and loses the first; putting none of it serves neither.

The title is doing work — *"Architecture in 30 seconds"* sets a budget and
promises there is more. End with the door:

> Single source of truth, single `chezmoi apply`, every target updated. The long
> version is in [ARCHITECTURE.md](ARCHITECTURE.md); the design decisions and the
> failures behind them are in [docs/decisions.md](docs/decisions.md).

A decision log — *what we tried, what broke, what we do now* — is the single
most useful document a project can keep and the least common. Link it here.

---

## Block 11: development `TRU001`

The exact commands CI runs, verbatim, so a contributor can reproduce the gate
before pushing:

```sh
ruff check src tests
ruff format --check src
mypy
pytest tests/
```

Then how they are enforced, and what CI covers that a laptop cannot:

> `.githooks/pre-commit` runs those four; `pre-push` re-runs the suite with the
> coverage floor, once the clone has `core.hooksPath=.githooks` set.
>
> CI covers Ubuntu, macOS, Windows and WSL, which is more than any single
> development machine can.

"Run the tests" is not this. Four pasteable lines are.

---

## Block 12: layout `DEP004`

One fenced tree, one comment per top-level entry:

```
project/
├── src/         the library itself
├── bootstrap/   per-OS bootstraps
├── services/    Docker stacks
├── docs/        architecture, decisions, runbooks
└── tests/       pytest suite, fixtures, parity containers
```

Top level only. A tree that recurses three levels deep is a `find` dump that
drifts the first time someone adds a file.

Follow it with anything non-obvious about the layout — which directories are
ignored by the packaging, which are generated, which are the source of truth for
something else. That paragraph is what a tree alone cannot say.

Tag the fence `text` `MEC004` so no highlighter tries to colour box-drawing
characters.

---

## Block 13: license `TRU002`

```markdown
## License

[MIT](LICENSE).
```

One line. Without it the legal default is "all rights reserved", which means
nobody may use it — including the person who was about to.

---

## Profiles

Not every project is a CLI. The linter ships six profiles, each a different
required-section set, because the question a reader arrives with differs:

| Profile | Required sections | The reader's question |
|---|---|---|
| `cli` | what, install, quickstart, config, development, license | "What do I type?" |
| `library` | what, install, quickstart, development, license | "What does the API look like?" |
| `service` | what, requirements, install, config, architecture, license | "What does it need, and where does it run?" |
| `app` | what, install, quickstart, license | "What does it look like?" |
| `docs` | what, contents, development, license | "What is in here, and how do I add to it?" |
| `minimal` | what, install, license | "Is this the thing I searched for?" |

Set one in `.awesome-readme.json`; add sections your project needs on top with
`require`, and switch off rules that do not apply with `disable`.

```json
{
  "profile": "library",
  "require": ["faq"],
  "disable": ["HERO005"],
  "strict": false
}
```

Turning a rule off is a legitimate answer. Turning it off *in the config, where
the next person can see it*, is the difference between a decision and a lapse.

---

## What this pattern deliberately omits

Things that appear in most README templates and are not here, with the reason:

| Omitted | Why |
|---|---|
| A "Features" section of adjectives | Superseded by verb-led capability bullets and the feature tour, both of which force a concrete claim. `HYG003` |
| Star/fork/follower badges | They report on your social graph, not on whether the software works. |
| "Made with ❤️", "PRs welcome", visitor counters | No data behind them, and they dilute the badges that have some. `HYG002` |
| A full API reference | That is a docs site or a `docs/` directory. A README that contains it is a manual whose first screen is buried. `HYG006` |
| A roadmap | It is stale in a month and reads as a promise. Use issues, milestones, or a decision log. |
| Emoji section headings | They change the generated anchor, break every link into the section, and render as tofu in half the Markdown viewers that are not GitHub. `HYG005` |
| A Contributors wall | GitHub renders one already, on the same page. |
| "Table of Contents" for a short page | Below six H2s it is longer than the thing it indexes. `ORI004` |
| Absolute `github.com/owner/repo/blob/main/...` self-links | They break on every fork, branch and mirror. Relative links do not. `HYG007` |

---

## Checking your work

```sh
python3 scripts/readme_lint.py README.md          # scored report
python3 scripts/readme_lint.py --rules            # the whole rubric
python3 scripts/readme_lint.py --explain DEP002   # one rule, and why
python3 scripts/readme_badges.py --check          # badges this repo cannot back
python3 scripts/readme_toc.py --check             # contents list drift
```

A score is a proxy, not the goal. Every rule here has a reason attached, and the
reason is the thing to satisfy — a 100 with a tagline nobody can parse is a
worse README than an 85 that tells the truth in the first sentence.
