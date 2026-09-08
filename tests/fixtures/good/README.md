<h1 align="center">portcheck</h1>

<p align="center">
  <em>Finds which process is holding a port, on Linux, macOS and Windows, with
  one command and the same output on all three.</em>
</p>

<p align="center">
  <a href="https://github.com/example/portcheck/actions/workflows/ci.yml"><img alt="CI status" src="https://img.shields.io/github/actions/workflow/status/example/portcheck/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/example/portcheck?style=flat-square"></a>
  <a href="https://github.com/example/portcheck/tags"><img alt="Latest tag" src="https://img.shields.io/github/v/tag/example/portcheck?style=flat-square&label=version"></a>
</p>

<p align="center">
  <a href="#install">Install</a> &middot;
  <a href="#quickstart">Quickstart</a> &middot;
  <a href="ARCHITECTURE.md">Architecture</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img alt="portcheck 8080 naming the process, then portcheck --all listing every listener" src="docs/demo.gif" width="760">
</p>

---

## What it is

Something is already on port 8080. Finding out what means remembering whether
this machine wants `lsof -i :8080`, `ss -lptn 'sport = :8080'`, or
`netstat -ano | findstr :8080` followed by looking the PID up in Task Manager —
and the three of them print three different things in three different shapes.

portcheck is one command that answers the question the same way everywhere. It
shells out to whichever of those tools the platform has, parses the output, and
prints one line per listener.

- **Names** the process, its PID and its user for any port, in one line.
- **Lists** every listener with `--all`, sorted by port.
- **Prints** JSON with `--json`, so a script does not have to parse a table.
- **Exits** non-zero when the port is free, so `portcheck 8080 || start-server`
  works without a wrapper.

> [!NOTE]
> portcheck reports; it never kills anything, because a tool that can both find
> and kill a process is one people run with `sudo` by habit. On Linux and macOS
> it needs no privileges for your own processes and shows `-` for the owner of
> anyone else's; run it with `sudo` to see those. On Windows it reads the same
> table `netstat` does and needs no elevation at all.

## Contents

- [Requirements](#requirements)
- [Install](#install)
- [Quickstart](#quickstart)
- [Configuring](#configuring)
- [What you get](#what-you-get)
- [How it works](#how-it-works)
- [Development](#development)
- [Layout](#layout)
- [License](#license)

## Requirements

| Platform | You need first | What portcheck uses |
|---|---|---|
| **Linux** | `ss` (iproute2) or `lsof` | `ss` when present; it is faster and needs no root for your own sockets |
| **macOS** | nothing — `lsof` ships with the OS | `lsof -i -P -n` |
| **Windows** | nothing — `netstat` ships with the OS | `netstat -ano`, plus the process table for names |

No runtime to install: portcheck is a single static binary.

## Install

Each command is idempotent — safe to re-run over an existing install.

<details open>
<summary><b>macOS and Linux</b></summary>

```sh
curl -fsSL https://example.com/portcheck/install.sh | sh
```

Installs to `~/.local/bin/portcheck`. Set `PREFIX=/usr/local` to put it
somewhere else.
</details>

<details>
<summary><b>Windows</b></summary>

```powershell
winget install Example.portcheck
```
</details>

Then verify:

```sh
portcheck --version
```

Prints the version and which backend it picked for this machine. If the backend
line says `none`, no supported tool was found and the requirements table above
says which one to install.

For unattended installs, `PORTCHECK_PREFIX` and `PORTCHECK_ASSUME_YES=1` answer
both prompts, so the script runs unattended in a Dockerfile or a CI job.

## Quickstart

```sh
portcheck 8080          # what is holding this port
portcheck --all         # every listener, sorted by port
portcheck --json 8080   # one JSON record, for scripts
portcheck --version     # version and the backend chosen for this machine
```

Output is one line per listener, aligned:

```text
8080  tcp  node       41213  marty   /usr/local/bin/node server.js
```

The last column is the full command line, which is the field that actually tells
you which of your four Node processes this is.

## Configuring

There is no config file. Three environment variables cover everything worth
changing:

| Variable | Default | Effect |
|---|---|---|
| `PORTCHECK_BACKEND` | autodetect | force `ss`, `lsof` or `netstat` |
| `PORTCHECK_TIMEOUT` | `5` | seconds to wait for the backend before giving up |
| `NO_COLOR` | unset | any value disables colour, per the `NO_COLOR` convention |

## What you get

<details open>
<summary><b>The same output everywhere</b></summary>

- **One line per listener**, with the port, protocol, process name, PID, user
  and full command line — the last field is the one that distinguishes four
  copies of the same runtime, which is why it is there rather than truncated.
- **Stable column order across platforms**, so a script that greps column four
  keeps working when it runs on a different machine — unlike parsing `lsof` and
  `netstat` directly, where the columns differ in both order and count.
</details>

<details>
<summary><b>Scriptable exits</b></summary>

- **Exit 0** when something is listening, **1** when the port is free, **2** when
  no backend is available. That third code matters: without it a missing `lsof`
  looks exactly like a free port, and a deploy script happily starts a second
  server on an occupied one.
</details>

## How it works

portcheck does not open sockets or read `/proc` directly. It runs the platform's
own tool and parses it, because those tools already handle the cases that make a
from-scratch implementation wrong: IPv4-mapped IPv6 addresses, sockets in
`TIME_WAIT`, and containers whose network namespace is not the host's.

The parsers are the whole program. Each backend has one, each normalises into the
same record, and each has a fixture of real captured output in `tests/fixtures/`
so a change to a distro's `ss` formatting shows up as a failing test rather than
as a wrong answer.

The long version is in [ARCHITECTURE.md](ARCHITECTURE.md).

## Development

```sh
make lint
make test
make fixtures
```

`make fixtures` re-captures backend output on the current machine and is the only
target that needs a real network stack; CI runs the other two on Ubuntu, macOS
and Windows against the committed fixtures.

## Layout

```text
portcheck/
├── src/         the CLI and the three backend parsers
├── docs/        architecture and the recording script
└── tests/       unit tests and captured backend fixtures
```

`tests/fixtures/` holds real output from each backend, captured on a machine that
had it. That directory is the reason the parsers can be tested on a runner that
does not have `ss`.

## License

[MIT](LICENSE).
