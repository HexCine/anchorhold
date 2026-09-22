# Releasing anchorhold

Repository: [anchorhold](https://github.com/HexCine/anchorhold). Distribution is through GitHub Releases.
Publishing to PyPI/npm is separate and requires ownership of the registry name;
no registry publication or hosted service is implied by a GitHub release.

1. Review source, license, changelog, examples and documentation. Exclude local
   environments, caches, credentials, private inputs and personal paths.
2. Run the documented tests and build. Install the resulting package into a
   clean environment, outside the source dependency tree, and test the examples.
3. Push the reviewed commit and inspect every matrix job in GitHub Actions.
   Resolve failures before selecting a release tag.
4. Create a new version tag at the exact commit with successful CI. Include the
   installable package, source archive, SHA256SUMS.txt and verification.json.
   The verification record must name the commit and executed jobs.
5. Verify asset digests and a public download. Keep previous releases unchanged.

Current first GitHub release: v0.1.1. See CHANGELOG.md and README.md for
implemented scope. Do not claim unrun tests, user adoption or production safety.
