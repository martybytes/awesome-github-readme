# Voice

The structure in [SPEC.md](SPEC.md) is the skeleton. This is how the sentences
inside it sound, and it is the part a linter can only partly check — `HYG003`
catches the worst offenders, and the `readme-reviewer` agent catches the rest.

## The one test

> Could a competitor's README contain this sentence unchanged?

If yes, delete it. "Fast, modern and flexible" fits any project ever written,
which is exactly why it tells a reader nothing. Specificity is not a style
preference; it is the entire information content.

| Generic | Specific |
|---|---|
| Blazingly fast | Indexes 40k files in 1.2s on an M2; `ripgrep` takes 0.9s and does less |
| Cross-platform | Windows 11, WSL2, Debian/Ubuntu, Arch and macOS, from one `apply` |
| Highly configurable | Twelve settings, each with a default, each overridable per machine |
| Seamless integration | Adds one `include.path` line to `~/.gitconfig` and owns nothing else in it |
| Robust error handling | Every failing check names the command that fixes it |
| Lightweight | One Python file, standard library only, no install step |

## Rules

**Second person, present tense.** "You answer a few questions once; every
machine ends up with the same prompt." Not "users are prompted" and not "will
be configured". The reader is doing this, now.

**Name the alternative you beat.** A feature described against nothing is a
feature with no size. "Unlike `ls -lt`, which sorts by the directory's own mtime
and buries it" is the whole reason the tool exists, in twelve words.

**Say what breaks without it.** This is the most efficient sentence pattern in
technical writing, because it converts a feature into a consequence:

> …the `ssh-terminfo`/`ssh-env` shell-integration features, **without which
> backspace and Delete break over ssh**.

**Put the cost next to the benefit.** A design note that admits a trade-off is
believed; one that does not is discounted:

> Because `--add` appends, the include resolves **last** and its settings win —
> so put a setting of your own *below* that line if you want yours to.

**Prefer a number, a path or a command to an adjective.** `%LOCALAPPDATA%\stack`
carries more than "a sensible location". `fail_under = 81` carries more than
"good coverage".

**Write the limitation before someone finds it.** "Desktop Linux installs
WezTerm but keeps its stock config" costs one clause and prevents one issue.
Every honest limitation you volunteer buys credit against the claims you make
elsewhere.

**Let paragraphs end.** The most common README failure is not a wrong sentence,
it is a fourth one where three were enough.

## Banned by default `HYG003`

Not because they are ugly, but because they are unfalsifiable — no reader can
check them, so no reader believes them:

> blazingly fast · lightning fast · world-class · cutting-edge · state-of-the-art
> · revolutionary · game-changing · next-generation · ultimate · seamlessly ·
> effortlessly · powerful and flexible · one-stop · best-in-class · supercharge ·
> unleash · simply the best

Each has a specific replacement. "Blazingly fast" → the benchmark. "Seamlessly"
→ the one line of config it needs. "Powerful and flexible" → the two things it
does that the alternative does not.

## Formatting conventions

- **Bold** for the first two or three words of a bullet — the name of the thing.
  Bold is a scanning aid; a paragraph in bold is a paragraph nobody scans.
- *Italic* for the one word carrying the contrast: "the newest mtime among their
  *immediate* children".
- `Code` for anything a reader types, and anything on disk — commands, flags,
  file names, environment variables, paths.
- Em dashes for the clause that carries the reason. They are the punctuation of
  this pattern; the rationale usually hangs off one.
- One bullet marker throughout `HYG004`. `-`.
- Tables when the reader is choosing a row (their platform, their profile, their
  language). Prose when they are reading in order.

## Length

Aim for 250 to 500 lines. Under 150 and something the reader needs is missing;
over 700 `HYG006` and the README has quietly become the manual — the reader who
needed only the first screen now has to scroll through everything else to be
sure they did.

The way out is not compression, it is `docs/`. Move the reference material out,
link to it from the nav row and from the section it belongs to, and let the
README stay the thing that gets someone from "what is this" to "it works".
