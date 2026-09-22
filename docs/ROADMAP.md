# Scope and first 30 days

User: a documentation maintainer about to publish a changed static HTML build.
Keep old externally linked targets pointing to the intended section.

## Why this stack

Python 3.11 + html5lib provides portable CLI installation and browser-style HTML5
parsing without implementing an HTML parser. html5lib uses MIT, six MIT and
webencodings BSD; the project uses MIT and depends on, rather than vendors, them.
Node + parse5 would also be reasonable for frontend repositories. Go/Rust would
offer a standalone executable but increase initial implementation effort. The
current release needs neither browser execution nor an online service.

## Five acceptance criteria

1. Snapshot a built UTF-8 site without executing code or fetching resources.
2. Find removed pages/targets and changed heading associations.
3. Reproduce numeric-heading retargeting using actual Sphinx output.
4. Preserve uncertainty and allow exact, reasoned review exceptions only.
5. Ship installable source/wheel, examples, meaningful tests and CI configuration.

No automatic redirects/rewrites, crawling, hosting emulation or semantic AI
matching in 0.1. An unchanged heading can conceal changed prose; the tool does
not claim to solve that.

## Days 1–7: review and publish the alpha

Choose a repository and verify package-name availability before publication.
Review the prepared distribution, run hosted CI, then publish clear limitations
and the before/shifted/fixed demo. Preserve the known-good baseline through
version control; never regenerate it as part of the candidate check.

Identify maintainers who have recently changed a changelog or documentation
generator. Seek three voluntary old/new build trials via channels that welcome
such requests. No messages or publication have been performed in this task.

## Days 8–14: determine whether the report saves work

Record confirmed accidental retargets, intentional changes and unsupported HTML
structures separately. Ask whether each maintainer would keep the check in CI.
Minimize shared reproductions and get permission before storing private docs.
If reports are mostly cosmetic noise, improve association/scope before adding
another feature. Do not count generated examples as external adoption.

## Days 15–21: address the biggest observed blocker

Choose one based on trial evidence: selection of public content containers,
verification of declared redirects, or a lychee integration proposal. Hosting
alias support must be explicit and tested against the actual host. Do not guess
semantic identity with an AI model just to eliminate review messages.

## Days 22–30: measure repeated use

Learning targets: three completed trials, one confirmed useful correction and
one maintainer who voluntarily runs the check again or adds it to CI. These are
internal targets, not official program requirements. Publish anonymized results
only with permission; retain public issue/release links as maintenance evidence.

If a standalone tool is inconvenient, discuss contributing the tested concept
to an existing checker. Stop expanding the product if there is no repeated use.
Do not create additional repositories merely to increase their count.

## Maintenance and application evidence

Budget a few hours per week initially for support, tests and release work; this
is a planning assumption, not a measured commitment from the user. Runtime is
local and no infrastructure was provisioned. Real community value and ongoing
maintainer work are stronger evidence than raw repository, star or download
counts. The previous program eligibility report still applies; this alpha alone
does not establish eligibility or guarantee approval.
