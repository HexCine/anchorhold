# Validation of the local 0.1.1 release

## Release evidence

The local record below was written before the first GitHub publication.
Hosted execution is recorded for the release commit in
[verification.json](https://github.com/HexCine/anchorhold/releases/download/v0.1.1/verification.json);
inspect its linked jobs rather than treating configured CI as an executed test.
The release process requires all six OS/Python jobs to succeed.

## Historical local validation

Date: 2026-09-21. Platform actually exercised: Windows.

| Check | Observed result |
|---|---|
| Fresh Python 3.11.15 environment, installed wheel | 43 tests passed; warnings treated as errors |
| Fresh Python 3.14.5 environment, installed wheel | 43 tests passed; warnings treated as errors |
| Imports and metadata | Loaded from the fresh environment; module and distribution versions are 0.1.1 |
| Console command | Installed entry point reports 0.1.1 |
| CLI contract | Clean=0, findings=1, invalid/unknown input=2 scenarios exercised |
| Dependencies | uv pip check passed in both clean environments |
| Build round trip | Direct wheel and wheel rebuilt from sdist agree under WheelTwin; RECORD inventories validated |
| Distribution metadata | twine check passed for wheel and sdist |
| CI configuration | actionlint 1.7.12 passed for the updated workflow |

The delivered wheel must have the same SHA-256 as the wheel used in these clean
environments; the release assembly script enforces that equality. Source archives
include the new regression tests, documentation and CI; caches and virtual
environments are excluded. The release bundle contains machine-readable
clean-install and build-comparison records and a SHA-256 manifest.

The CI matrix builds through sdist, checks metadata, installs the resulting wheel
in a fresh environment, and tests it on Python 3.11/3.14 across Windows, Linux and
macOS. Hosted CI and Linux/macOS jobs were **not run** during this local review.

Earlier evidence is retained separately in [the 0.1.0 validation record](VALIDATION-0.1.0.md).

This is an unpublished alpha with documented scope limits, not a claim of
complete correctness, external adoption, a security audit or program eligibility.
