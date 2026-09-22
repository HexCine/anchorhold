# AnchorHold

[![CI](https://github.com/HexCine/anchorhold/actions/workflows/ci.yml/badge.svg)](https://github.com/HexCine/anchorhold/actions/workflows/ci.yml)

**A link can still resolve and point to the wrong release.** AnchorHold compares
the static targets of two documentation builds and flags old URLs whose heading
changed, disappeared, or now lives at a different target.

For example, a generated changelog uses `#id1` for version 1.2.0. After prepending
1.3.0, `#id1` still exists, but 1.2.0 moved to `#id2`. An existence-only link check
does not establish that the old link still means the same thing.

Python 3.11+, html5lib, MIT. This is an early 0.1.1 alpha. It works locally
on generated HTML: no account, network requests, site execution or paid API.

## Download a release

[Release v0.1.1](https://github.com/HexCine/anchorhold/releases/tag/v0.1.1) includes a wheel, source
archives, checksums and a verification record. With Python 3.11+, install the
downloaded wheel using `python -m pip install anchorhold-0.1.1-py3-none-any.whl`.
Runtime dependencies listed below are resolved by pip when needed.
For source development, clone this repository and follow the existing install steps.

## Quick start

From this source folder, in a virtual environment:

```sh
python -m pip install .
anchorhold snapshot examples/before --output baseline.json
anchorhold check baseline.json examples/shifted
anchorhold check baseline.json examples/fixed --format json
anchorhold check baseline.json examples/shifted --format html > report.html
```

The shifted example exits 1: all three old numeric anchors now label different
releases. The fixed example exits 0 because the historical targets still label
their original releases. The HTML report is a standalone file with escaped text
and no scripts. Redirect only into a new report path, never onto an input.

For a real project, build the currently published revision and the proposed
revision into separate directories using the project's normal build command.
Snapshot the published build once, then check the candidate build. AnchorHold
does not invoke a documentation builder or run conf.py itself.

## What it checks

| Code | Evidence |
|---|---|
| `page_removed` | An old HTML file no longer exists at its relative path |
| `anchor_removed` | An old target no longer appears in that file |
| `heading_retargeted` | The URL has a different heading; old heading text exists at other current targets |
| `heading_changed` | Heading text changed, without a same-text candidate elsewhere |
| `heading_unresolved` | The target exists but its previous heading association is no longer recognized |

All findings require review. Even `heading_retargeted` is textual evidence, not
a proof of semantic equivalence or a confirmed bug. Repeated headings such as
"Overview" can produce several candidates; none is chosen automatically.

The snapshot records all static `id` targets and legacy `<a name>` targets, but
the default comparison protects **anchored headings and HTML page paths**.
Use `snapshot --all-anchors` to also protect targets without a heading label.

Heading associations cover h1–h6 IDs, IDs/named anchors inside a heading, and
IDs on section/div containers with a first descendant heading (Sphinx-style
output). Text includes inline markup, collapses whitespace, and excludes
script/style content and common hidden/permalink decorations. It does not
normalize case, punctuation or Unicode characters. An isolated anchor before
a heading is not automatically assigned to that heading.

Snapshots use schema_version 1, relative paths, content hashes and labels.
Hashes record source provenance; snapshots are not cryptographically signed.
HTML input must be UTF-8. html5lib applies HTML5 parsing rules, including common
omitted end tags. This is not an HTML validity or accessibility checker.

## Review intentional changes

JSON reports contain a fingerprint for the exact code, URL, before and after
values. To acknowledge an intentional change, copy that fingerprint into a
review file with a reason:

```json
{
  "schema_version": 1,
  "accept": [
    {"fingerprint": "COPY_THE_64_HEX_CHARACTERS_FROM_THE_REPORT", "reason": "Reviewed wording change; same section."}
  ]
}
```

```sh
anchorhold check baseline.json new-site --accept reviewed.json --format json
```

Accepted findings remain visible in `accepted`. Changed evidence no longer
matches. Unused/stale entries make the result incomplete, so remove them only
after reviewing the current report. There are no wildcard suppressions or auto
fixes. Snapshot creation refuses to overwrite any existing path. Replace a
baseline through a separate, reviewed version-control change, never merely to
make CI green.

## Exit codes

| Exit | Meaning |
|---|---|
| 0 | No unreviewed changes within the supported static model |
| 1 | Changes require review |
| 2 | Invalid input or incomplete analysis |

Duplicate static targets and meta-refresh redirects make candidate analysis
incomplete; known findings remain in the report. A baseline containing either
is rejected. A headings-only baseline with no anchored headings is rejected.
Errors are JSON on stderr; successful reports are stdout. `complete` only
describes this static model, not every behavior of the deployed website.

## Boundaries

This release compares exact build-relative HTML paths. It does **not** model
hosting rewrites, directory-index aliases, extensionless paths, HTTP redirects,
JavaScript routing, shadow DOM, deployment base paths or cross-domain moves.
Those need a separate deployed-site/browser check. Meta refresh is reported;
arbitrary JavaScript redirects cannot be inferred. No requests are made.

It cannot detect changed prose beneath an unchanged heading, prove a proposed
replacement has the same meaning, or know which targets outsiders actually use.
Default heading scope omits non-heading targets such as many API signatures;
all-anchor scope checks their existence but not their meaning. CSS visibility
and text created by JavaScript are not evaluated. Avoid using SPA shells as a
substitute for rendered documentation.

The source tree must be stable during scanning. Nested symlinks/junctions are
rejected. Bounds: 10,000 HTML files, 100,000 filesystem entries, 2 MiB/HTML file,
100 MiB HTML total, 200,000 DOM nodes/file, depth 150, 32 MiB JSON input. These
are defensive limits, not an OS resource sandbox. Reports/snapshots include
document headings and paths; review private-site reports before sharing.

## Research and development

[Sphinx #8709](https://github.com/sphinx-doc/sphinx/issues/8709) documents numeric
anchor drift; explicit stable targets and ID-prefix workarounds already exist.
[pip #8152](https://github.com/pypa/pip/issues/8152) is closed and must not be
presented as an unfixed pip bug. The value here is a release regression check,
not a new slug generator. See the [research ledger](docs/RESEARCH.ru.md) for
competitors, rejected ideas and limits of the novelty claim.

```sh
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

CI is configured for Windows/Linux/macOS and Python 3.11/3.14. See
[validation](docs/VALIDATION.md), [30-day plan](docs/ROADMAP.md),
[CONTRIBUTING](CONTRIBUTING.md), [SECURITY](SECURITY.md) and
[release instructions](docs/RELEASING.md). No external users or program approval
are claimed. Publication is a separate step.

### Upgrading from 0.1.0

Heading labels now ignore HTML comments and treat `<br>` as a word boundary. If your baseline contains affected headings, rebuild the baseline with 0.1.1 from the **same known-good historical HTML** before comparing the new site. Do not regenerate it from an unreviewed candidate site: doing so would acknowledge its changes. Unaffected snapshots remain compatible.
