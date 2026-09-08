# Antipatterns

Each of these is common, each looks like effort, and each costs a reader
something. The rule id in the margin is the machine check where one exists.

## The feature list with no reader

```markdown
## Features
- Fast
- Flexible
- Easy to use
- Cross-platform
- Well documented
```

Every one of these fits every project ever written, which is what makes them
worthless — a reader learns nothing they did not assume. And the section
arrives before the reader has been told what problem the software solves, so
there is nothing for the adjectives to attach to.

**Instead:** verb-led capability bullets `ORI002` after a problem paragraph
`ORI001`, then a feature tour where each bullet carries its reason `DEP002`.

## The badge wall

Fourteen badges: build, coverage, licence, version, downloads, stars, forks,
issues, PRs welcome, made with love, code style, dependencies, Discord, Twitter.

Past about five, badges stop being read as individual facts and become a texture
that the eye skips — which means the two that matter got hidden by the twelve
that do not `HERO003`. And the vanity ones actively discount the real ones,
because they mark the row as assembled from a template `HYG002`.

**Instead:** three to five, one style, each linked, each backed by live data.
[badges.md](badges.md).

## The README that is the manual

Eleven hundred lines: every flag, every config key, every API method, an FAQ, a
roadmap, a changelog, a contributor wall.

Everything a reader needs is in there, and none of it is findable `HYG006`. The
evaluator who wanted to know what this is has to scroll past the API reference
to reach the install command.

**Instead:** the README gets someone from "what is this" to "it works". Reference
material lives in `docs/`, linked from the nav row and from the section it
belongs to.

## The empty template

```markdown
## Installation
TODO

## Usage
Coming soon

## Contributing
PRs welcome!
```

Worse than having no README, because the headings promise answers that are not
there `HYG001`. A reader now knows the project is unfinished *and* that its
documentation was generated and never read — which is what they will assume
about the code.

**Instead:** write the sections you can, delete the ones you cannot. A short
honest README is a good README.

## The mock demo

A hand-made ASCII diagram of terminal output, or a screenshot from a version
that no longer exists.

Anything not reproducible from a committed script has already started drifting,
and there is no way for a reader — or CI — to tell how far. The first thing on
the page is the thing you cannot verify.

**Instead:** a VHS tape committed beside the GIF, and a line in the README saying
when to re-record. [visuals.md](visuals.md).

## Install instructions that assume your machine

```sh
git clone …
cd project
make install
```

Which `make`? Is `python3` on the path? Does this need `sudo`? Where does it
install to? What if the clone directory already exists?

Every unstated assumption is a place a reader stops `ONB003`.

**Instead:** requirements before install, one command per platform, and a verify
step that proves it landed `ONB004`.

## Emoji headings

```markdown
## 🚀 Getting Started
## ✨ Features
## 📦 Installation
```

The emoji becomes part of the generated anchor, so every link into the section
breaks — including the Contents list the same document ships `HYG005` `MEC002`.
They render as tofu in half the Markdown viewers that are not GitHub. And they
carry no information: 🚀 appears above every "Getting Started" section in the
world.

**Instead:** words. If a section needs a visual anchor, `<details>` and bold
summaries do more with less.

## The stale Contents list

A hand-maintained TOC that drifted three headings ago. The links still render,
still look right, and land the reader at the top of the page `MEC002`.

**Instead:** generate it, and check it in CI:

```sh
python3 scripts/readme_toc.py --write
python3 scripts/readme_toc.py --check
```

## Absolute self-links

```markdown
See [the architecture](https://github.com/owner/repo/blob/main/ARCHITECTURE.md).
```

Breaks on every fork, every branch, every mirror, and in every local clone
`HYG007`. A reader on a fork follows it back to the upstream and reads the wrong
version of the document.

**Instead:** `[the architecture](ARCHITECTURE.md)`.

## The roadmap

```markdown
## Roadmap
- [x] Core engine
- [ ] Plugin system (Q2)
- [ ] Cloud sync
```

It is stale within a month, and until then it reads as a promise. A reader who
adopts the project for the plugin system has been misled by a checkbox.

**Instead:** issues and milestones, which update themselves. If the point was to
explain *why* the project is shaped the way it is, that is a decision log —
`docs/decisions.md`, what we tried, what broke, what we do now — and it is the
most useful document a project can keep.

## Prompt characters in copyable blocks

````markdown
```
$ npm install thing
$ thing --init
```
````

GitHub puts a copy button on fenced blocks. It copies the `$` too, and the
reader pastes a script that does not run `MEC006`. The block is also untagged,
so it gets no highlighting `MEC004`.

**Instead:** drop the prompts and tag the fence ```` ```sh ````. If you genuinely
need to show output interleaved with input, tag it ```` ```console ```` and
accept that it is for reading, not copying.

## The scope callout that isn't there

The most common omission, and the largest available improvement.

A README with no admitted limitation reads as marketing, and a reader discounts
every other claim in it by however much they discount marketing. Meanwhile the
project *does* have limits, and the reader finds them on day two — with an
issue, or by leaving `ORI003`.

**Instead:** one `> [!NOTE]` saying what it is not for, what it takes over, and
where the escape hatch is. It costs four lines and buys more trust than any
feature bullet.

## "Just" and "simply"

> Simply run the installer and you're done.

If it were simple the reader would not be reading. The word does nothing except
tell someone who then hits a problem that the problem is theirs — which is the
last thing you want from documentation.

**Instead:** delete the word. The sentence is better without it, every time.
