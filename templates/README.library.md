<h1 align="center">{{PROJECT}}</h1>

<p align="center">
  <em>{{TAGLINE — what it does, for which language and runtime, and the
  constraint that makes it different from the obvious alternative.}}</em>
</p>

<p align="center">
  <a href="https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="https://pypi.org/project/{{PACKAGE}}/"><img alt="Package version" src="https://img.shields.io/pypi/v/{{PACKAGE}}?style=flat-square"></a>
  <a href="https://pypi.org/project/{{PACKAGE}}/"><img alt="Supported versions" src="https://img.shields.io/pypi/pyversions/{{PACKAGE}}?style=flat-square"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=flat-square"></a>
</p>

<p align="center">
  <a href="#install">Install</a> &middot;
  <a href="#usage">Usage</a> &middot;
  <a href="#api">API</a> &middot;
  <a href="docs/">Docs</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## What it is

{{THE PROBLEM, in the language of someone who writes this kind of code. The
awkward thing they do today, in one or two sentences.}}

{{WHAT THIS DOES INSTEAD, and the one design decision that makes it possible.}}

```{{lang}}
{{The five-line version. Imports included. Runnable by paste. No elisions.}}
```

- **{{Verb}}s** {{one concrete capability}}.
- **{{Verb}}s** {{the second, with what it beats}}.
- **{{Verb}}s** {{the third}}.
- **No dependencies** beyond {{the standard library / the one you cannot avoid}}.

> [!NOTE]
> {{SCOPE. What it deliberately does not handle, and what to use instead for
> that case. Which versions are supported. Whether the API is stable.}}

## Install

```sh
{{package manager install command}}
```

<details>
<summary>Other package managers</summary>

```sh
{{alternative}}
{{from source}}
```
</details>

Supported: {{runtime versions}}. {{Anything about optional extras.}}

## Usage

{{The smallest complete program that does something worth doing.}}

```{{lang}}
{{code}}
```

{{One paragraph on what just happened, naming the thing a reader would get wrong
on their first attempt.}}

<details open>
<summary><b>{{The second common case}}</b></summary>

```{{lang}}
{{code}}
```

{{Why you would reach for this instead of the first one.}}
</details>

<details>
<summary><b>{{The advanced case}}</b></summary>

```{{lang}}
{{code}}
```
</details>

## API

| {{Function / type}} | Does | Returns |
|---|---|---|
| `{{name}}({{args}})` | {{one clause}} | `{{type}}` |
| `{{name}}({{args}})` | {{one clause}} | `{{type}}` |

Full reference: [docs/api.md](docs/api.md).

{{The behaviours that surprise people: what raises, what mutates, what is
thread-safe, what the defaults actually are.}}

## Configuring

| Option | Default | Effect |
|---|---|---|
| `{{option}}` | `{{default}}` | {{what changes, and when you would change it}} |

## How it works

{{Two or three paragraphs on the mechanism — enough that a reader can predict
the performance and the failure modes without reading the source.}}

The long version is in [ARCHITECTURE.md](ARCHITECTURE.md).

## Development

```sh
{{install dev deps}}
{{lint}}
{{type check}}
{{test}}
```

{{The coverage floor, the supported-version matrix, and what CI runs that a
laptop cannot.}}

## Layout

```text
{{project}}/
├── src/{{package}}/   the library
├── docs/              reference and design notes
└── tests/             {{suite description}}
```

## License

[MIT](LICENSE).
