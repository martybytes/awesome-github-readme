<h1 align="center">{{PROJECT}}</h1>

<p align="center">
  <em>{{TAGLINE — what it lets someone do, on which platforms, and the one thing
  it does differently from the app they use now.}}</em>
</p>

<p align="center">
  <a href="https://github.com/{{OWNER}}/{{REPO}}/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/{{OWNER}}/{{REPO}}?style=flat-square"></a>
  <a href="https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=flat-square"></a>
</p>

<p align="center">
  <a href="#install">Install</a> &middot;
  <a href="#using-it">Using it</a> &middot;
  <a href="#features">Features</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/screenshot-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/screenshot-light.png">
    <img alt="{{ALT — the screen, and what is happening on it}}" src="docs/screenshot-light.png" width="760">
  </picture>
</p>

---

## What it is

{{THE PROBLEM someone has with the app they use today. Concrete, in their words.}}

{{WHAT THIS DOES INSTEAD, and the design choice that makes it possible.}}

- **{{Verb}}s** {{one thing a user does with it}}.
- **{{Verb}}s** {{the second}}.
- **Works offline** / **Stores nothing** / {{the property people actually care about}}.
- **{{Verb}}s** {{the fourth}}.

> [!NOTE]
> {{Who this is not for. What data it touches. Whether anything leaves the
> machine, and where it goes.}}

## Install

<details open>
<summary><b>macOS</b></summary>

```sh
brew install --cask {{project}}
```

{{Any Gatekeeper or permission step, with what the dialog actually says.}}
</details>

<details>
<summary><b>Windows</b></summary>

```powershell
winget install {{Publisher}}.{{Project}}
```
</details>

<details>
<summary><b>Linux</b></summary>

```sh
{{flatpak / AppImage / package manager command}}
```
</details>

Or download a build from [Releases](https://github.com/{{OWNER}}/{{REPO}}/releases/latest).

## Using it

{{The first thing to do after opening it, in three numbered steps, one sentence
each.}}

1. {{step}}
2. {{step}}
3. {{step}}

| Shortcut | Does |
|---|---|
| <kbd>{{key}}</kbd> | {{action}} |
| <kbd>{{key}}</kbd> | {{action}} |

## Features

<details open>
<summary><b>{{Theme one}}</b></summary>

- **{{Feature}}** {{what it does}}, so {{the consequence}} — unlike {{the
  alternative}}, which {{its failure}}.
</details>

<details>
<summary><b>{{Theme two}}</b></summary>

- **{{Feature}}** {{what it does, and why it beats the obvious approach}}.
</details>

## Configuration

{{Where settings live on each platform, and which of them survive an upgrade.}}

| | Settings | Data |
|---|---|---|
| **macOS** | `~/Library/Preferences/{{id}}.plist` | `~/Library/Application Support/{{Project}}/` |
| **Windows** | `%APPDATA%\{{Project}}\` | `%LOCALAPPDATA%\{{Project}}\` |
| **Linux** | `~/.config/{{project}}/` | `~/.local/share/{{project}}/` |

## Development

```sh
{{install deps}}
{{run in dev mode}}
{{test}}
{{build a release}}
```

{{What CI builds, on which runners, and which platform can only be verified by
hand.}}

## License

[MIT](LICENSE).
