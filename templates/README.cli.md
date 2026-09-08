<h1 align="center">{{PROJECT}}</h1>

<p align="center">
  <em>{{TAGLINE — what it is, where it applies, and the constraint that makes it
  different. One sentence, under 30 words, that works with no other context.}}</em>
</p>

<p align="center">
  <a href="https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=flat-square"></a>
  <a href="https://github.com/{{OWNER}}/{{REPO}}/tags"><img alt="Latest tag" src="https://img.shields.io/github/v/tag/{{OWNER}}/{{REPO}}?style=flat-square&label=version"></a>
  <a href="https://github.com/{{OWNER}}/{{REPO}}/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/{{OWNER}}/{{REPO}}?style=flat-square"></a>
</p>

<p align="center">
  <a href="#install">Install</a> &middot;
  <a href="#quickstart">Quickstart</a> &middot;
  <a href="#configuring">Configuring</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img alt="{{ALT — what the recording shows, command by command}}" src="docs/demo.gif" width="760">
</p>

---

## What it is

{{THE PROBLEM. Two or three sentences in the reader's language, about the pain
they already have. Not about your software. A reader who does not have this
problem should be able to stop here.}}

{{WHAT THIS DOES ABOUT IT. Two or three sentences. The mechanism, in plain
words, and the one design choice that makes it work.}}

- **{{Verb}}s** {{one concrete thing it does — a command, a file, a result}}.
- **{{Verb}}s** {{the second, with the reason it matters}}.
- **{{Verb}}s** {{the third}}.
- **{{Verb}}s** {{the fourth}}.
- **{{Verb}}s** itself with `{{project}} doctor` — {{what the check covers}}.

> [!NOTE]
> {{SCOPE. What this is not for. What it takes over on the reader's machine,
> named exactly. The escape hatch for someone who wants to inspect first.}}

## Contents

<!-- toc -->

- [Requirements](#requirements)
- [Install](#install)
- [Quickstart](#quickstart)
- [Configuring](#configuring)
- [What you get](#what-you-get)
- [How it works](#how-it-works)
- [Development](#development)
- [Layout](#layout)
- [License](#license)

<!-- /toc -->

## Requirements

Pick your row. Everything in the third column is installed for you.

| Platform | You need first | The installer adds |
|---|---|---|
| **{{Platform A}}** | {{prerequisite}} | {{what lands}} |
| **{{Platform B}}** | {{prerequisite}} | {{what lands}} |
| **{{Platform C}}** | {{prerequisite}} | {{what lands}} |

{{What is optional, and what it costs to skip it.}}

## Install

Each installer is idempotent — safe to re-run.

<details open>
<summary><b>{{Platform A}}</b></summary>

```sh
{{one command}}
```

{{Anything a reader has to do by hand afterwards, with a link to the long form.}}
</details>

<details>
<summary><b>{{Platform B}}</b></summary>

```sh
{{one command}}
```
</details>

Then verify:

```sh
{{project}} doctor
```

Read-only, and exits non-zero if anything is wrong. Each failing check names the
command that fixes it.

<details>
<summary><b>Unattended</b> (CI, containers, fleets)</summary>

Every prompt has an environment variable that answers it:

```sh
{{PROJECT}}_PROFILE=full {{PROJECT}}_ASSUME_YES=1 {{one command}}
```

| Variable | Answers |
|---|---|
| `{{PROJECT}}_PROFILE` | {{which question}} |
| `{{PROJECT}}_ASSUME_YES` | the review screen |
</details>

## Quickstart

```sh
{{project}}                 # every subcommand, with unavailable ones marked
{{project}} --version       # version, install path, commit
{{project}} doctor          # diagnose the install; --json for one record per check
{{project}} {{verb}}        # {{the thing people came for}}
{{project}} config          # interactive settings
{{project}} update          # pull the latest and re-apply
```

{{Anything about these commands a reader would otherwise have to discover — that
they are shell functions, that one needs sudo, that one is destructive.}}

## Configuring

`{{project}} config` is the front door. Run it bare for a menu, or one-shot:

```sh
{{project}} config {{key}} {{value}}   # {{what it changes}}
{{project}} config show                # everything currently saved
```

| | Config | Data |
|---|---|---|
| **Linux / macOS** | `~/.config/{{project}}/` | `~/.local/share/{{project}}/` |
| **Windows** | `%APPDATA%\{{project}}\` | `%LOCALAPPDATA%\{{project}}\` |

## What you get

<details open>
<summary><b>{{Theme one}}</b></summary>

- **`{{name}}`** {{what it does}}, so {{the consequence}} — unlike {{the
  alternative}}, which {{the failure it has}}.
- **`{{name}}`** {{what it does}} — {{what breaks without it}}.
</details>

<details>
<summary><b>{{Theme two}}</b></summary>

- **{{name}}** {{what it does and why it beats the obvious approach}}.
</details>

## How it works

{{Three paragraphs. The mechanism, the one non-obvious decision, and the
consequence of that decision.}}

{{One sentence of summary.}} The long version is in
[ARCHITECTURE.md](ARCHITECTURE.md); the decisions and the failures behind them
are in [docs/decisions.md](docs/decisions.md).

## Development

```sh
{{lint command}}
{{format check command}}
{{type check command}}
{{test command}}
```

{{How they are enforced — pre-commit hook, CI matrix — and what CI covers that a
single development machine cannot.}}

## Layout

```text
{{project}}/
├── src/      {{what it holds}}
├── docs/     {{what it holds}}
└── tests/    {{what it holds}}
```

{{Anything non-obvious: which directories are generated, which are ignored by
packaging, which are the source of truth for something else.}}

## License

[MIT](LICENSE).
