<h1 align="center">{{PROJECT}}</h1>

<p align="center">
  <em>{{TAGLINE — what this collection covers, who maintains it, and what makes
  it worth reading over the official documentation.}}</em>
</p>

<p align="center">
  <a href="https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml"><img alt="Link check" src="https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?branch=main&style=flat-square&label=links"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/{{OWNER}}/{{REPO}}?style=flat-square"></a>
  <a href="https://github.com/{{OWNER}}/{{REPO}}/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/{{OWNER}}/{{REPO}}?style=flat-square"></a>
</p>

<p align="center">
  <a href="#contents">Contents</a> &middot;
  <a href="#how-to-use-this">How to use this</a> &middot;
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## What it is

{{WHAT QUESTION this collection answers, and for whom. The gap in the existing
material that made it worth writing.}}

{{HOW IT IS ORGANISED, and what that organisation assumes about the reader.}}

> [!NOTE]
> {{What is deliberately out of scope, and where to go for it. How current the
> material is, and against which version of the thing it documents.}}

## Contents

<!-- toc -->

- [Getting started](#getting-started)
- [How to use this](#how-to-use-this)
- [Contributing](#contributing)
- [Layout](#layout)
- [License](#license)

<!-- /toc -->

## Getting started

{{The first three documents to read, in order, with one line each on what the
reader will be able to do afterwards.}}

1. **[{{Doc}}]({{path}})** — {{what it gets you}}
2. **[{{Doc}}]({{path}})** — {{what it gets you}}
3. **[{{Doc}}]({{path}})** — {{what it gets you}}

To read it offline, or preview a change before you open a pull request:

```sh
git clone https://github.com/{{OWNER}}/{{PROJECT}}
{{the one command that serves the docs locally}}
```

## How to use this

| If you want to | Read |
|---|---|
| {{task}} | [{{doc}}]({{path}}) |
| {{task}} | [{{doc}}]({{path}}) |
| {{task}} | [{{doc}}]({{path}}) |

{{How to search it — the tool, the convention, the tags.}}

## Contributing

```sh
{{lint command}}
{{link check command}}
{{build or preview command}}
```

{{The conventions a new page must follow: front matter, file naming, where it
goes in the index, how it gets reviewed.}} The full guide is in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Layout

```text
{{project}}/
├── guides/     task-shaped, start here
├── reference/  lookup material
├── decisions/  why things are the way they are
└── assets/     images and diagrams
```

## License

{{The content licence, which for a documentation repository is usually not the
code licence.}} [CC BY 4.0](LICENSE).
