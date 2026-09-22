# Validation of the local 0.1.0 release

Date: 2026-09-21. Unpublished alpha; no external adoption is claimed.

| Check | Observed result |
|---|---|
| Windows, Python 3.11.15 | 40 unittest tests passed |
| Windows, Python 3.14.5 | 40 unittest tests passed |
| Fresh environment, wheel installation | 40 tests passed; import location verified in site-packages |
| Installed console command | Snapshot created; overwrite and missing input refused |
| Text / JSON / HTML | Shifted exits 1, fixed exits 0, unknown exits 2 in all formats |
| Exact review exceptions | Findings retained as accepted; stale exceptions exit 2 |
| Independent generator | Sphinx 9.1.0 / docutils 0.22.4 reproduces three shifted numeric targets |
| Comparison | lychee 0.24.2 accepts those three existing targets; AnchorHold flags three changed associations |
| Distribution | sdist and wheel built; metadata checked with twine |

Tests exercise HTML5 optional closing tags, inline/hidden text, template/script
exclusion, Sphinx containers, nested sections, aliases, duplicate IDs, Unicode
URL encoding, whitespace handling, removals, semantic-review boundaries,
input limits, malformed JSON, exclusive snapshot creation, exceptions and HTML
escaping. The filesystem-link rejection branch is tested by simulating link
detection; no live symlink/junction fixture was created on this Windows host.

The optional examples/reproduce_sphinx.py was run successfully against Sphinx
9.1.0. Only original minimal RST/conf.py created by that script was executed.
AnchorHold's CLI itself never executes a site or documentation build. Demo JSON
and the lychee release digest are in examples/reports.

The clean environment uses html5lib 1.1, six 1.17.0 and webencodings 0.6.1.
The source installation was tested on both Python versions; the fresh wheel
environment uses Python 3.14.5. This is local Windows evidence only.

Not run: hosted GitHub CI, Linux/macOS jobs, deployment-level redirects, browser
scroll position, arbitrary theme/SPA compatibility or a representative external
workflow corpus. Those remain distinct from the supported static model.

The clean release excludes caches, virtual environments, downloaded upstream
binaries, generated Sphinx theme assets and research scratch. Distribution text
was checked for private absolute paths and common credential patterns. This
review is not a guarantee against every possible kind of sensitive content.
