"""Tests for readme-lint.

Two kinds. Unit tests pin one rule each. The calibration tests pin the rubric
itself against two fixtures - a README known to be good and one known to be bad -
because a rubric with no calibration drifts into whatever the last commit felt
like, and every individual rule can still pass while the score means nothing.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import readme_badges  # noqa: E402
import readme_lint as rl  # noqa: E402
import readme_toc  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def lint(text: str, tmp_path: Path, profile: str = "cli", **cfg_kwargs):
    path = tmp_path / "README.md"
    path.write_text(text, encoding="utf-8")
    cfg = rl.Config(profile=profile, root=tmp_path, **cfg_kwargs)
    doc = rl.parse(path, tmp_path)
    return rl.run(doc, cfg)


def rule_ids(report) -> set:
    return {f.rule for f in report.findings}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_github_slug_matches_github_rules():
    assert rl.github_slug("What it is") == "what-it-is"
    assert rl.github_slug("Architecture in 30 seconds") == "architecture-in-30-seconds"
    assert rl.github_slug("`code` and **bold**") == "code-and-bold"
    # Punctuation is dropped, not collapsed: "C++ / Rust?" -> "c  rust" -> "c--rust".
    assert rl.github_slug("C++ / Rust?") == "c--rust"
    assert rl.github_slug("[a link](x.md)") == "a-link"


def test_fences_are_excluded_from_prose(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("# t\n\n```sh\nblazingly fast\n```\n", encoding="utf-8")
    doc = rl.parse(path, tmp_path)
    assert "blazingly fast" not in doc.prose
    assert doc.in_fence(4)
    assert not doc.in_fence(1)


def test_setext_headings_are_found(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("Title\n=====\n\nSection\n-------\n", encoding="utf-8")
    doc = rl.parse(path, tmp_path)
    assert [(h.level, h.text) for h in doc.headings] == [(1, "Title"), (2, "Section")]


def test_html_headings_and_images_are_found(tmp_path):
    path = tmp_path / "README.md"
    path.write_text('<h1 align="center">x</h1>\n<img alt="a cat" src="c.png">\n',
                    encoding="utf-8")
    doc = rl.parse(path, tmp_path)
    assert doc.h1s and doc.h1s[0].text == "x"
    assert doc.images[0].alt == "a cat"


def test_reference_style_links_resolve(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("# t\n\nSee [the docs][d].\n\n[d]: docs/x.md\n", encoding="utf-8")
    doc = rl.parse(path, tmp_path)
    assert any(link.target == "docs/x.md" for link in doc.links)


def test_section_vocabulary_maps_variants():
    assert rl.section_key_of("Getting Started") == "install"
    assert rl.section_key_of("Architecture in 30 seconds") == "architecture"
    assert rl.section_key_of("## Quick Start") == "quickstart"
    assert rl.section_key_of("Zebra husbandry") is None


# ---------------------------------------------------------------------------
# Individual rules
# ---------------------------------------------------------------------------


def test_hero001_flags_a_second_h1(tmp_path):
    report = lint("# one\n\n# two\n", tmp_path)
    assert "HERO001" in rule_ids(report)


def test_hero002_accepts_a_real_tagline(tmp_path):
    good = "# tool\n\nA linter that scores a README against a written rubric, for any project.\n"
    assert "HERO002" not in rule_ids(lint(good, tmp_path))
    assert "HERO002" in rule_ids(lint("# tool\n\n## Install\n", tmp_path))


def test_hero003_flags_mixed_badge_styles(tmp_path):
    text = ("# t\n\nA tagline long enough to count as a real one for the linter.\n\n"
            "![a](https://img.shields.io/x?style=flat)\n"
            "![b](https://img.shields.io/y?style=for-the-badge)\n")
    findings = [f for f in lint(text, tmp_path).findings if f.rule == "HERO003"]
    assert any("Mixed badge styles" in f.message for f in findings)


def test_hero005_accepts_a_mermaid_fence(tmp_path):
    text = ("# t\n\nA tagline long enough to count as a real one for the linter.\n\n"
            "```mermaid\nflowchart LR\n  a --> b\n```\n\n## Install\n")
    assert "HERO005" not in rule_ids(lint(text, tmp_path))


def test_mec001_flags_a_dead_relative_link(tmp_path):
    report = lint("# t\n\nSee [docs](docs/missing.md).\n", tmp_path)
    assert any(f.rule == "MEC001" and "docs/missing.md" in f.message
               for f in report.findings)


def test_mec001_accepts_a_link_that_resolves(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "there.md").write_text("x", encoding="utf-8")
    report = lint("# t\n\nSee [docs](docs/there.md).\n", tmp_path)
    assert "MEC001" not in rule_ids(report)


def test_mec001_ignores_external_links(tmp_path):
    report = lint("# t\n\n[x](https://example.com/a) [y](mailto:a@b.c)\n", tmp_path)
    assert "MEC001" not in rule_ids(report)


def test_mec002_flags_an_anchor_with_no_heading(tmp_path):
    report = lint("# t\n\n## Install\n\n[go](#nowhere) [ok](#install)\n", tmp_path)
    msgs = [f.message for f in report.findings if f.rule == "MEC002"]
    assert any("nowhere" in m for m in msgs)
    assert not any("install" in m for m in msgs)


def test_mec002_handles_duplicate_heading_slugs(tmp_path):
    text = "# t\n\n## Notes\n\n## Notes\n\n[a](#notes) [b](#notes-1)\n"
    assert "MEC002" not in rule_ids(lint(text, tmp_path))


def test_mec003_flags_a_missing_alt(tmp_path):
    report = lint("# t\n\n![](a.png)\n", tmp_path)
    assert "MEC003" in rule_ids(report)


def test_hyg001_flags_placeholders(tmp_path):
    report = lint("# t\n\nTODO: write this.\n", tmp_path)
    assert any(f.rule == "HYG001" and f.level == rl.ERROR for f in report.findings)


def test_hyg002_flags_vanity_badges(tmp_path):
    text = ("# t\n\nA tagline long enough to count as a real one for the linter.\n\n"
            "![love](https://img.shields.io/badge/made%20with-love-red?style=flat)\n")
    assert "HYG002" in rule_ids(lint(text, tmp_path))


def test_hyg002_respects_allow_badges(tmp_path):
    text = ("# t\n\nA tagline long enough to count as a real one for the linter.\n\n"
            "![love](https://img.shields.io/badge/made%20with-love-red?style=flat)\n")
    report = lint(text, tmp_path, allow_badges=["made%20with-love"])
    assert "HYG002" not in rule_ids(report)


def test_hyg003_flags_superlatives_in_prose_only(tmp_path):
    assert "HYG003" in rule_ids(lint("# t\n\nIt is blazingly fast.\n", tmp_path))
    fenced = "# t\n\n```text\nblazingly fast\n```\n"
    assert "HYG003" not in rule_ids(lint(fenced, tmp_path))


def test_hyg007_flags_absolute_self_links(tmp_path):
    text = "# t\n\n[arch](https://github.com/o/r/blob/main/ARCHITECTURE.md)\n"
    report = lint(text, tmp_path)
    assert any(f.rule == "HYG007" and "ARCHITECTURE.md" in f.fix for f in report.findings)


def test_sec001_follows_the_profile(tmp_path):
    text = "# t\n\n## What it is\n\n## Install\n\n## License\n"
    cli = {f.message for f in lint(text, tmp_path, "cli").findings if f.rule == "SEC001"}
    minimal = rule_ids(lint(text, tmp_path, "minimal"))
    assert any("quickstart" in m for m in cli)
    assert "SEC001" not in minimal


def test_disabled_rules_stay_in_the_denominator(tmp_path):
    text = "# t\n\nTODO\n"
    with_rule = lint(text, tmp_path)
    without = lint(text, tmp_path, disable=["HYG001"])
    assert "HYG001" not in rule_ids(without)
    # Switching a failing rule off must not raise the score by its full weight.
    assert without.score - with_rule.score <= 4


def test_a_crashing_rule_does_not_fail_the_run(tmp_path, monkeypatch):
    def boom(doc, cfg):
        raise RuntimeError("nope")

    victim = next(r for r in rl.RULES if r.id == "HYG004")
    monkeypatch.setattr(victim, "check", boom)
    report = lint("# t\n\nsome text\n", tmp_path)
    assert any(f.rule == "HYG004" and "crashed" in f.message for f in report.findings)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_loads_from_the_repo_root(tmp_path):
    (tmp_path / ".awesome-readme.json").write_text(
        json.dumps({"profile": "library", "strict": True, "disable": ["HERO005"]}),
        encoding="utf-8")
    cfg = rl.Config.load(tmp_path)
    assert cfg.profile == "library"
    assert cfg.strict is True
    assert "HERO005" in cfg.disable


def test_config_survives_malformed_json(tmp_path):
    (tmp_path / ".awesome-readme.json").write_text("{not json", encoding="utf-8")
    assert rl.Config.load(tmp_path).profile == "cli"


def test_require_adds_to_the_profile_set(tmp_path):
    cfg = rl.Config(profile="minimal", require=["faq"], root=tmp_path)
    assert "faq" in cfg.required_sections
    assert "install" in cfg.required_sections


# ---------------------------------------------------------------------------
# TOC
# ---------------------------------------------------------------------------


def test_toc_collects_h2s_and_skips_itself(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("# t\n\n## Contents\n\n## Install\n\n## License\n", encoding="utf-8")
    doc = rl.parse(path, tmp_path)
    entries = readme_toc.collect(doc, 2, 2)
    assert [e[1] for e in entries] == ["Install", "License"]


def test_toc_splice_is_idempotent(tmp_path):
    raw = "# t\n\n## Contents\n\n<!-- toc -->\n\nold\n\n<!-- /toc -->\n\n## Install\n"
    once, changed = readme_toc.splice(raw, "- [Install](#install)")
    assert changed
    twice, changed_again = readme_toc.splice(once, "- [Install](#install)")
    assert not changed_again
    assert once == twice


def test_toc_creates_the_section_when_markers_are_absent(tmp_path):
    raw = "# t\n\n## Install\n\n## License\n"
    out, changed = readme_toc.splice(raw, "- [Install](#install)")
    assert changed
    assert "## Contents" in out
    assert readme_toc.BEGIN in out


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------


def test_badges_emit_nothing_a_repo_cannot_back(tmp_path):
    info = readme_badges.detect(tmp_path)
    keys = readme_badges.choose(info, 4)
    assert "ci" not in keys          # no .github/workflows
    assert "license" not in keys     # no LICENSE
    assert "npm" not in keys


def test_badges_detect_a_workflow_and_a_licence(tmp_path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("on: push", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
    info = readme_badges.detect(tmp_path)
    assert info["workflow"] == "ci.yml"
    keys = readme_badges.choose(info, 4)
    assert "ci" in keys and "license" in keys


def test_badges_render_linked_html(tmp_path):
    info = readme_badges.detect(tmp_path)
    out = readme_badges.build(["version"], info, "flat-square", "html")
    assert out.startswith('<p align="center">')
    assert "<a href=" in out and "alt=" in out


# ---------------------------------------------------------------------------
# Calibration - the tests that keep the rubric meaningful
# ---------------------------------------------------------------------------


def test_the_good_fixture_scores_well(tmp_path):
    src = (FIXTURES / "good" / "README.md").read_text(encoding="utf-8")
    report = lint(src, tmp_path)
    assert report.score >= 85, "\n".join(
        "%s %s" % (f.rule, f.message) for f in report.findings)


def test_the_bad_fixture_scores_badly(tmp_path):
    src = (FIXTURES / "bad" / "README.md").read_text(encoding="utf-8")
    report = lint(src, tmp_path)
    assert report.score < 45
    assert any(f.level == rl.ERROR for f in report.findings)


def test_this_repos_own_readme_passes_its_own_rubric():
    doc = rl.parse(ROOT / "README.md", ROOT)
    report = rl.run(doc, rl.Config.load(ROOT))
    errors = [f for f in report.findings if f.level == rl.ERROR]
    assert not errors, "\n".join("%s:%d %s" % (f.rule, f.line, f.message) for f in errors)
    assert report.score >= 90


def test_the_generated_rubric_doc_is_current():
    generated = rl.render_rules()
    on_disk = (ROOT / "docs" / "rubric.md").read_text(encoding="utf-8")
    assert generated.strip() in on_disk, (
        "docs/rubric.md has drifted; regenerate with "
        "`python3 scripts/readme_lint.py --rules`")


def test_every_rule_has_a_reason_and_a_sane_weight():
    for r in rl.RULES:
        assert r.category in rl.CATEGORIES, r.id
        assert 1 <= r.weight <= 10, r.id
        assert len(r.why.split()) >= 12, "%s: the reason is too thin to defend" % r.id
        assert r.title and not r.title.endswith("."), r.id


def test_rule_ids_are_unique():
    ids = [r.id for r in rl.RULES]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def run_cli(*args, cwd=None):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "readme_lint.py"), *args],
                          capture_output=True, text=True, cwd=cwd)


def test_cli_json_is_parseable(tmp_path):
    (tmp_path / "README.md").write_text("# t\n\nA tagline that is long enough here.\n",
                                        encoding="utf-8")
    out = run_cli("README.md", "--json", cwd=tmp_path)
    data = json.loads(out.stdout)
    assert set(data) >= {"score", "grade", "findings", "categories", "profile"}
    assert out.returncode == 0


def test_cli_strict_exits_nonzero_on_errors(tmp_path):
    (tmp_path / "README.md").write_text("# t\n\nTODO\n", encoding="utf-8")
    assert run_cli("README.md", "--strict", cwd=tmp_path).returncode == 1


def test_cli_advisory_exits_zero_on_errors(tmp_path):
    (tmp_path / "README.md").write_text("# t\n\nTODO\n", encoding="utf-8")
    assert run_cli("README.md", cwd=tmp_path).returncode == 0


def test_cli_min_score_gate(tmp_path):
    (tmp_path / "README.md").write_text("# t\n\nTODO\n", encoding="utf-8")
    assert run_cli("README.md", "--min-score", "90", cwd=tmp_path).returncode == 1


def test_cli_missing_file_exits_two(tmp_path):
    assert run_cli("nope.md", cwd=tmp_path).returncode == 2


def test_cli_explain_prints_the_reason():
    out = run_cli("--explain", "DEP002")
    assert out.returncode == 0
    assert "DEP002" in out.stdout and len(out.stdout.split()) > 20


def test_cli_explain_unknown_rule_exits_two():
    assert run_cli("--explain", "ZZZ999").returncode == 2


# ---------------------------------------------------------------------------
# Hook
# ---------------------------------------------------------------------------


def run_hook(payload: dict):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "readme_hook.py")],
        input=json.dumps(payload), capture_output=True, text=True)


def test_hook_is_silent_on_an_unrelated_file(tmp_path):
    out = run_hook({"hook_event_name": "PostToolUse", "tool_name": "Edit",
                    "tool_input": {"file_path": str(tmp_path / "main.py")}})
    assert out.returncode == 0 and out.stdout.strip() == ""


def test_hook_reports_on_a_bad_readme(tmp_path):
    p = tmp_path / "README.md"
    p.write_text("# t\n\nTODO\n", encoding="utf-8")
    out = run_hook({"hook_event_name": "PostToolUse", "tool_name": "Edit",
                    "tool_input": {"file_path": str(p)}})
    payload = json.loads(out.stdout)["hookSpecificOutput"]
    assert payload["hookEventName"] == "PostToolUse"
    assert "readme-lint" in payload["additionalContext"]


def test_hook_ignores_non_commit_bash(tmp_path):
    out = run_hook({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                    "cwd": str(tmp_path), "tool_input": {"command": "git log --oneline"}})
    assert out.stdout.strip() == ""


def test_hook_denies_a_commit_only_in_strict_mode(tmp_path):
    (tmp_path / "README.md").write_text("# t\n\nTODO\n", encoding="utf-8")
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
               "cwd": str(tmp_path), "tool_input": {"command": "git commit -m x"}}

    advisory = json.loads(run_hook(payload).stdout)["hookSpecificOutput"]
    assert "permissionDecision" not in advisory
    assert "additionalContext" in advisory

    (tmp_path / ".awesome-readme.json").write_text('{"strict": true}', encoding="utf-8")
    strict = json.loads(run_hook(payload).stdout)["hookSpecificOutput"]
    assert strict["permissionDecision"] == "deny"
    assert "strict mode" in strict["permissionDecisionReason"]


def test_hook_can_be_disabled_by_environment(tmp_path, monkeypatch):
    p = tmp_path / "README.md"
    p.write_text("# t\n\nTODO\n", encoding="utf-8")
    env = dict(**__import__("os").environ, AWESOME_README_HOOKS="0")
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "readme_hook.py")],
                         input=json.dumps({"hook_event_name": "PostToolUse",
                                           "tool_name": "Edit",
                                           "tool_input": {"file_path": str(p)}}),
                         capture_output=True, text=True, env=env)
    assert out.stdout.strip() == ""


def test_hook_survives_garbage_input():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "readme_hook.py")],
                         input="not json at all", capture_output=True, text=True)
    assert out.returncode == 0


# ---------------------------------------------------------------------------
# Manifests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "hooks/hooks.json",
    "schema/awesome-readme.schema.json",
])
def test_manifests_are_valid_json(path):
    json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_every_declared_skill_exists():
    import install  # noqa: E402
    for name in install.SKILLS:
        assert (ROOT / "skills" / name / "SKILL.md").is_file(), name


def test_every_skill_has_frontmatter():
    for skill in (ROOT / "skills").iterdir():
        md = skill / "SKILL.md"
        text = md.read_text(encoding="utf-8")
        assert text.startswith("---\n"), md
        head = text.split("---", 2)[1]
        assert "name:" in head and "description:" in head, md


def test_every_template_names_its_profile():
    templates = {p.stem.split(".", 1)[1] for p in (ROOT / "templates").glob("README.*.md")}
    assert templates == set(rl.PROFILES)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------


def test_report_survives_a_non_ascii_readme(tmp_path):
    """A cp1252 console must not kill the run that was about to flag the emoji.

    The report quotes heading text back at the reader, so an emoji heading - the
    exact thing HYG005 exists to catch - crashed the whole report on a default
    Windows console before the streams were reconfigured to UTF-8.
    """
    (tmp_path / "README.md").write_text(
        "# t\n\nA tagline that is long enough to count for the linter here.\n\n"
        "## \u2728 Features \u2014 caf\u00e9\n\nSome prose.\n", encoding="utf-8")
    env = dict(**__import__("os").environ, PYTHONIOENCODING="cp1252")
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "readme_lint.py"), "README.md",
         "--no-colour"],
        capture_output=True, text=True, cwd=tmp_path, env=env,
        encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    assert "grade" in out.stdout


def test_toc_survives_a_non_ascii_heading(tmp_path):
    (tmp_path / "README.md").write_text(
        "# t\n\n## Caf\u00e9 \u2728\n\n## Install\n", encoding="utf-8")
    env = dict(**__import__("os").environ, PYTHONIOENCODING="cp1252")
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "readme_toc.py"), "README.md"],
        capture_output=True, text=True, cwd=tmp_path, env=env,
        encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    assert "#install" in out.stdout


def test_user_install_leaves_a_toolkit_beside_every_skill(tmp_path, monkeypatch):
    """A ~/.claude skill has no ${CLAUDE_PLUGIN_ROOT}, so scripts/ must be local.

    Both install shapes have to end the same way: if the skill's own
    instructions say `the scripts/ directory beside this SKILL.md`, that
    directory has to be there, copied or linked.
    """
    import install  # noqa: E402

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert install.do_user(dry=False, link=False) == 0
    for name in install.SKILLS:
        skill = tmp_path / "skills" / name
        assert (skill / "SKILL.md").is_file(), name
        assert (skill / "scripts" / "readme_lint.py").is_file(), name


def test_user_install_is_idempotent_and_reversible(tmp_path, monkeypatch):
    import install  # noqa: E402

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    settings = tmp_path / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps({"hooks": {"PostToolUse": [
        {"matcher": "Write", "hooks": [{"type": "command", "command": "theirs"}]}]}}),
        encoding="utf-8")

    install.do_user(dry=False, link=False)
    install.do_user(dry=False, link=False)          # twice: must not duplicate
    data = json.loads(settings.read_text(encoding="utf-8"))
    ours = [e for e in data["hooks"]["PostToolUse"]
            if e.get("_source") == install.MARKER]
    assert len(ours) == 1
    assert any(e.get("_source") != install.MARKER for e in data["hooks"]["PostToolUse"]), \
        "an unrelated hook must survive the merge"

    install.do_uninstall(user=True, project=None, dry=False)
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert not any(e.get("_source") == install.MARKER
                   for e in data.get("hooks", {}).get("PostToolUse", []))
    assert data["hooks"]["PostToolUse"], "the unrelated hook must still be there"
    assert not (tmp_path / "skills" / "readme-audit").exists()


def test_project_install_writes_a_valid_config(tmp_path):
    import install  # noqa: E402

    assert install.do_project(tmp_path, "service", strict=True, min_score=75,
                              ci=True, git_hook=True, dry=False) == 0
    cfg = json.loads((tmp_path / ".awesome-readme.json").read_text(encoding="utf-8"))
    assert cfg["profile"] == "service" and cfg["strict"] is True
    assert (tmp_path / ".githooks" / "pre-commit").is_file()
    assert (tmp_path / ".github" / "workflows" / "readme.yml").is_file()
    # The config it writes must satisfy the schema it points at.
    schema = json.loads((ROOT / "schema" / "awesome-readme.schema.json")
                        .read_text(encoding="utf-8"))
    allowed = set(schema["properties"])
    assert set(cfg) <= allowed, set(cfg) - allowed


# ---------------------------------------------------------------------------
# Hostile input
# ---------------------------------------------------------------------------


# Bodies are built lazily and identified by name: a parametrize carrying a
# 2 MB string inline puts that string in every test id pytest prints.
HOSTILE = {
    "unclosed-brackets": lambda: "[" * 50000,
    "atx-heading-of-hashes": lambda: "# " + "#" * 50000,
    "unterminated-html-anchor": lambda: '<a href="x">' + "a" * 200000,
    "unterminated-fence": lambda: "```\n" + ("x" * 200 + "\n") * 5000,
    "one-very-long-line": lambda: "z" * 2_000_000,
    "repeated-dead-link": lambda: "# t\n\n" + "[a](nope.md) " * 20000,
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_pathological_input_stays_fast(tmp_path, name):
    r"""CI lints READMEs written by strangers, so input cost has to be bounded.

    Unbounded `[^\]]*` rescanned to the end of the input from every `[`: 50k
    unclosed brackets cost 8.7s before the character classes were bounded, and a
    README naming the same missing file 20k times cost 20k stat calls.
    """
    p = tmp_path / "README.md"
    p.write_text(HOSTILE[name](), encoding="utf-8")
    start = time.perf_counter()
    rl.run(rl.parse(p, tmp_path), rl.Config(root=tmp_path))
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, "%s took %.2fs" % (name, elapsed)


def test_link_dedupe_makes_one_stat_per_target(tmp_path, monkeypatch):
    calls = []
    real_exists = Path.exists

    def counting_exists(self, *a, **kw):
        calls.append(str(self))
        return real_exists(self, *a, **kw)

    monkeypatch.setattr(Path, "exists", counting_exists)
    text = "# t\n\n" + "[a](same.md) " * 500 + "[b](other.md)\n"
    report = lint(text, tmp_path)
    probed = [c for c in calls if c.endswith(("same.md", "other.md"))]
    assert len(probed) == 2, probed
    assert len([f for f in report.findings if f.rule == "MEC001"]) == 2


def test_links_outside_the_repo_are_reported_not_probed(tmp_path, monkeypatch):
    """A README from a stranger must not make CI stat arbitrary paths.

    GitHub serves relative links from the repository, so a link that walks out
    is broken for every reader anyway - reporting it is the correct behaviour
    and the safe one at the same time.
    """
    probed = []
    real_exists = Path.exists

    def counting_exists(self, *a, **kw):
        probed.append(str(self))
        return real_exists(self, *a, **kw)

    monkeypatch.setattr(Path, "exists", counting_exists)
    report = lint("# t\n\n[a](../../../etc/passwd) [b](../outside.md)\n", tmp_path)
    findings = [f for f in report.findings if f.rule == "MEC001"]
    assert len(findings) == 2
    assert all("outside the repository" in f.message for f in findings)
    assert not [p for p in probed if "etc" in p or "outside.md" in p], probed


def test_links_inside_the_repo_still_resolve(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    report = lint("# t\n\n[a](docs/a.md) [b](./docs/a.md) [c](/docs/a.md)\n", tmp_path)
    assert "MEC001" not in rule_ids(report)
